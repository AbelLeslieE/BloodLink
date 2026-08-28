"""
Notification API Router
"""

from __future__ import annotations

from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from sqlalchemy.orm import Session

from backend.auth.dependencies import require_administrator
from backend.database.database import get_db
from backend.database.models import DonationHistory, User
from backend.database.donor_response import DonorResponse
from backend.database import crud

router = APIRouter(
    prefix="/api/notifications",
    tags=["Notifications"],
)


def _recipient_response_status(status: str | None) -> str:
    """Return the three response states understood by the administrator UI."""
    normalized = (status or "").strip().upper()

    if normalized in {"ACCEPTED", "YES"}:
        return "ACCEPTED"
    if normalized in {"DECLINED", "NO"}:
        return "DECLINED"

    # Old rows can contain delivery/sending placeholders or an empty value.
    # They are not donor decisions, so present them as a pending response.
    return "PENDING"
# ==========================================================
# GET ALL CAMPAIGNS
# ==========================================================

@router.get("")
def get_notifications(
    database_session: Session = Depends(get_db),
    _: User = Depends(require_administrator),
):
    """
    Return all notification campaigns together with
    the associated blood request summary.
    """

    notifications = crud.get_notifications(
        database_session,
    )

    result = []

    for notification in notifications:

        request = notification.blood_request

        result.append({

            "id": notification.id,

            "title": notification.title,

            "status": notification.status,

            "created_at": notification.created_at,

            "sent_at": notification.sent_at,

            "total_sent": notification.total_sent,

            "accepted_count": notification.accepted_count,

            "declined_count": notification.declined_count,

            "pending_count": notification.pending_count,

            "blood_request": {

                "id": request.id,

                "patient_name": request.patient_name,

                "hospital_name": request.hospital_name,

                "hospital_location": request.hospital_location,

                "blood_group": request.blood_group,

                "priority": request.priority,

                "units_required": request.units_required,

                "required_date": request.required_date,

                "status": request.status

            }

        })

    return result
# ==========================================================
# GET CAMPAIGN
# ==========================================================

@router.get("/{notification_id:int}")
def get_notification(
    notification_id: int,
    database_session: Session = Depends(get_db),
    _: User = Depends(require_administrator),
):

    notification = crud.get_notification_by_id(
        database_session,
        notification_id,
    )

    if notification is None:
        raise HTTPException(
            status_code=404,
            detail="Notification not found.",
        )

    return notification
# ==========================================================
# RECIPIENTS
# ==========================================================

@router.get("/{notification_id:int}/recipients")
def get_notification_recipients(
    notification_id: int,
    database_session: Session = Depends(get_db),
    _: User = Depends(require_administrator),
):
    """
    Return all recipients belonging to a notification campaign.
    """

    notification = crud.get_notification_by_id(
        database_session,
        notification_id,
    )

    if notification is None:
        raise HTTPException(
            status_code=404,
            detail="Notification not found.",
        )

    recipients = crud.get_notification_recipients(
        database_session,
        notification_id,
    )

    result = []

    for recipient in recipients:

        donor = recipient.donor
        response_status = _recipient_response_status(
            recipient.status,
        )
        donation = database_session.query(DonationHistory).filter(
            DonationHistory.donor_id == donor.id,
            DonationHistory.blood_request_id == recipient.notification.blood_request_id,
        ).first()

        result.append({

            "id": recipient.id,

            "email": recipient.email,

            "distance": recipient.distance,

            "status": response_status,

            "responded_at": (
                recipient.responded_at
                if response_status in {"ACCEPTED", "DECLINED"}
                else None
            ),
            "donation_confirmed": donation is not None,
            "points_awarded": donation.points_awarded if donation else 0,

            "sent_at": recipient.sent_at,

            "donor": {

                "id": donor.id,

                "full_name": donor.full_name,

                "blood_group": donor.blood_group,

                "phone": donor.phone,

                "email": donor.email,

                "district": donor.district,

                "status": donor.status,

            }

        })

    # Older campaigns can have a recorded email decision without a retained
    # NotificationRecipient row.  Include those responses so the dashboard
    # still shows the accepting donor and lets an administrator act on it.
    recipient_donor_ids = {recipient.donor_id for recipient in recipients}
    response_query = database_session.query(DonorResponse).filter(
        DonorResponse.blood_request_id == notification.blood_request_id,
    )
    if recipient_donor_ids:
        response_query = response_query.filter(
            ~DonorResponse.donor_id.in_(recipient_donor_ids),
        )

    for donor_response in response_query.all():
        donor = donor_response.donor
        donation = database_session.query(DonationHistory).filter(
            DonationHistory.donor_id == donor.id,
            DonationHistory.blood_request_id == notification.blood_request_id,
        ).first()

        result.append({
            "id": donor_response.id,
            "email": donor.email or "Not provided",
            "distance": None,
            "status": "ACCEPTED" if donor_response.response.upper() in {"YES", "ACCEPTED"} else "DECLINED",
            "responded_at": donor_response.responded_at,
            "donation_confirmed": donation is not None,
            "points_awarded": donation.points_awarded if donation else 0,
            "sent_at": None,
            "donor": {
                "id": donor.id,
                "full_name": donor.full_name,
                "blood_group": donor.blood_group,
                "phone": donor.phone,
                "email": donor.email,
                "district": donor.district,
                "status": donor.status,
            },
        })

    return result
# ==========================================================
# DASHBOARD STATS
# ==========================================================

@router.get("/stats/summary")
def notification_summary(
    database_session: Session = Depends(get_db),
    _: User = Depends(require_administrator),
):

    campaigns = crud.get_notifications(
        database_session,
    )

    return {

        "campaigns": len(campaigns),

        "emails_sent": sum(
            campaign.total_sent
            for campaign in campaigns
        ),

        "accepted": sum(
            campaign.accepted_count
            for campaign in campaigns
        ),

        "declined": sum(
            campaign.declined_count
            for campaign in campaigns
        ),

        "pending": sum(
            campaign.pending_count
            for campaign in campaigns
        ),

    }
