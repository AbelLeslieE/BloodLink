"""
Notification API Router
"""

from __future__ import annotations

from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from sqlalchemy.orm import Session

from backend.auth.dependencies import require_authentication
from backend.database.database import get_db
from backend.database.models import User
from backend.database import crud

router = APIRouter(
    prefix="/api/notifications",
    tags=["Notifications"],
)
# ==========================================================
# GET ALL CAMPAIGNS
# ==========================================================

@router.get("")
def get_notifications(
    database_session: Session = Depends(get_db),
    _: User = Depends(require_authentication),
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

@router.get("/{notification_id}")
def get_notification(
    notification_id: int,
    database_session: Session = Depends(get_db),
    _: User = Depends(require_authentication),
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

@router.get("/{notification_id}/recipients")
def get_notification_recipients(
    notification_id: int,
    database_session: Session = Depends(get_db),
    _: User = Depends(require_authentication),
):
    """
    Return all recipients belonging to a notification campaign.
    """

    recipients = crud.get_notification_recipients(
        database_session,
        notification_id,
    )

    result = []

    for recipient in recipients:

        donor = recipient.donor

        result.append({

            "id": recipient.id,

            "email": recipient.email,

            "distance": recipient.distance,

            "status": recipient.status,

            "responded_at": recipient.responded_at,

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

    return result
# ==========================================================
# DASHBOARD STATS
# ==========================================================

@router.get("/stats/summary")
def notification_summary(
    database_session: Session = Depends(get_db),
    _: User = Depends(require_authentication),
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