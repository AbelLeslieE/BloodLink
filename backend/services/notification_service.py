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

from sqlalchemy.orm import Session

from backend.database import crud
from backend.database.models import BloodRequest, Donor
from backend.database.notification import Notification

from backend.services import email_service

# ==========================================================
# CREATE CAMPAIGN
# ==========================================================

def create_notification_campaign(
    database_session: Session,
    blood_request: BloodRequest,
    compatible_donors: list[tuple[Donor, float]],
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
    )

    for donor, distance in compatible_donors:

        crud.create_notification_recipient(
            database_session=database_session,
            notification_id=notification.id,
            donor=donor,
            distance=distance,
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

    return crud.refresh_notification_statistics(
        database_session,
        notification,
    )
# ==========================================================
# SEND NOTIFICATION CAMPAIGN
# ==========================================================

def send_notification_campaign(
    database_session: Session,
    blood_request: BloodRequest,
    compatible_donors: list[tuple[Donor, float]],
) -> Notification:
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
    )

    # ------------------------------------------------------
    # Load Recipients
    # ------------------------------------------------------

    recipients = crud.get_notification_recipients(
        database_session,
        notification.id,
    )

    # ------------------------------------------------------
    # Send Email To Each Recipient
    # ------------------------------------------------------

    for recipient in recipients:

        donor = recipient.donor

        # ----------------------------------------------
        # Generate Token
        # ----------------------------------------------

        token = email_service.generate_email_token()

        expiry = email_service.generate_expiry_time()

        email_token = crud.create_email_token(
            database_session=database_session,
            recipient=recipient,
            token=token,
            expires_at=expiry,
        )

        # ----------------------------------------------
        # Create URLs
        # ----------------------------------------------

        settings = email_service.settings

        accept_url = (
            f"{settings.backend_url}"
            f"/email/accept/{token}"
        )

        decline_url = (
            f"{settings.backend_url}"
            f"/email/decline/{token}"
        )
        # ----------------------------------------------
        # Build Email
        # ----------------------------------------------

        subject = email_service.build_email_subject(
            blood_request,
        )

        html = email_service.build_html_email(
            donor=donor,
            blood_request=blood_request,
            accept_url=accept_url,
            decline_url=decline_url,
        )

        # ----------------------------------------------
        # Send Email
        # ----------------------------------------------

        success = email_service.send_email(
            recipient_email=recipient.email,
            subject=subject,
            html_body=html,
        )

        print(f"Sending email to {recipient.email} -> {success}")

    # ------------------------------------------------------
    # Refresh Statistics
    # ------------------------------------------------------

    refresh_statistics(
        database_session,
        notification,
    )

    return notification