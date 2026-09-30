"""
==========================================================
Notification Service
==========================================================

Business logic for BloodLink notification campaigns.

Responsibilities
----------------
- Create notification campaigns
- Create notification recipients
- Update campaign statistics
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from backend.database import crud
from backend.database.models import BloodRequest, Donor
from backend.database.notification import Notification

from backend.services import donor_eligibility_service, email_service


@dataclass(frozen=True)
class StageDeliveryResult:
    stage_number: int
    attempted: int
    sent: int
    failed: int
    queued_remaining: int
    target_met: bool
    next_stage_at: datetime | None


def _as_utc(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _send_to_recipient(
    database_session: Session,
    blood_request: BloodRequest,
    recipient,
) -> bool:
    """Send a new, one-time response link to an existing campaign recipient."""
    donor = recipient.donor
    if (
        not donor_eligibility_service.is_donor_match_allowed(database_session, donor)
        or donor_eligibility_service.outreach_preference_block_reason(
            donor,
            distance_km=recipient.distance,
            include_contact_window=False,
        )
    ):
        recipient.status = "INELIGIBLE"
        recipient.responded_at = None
        database_session.commit()
        return False
    token = email_service.generate_email_token()
    email_token = crud.create_email_token(
        database_session=database_session,
        recipient=recipient,
        token=token,
        expires_at=email_service.generate_expiry_time(),
    )
    settings = email_service.settings
    accept_url = f"{settings.backend_url}/email/accept/{token}"
    decline_url = f"{settings.backend_url}/email/decline/{token}"
    success = email_service.send_email(
        recipient_email=recipient.email,
        subject=email_service.build_email_subject(blood_request),
        html_body=email_service.build_html_email(
            donor=donor,
            blood_request=blood_request,
            accept_url=accept_url,
            decline_url=decline_url,
        ),
        text_body=email_service.build_text_email(
            donor=donor,
            blood_request=blood_request,
            accept_url=accept_url,
            decline_url=decline_url,
        ),
    )

    recipient.sent_at = datetime.now(timezone.utc)
    recipient.responded_at = None
    recipient.status = "PENDING" if success else "DELIVERY_FAILED"
    database_session.commit()
    database_session.refresh(recipient)
    return success

# ==========================================================
# CREATE CAMPAIGN
# ==========================================================

def create_notification_campaign(
    database_session: Session,
    blood_request: BloodRequest,
    compatible_donors: list[tuple[Donor, float]],
    stage_size: int = 5,
    stage_delay_minutes: int = 30,
) -> Notification:
    """
    Create a notification campaign and add all compatible donors
    as recipients.
    """

    title = (
        f"Blood Request #{blood_request.id} "
        f"({blood_request.blood_group})"
    )

    notification = crud.create_notification(
        database_session=database_session,
        blood_request_id=blood_request.id,
        title=title,
        stage_size=stage_size,
        stage_delay_minutes=stage_delay_minutes,
        target_acceptances=max(1, blood_request.units_remaining),
    )

    for outreach_order, (donor, distance) in enumerate(compatible_donors, start=1):

        crud.create_notification_recipient(
            database_session=database_session,
            notification_id=notification.id,
            donor=donor,
            distance=distance,
            status="QUEUED",
            stage_number=((outreach_order - 1) // stage_size) + 1,
            outreach_order=outreach_order,
        )

    crud.refresh_notification_statistics(
        database_session,
        notification,
    )

    return notification

# ==========================================================
# ADD RECIPIENT
# ==========================================================

def add_recipient(
    database_session: Session,
    notification: Notification,
    donor: Donor,
    distance: float,
):
    """
    Add one donor to a notification campaign.
    """

    return crud.create_notification_recipient(
        database_session=database_session,
        notification_id=notification.id,
        donor=donor,
        distance=distance,
    )


# ==========================================================
# REFRESH STATISTICS
# ==========================================================

def refresh_statistics(
    database_session: Session,
    notification: Notification,
):
    """
    Refresh campaign statistics.
    """

    notification = crud.refresh_notification_statistics(
        database_session,
        notification,
    )
    update_campaign_target_status(notification)
    database_session.commit()
    database_session.refresh(notification)
    return notification


def update_campaign_target_status(notification: Notification) -> bool:
    """Stop future outreach once the campaign has enough acceptances."""
    target_met = notification.accepted_count >= max(1, notification.target_acceptances)
    if notification.status != "COMPLETED":
        notification.status = "TARGET_MET" if target_met else "ACTIVE"
    if target_met:
        notification.next_stage_at = None
    return target_met
# ==========================================================
# SEND NOTIFICATION CAMPAIGN
# ==========================================================

def send_notification_campaign(
    database_session: Session,
    blood_request: BloodRequest,
    compatible_donors: list[tuple[Donor, float]],
    stage_size: int = 5,
    stage_delay_minutes: int = 30,
) -> tuple[Notification, StageDeliveryResult]:
    """
    Create a notification campaign and send emails to all
    compatible donors.
    """

    # ------------------------------------------------------
    # Create Campaign
    # ------------------------------------------------------

    notification = create_notification_campaign(
        database_session=database_session,
        blood_request=blood_request,
        compatible_donors=compatible_donors,
        stage_size=stage_size,
        stage_delay_minutes=stage_delay_minutes,
    )

    return notification, send_next_stage(
        database_session,
        notification,
        bypass_cooldown=True,
    )


def send_next_stage(
    database_session: Session,
    notification: Notification,
    *,
    bypass_cooldown: bool = False,
    now: datetime | None = None,
) -> StageDeliveryResult:
    """Release exactly one ranked donor batch when the campaign permits it."""
    current_time = now or datetime.now(timezone.utc)
    refresh_statistics(database_session, notification)

    if notification.status == "COMPLETED":
        raise ValueError("This outreach campaign has already been closed.")
    if update_campaign_target_status(notification):
        database_session.commit()
        raise ValueError("Enough donors have accepted. No further outreach is needed.")

    next_stage_at = _as_utc(notification.next_stage_at)
    if not bypass_cooldown and next_stage_at and current_time < next_stage_at:
        raise ValueError(
            f"The next donor batch can be sent after {next_stage_at.isoformat()}."
        )

    queued = [
        recipient
        for recipient in crud.get_notification_recipients(database_session, notification.id)
        if recipient.status == "QUEUED"
    ]
    if not queued:
        raise ValueError("There are no queued donors left in this campaign.")

    stage_number = min(recipient.stage_number for recipient in queued)
    stage_recipients = sorted(
        (recipient for recipient in queued if recipient.stage_number == stage_number),
        key=lambda recipient: recipient.outreach_order,
    )
    stage_recipients = [
        recipient
        for recipient in stage_recipients
        if donor_eligibility_service.is_contact_window_open(recipient.donor)
    ]
    if not stage_recipients:
        raise ValueError(
            "The next donor batch is outside its preferred contact hours. Try again during the configured window."
        )
    successful_deliveries = sum(
        _send_to_recipient(
            database_session,
            notification.blood_request,
            recipient,
        )
        for recipient in stage_recipients
    )

    notification.current_stage = stage_number
    notification.sent_at = notification.sent_at or current_time
    notification.last_stage_sent_at = current_time
    refresh_statistics(database_session, notification)
    target_met = update_campaign_target_status(notification)
    notification.next_stage_at = (
        current_time + timedelta(minutes=notification.stage_delay_minutes)
        if notification.queued_count > 0 and not target_met
        else None
    )
    database_session.commit()
    database_session.refresh(notification)

    attempted = len(stage_recipients)
    return StageDeliveryResult(
        stage_number=stage_number,
        attempted=attempted,
        sent=successful_deliveries,
        failed=attempted - successful_deliveries,
        queued_remaining=notification.queued_count,
        target_met=target_met,
        next_stage_at=notification.next_stage_at,
    )


def resend_pending_recipients(
    database_session: Session,
    notification: Notification,
) -> tuple[int, int]:
    """Resend a campaign only to donors who have not responded yet."""
    unresolved_recipients = [
        recipient
        for recipient in crud.get_notification_recipients(database_session, notification.id)
        if recipient.status in {"PENDING", "DELIVERY_FAILED"}
    ]
    pending_recipients = []
    for recipient in unresolved_recipients:
        donor = recipient.donor
        if (
            donor_eligibility_service.is_donor_match_allowed(database_session, donor)
            and donor_eligibility_service.travel_radius_allows(recipient.distance, donor)
            and donor_eligibility_service.is_contact_window_open(donor)
        ):
            pending_recipients.append(recipient)
        elif (
            not donor_eligibility_service.is_donor_match_allowed(database_session, donor)
            or not donor_eligibility_service.travel_radius_allows(recipient.distance, donor)
        ):
            recipient.status = "INELIGIBLE"
            recipient.responded_at = None
    if len(pending_recipients) != len(unresolved_recipients):
        database_session.commit()
        refresh_statistics(database_session, notification)
    successful_deliveries = sum(
        _send_to_recipient(database_session, notification.blood_request, recipient)
        for recipient in pending_recipients
    )
    if pending_recipients:
        notification.sent_at = datetime.now(timezone.utc)
        refresh_statistics(database_session, notification)
    return len(pending_recipients), successful_deliveries
