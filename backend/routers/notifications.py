"""
Notification API Router
"""

from __future__ import annotations

import csv
import io

from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from backend.auth.dependencies import require_administrator
from backend.database.database import get_db
from backend.database.models import DonationHistory, SavedMatch, User
from backend.database.donor_response import DonorResponse
from backend.database.notification import Notification
from backend.database.notification_recipient import NotificationRecipient
from backend.database import crud
from backend.services import notification_service

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


def _notification_or_404(database_session: Session, notification_id: int):
    notification = crud.get_notification_by_id(database_session, notification_id)
    if notification is None:
        raise HTTPException(status_code=404, detail="Notification not found.")
    return notification
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


@router.post("/{notification_id:int}/resend-pending")
def resend_pending_recipients(
    notification_id: int,
    database_session: Session = Depends(get_db),
    _: User = Depends(require_administrator),
) -> dict:
    """Send fresh response links to unresolved recipients in one campaign."""
    notification = _notification_or_404(database_session, notification_id)
    if notification.status == "COMPLETED" or notification.blood_request.status in {"Fulfilled", "Closed", "Cancelled"}:
        raise HTTPException(status_code=409, detail="This request is no longer open for donor responses.")

    pending_count, sent_count = notification_service.resend_pending_recipients(
        database_session,
        notification,
    )
    if pending_count == 0:
        raise HTTPException(status_code=409, detail="There are no pending recipients to resend.")
    return {"success": True, "pending_recipients": pending_count, "emails_sent": sent_count}


@router.post("/{notification_id:int}/complete")
def complete_notification_request(
    notification_id: int,
    database_session: Session = Depends(get_db),
    _: User = Depends(require_administrator),
) -> dict:
    """Close a request after its donor-response workflow is complete."""
    notification = _notification_or_404(database_session, notification_id)
    notification.status = "COMPLETED"
    notification.blood_request.status = "Fulfilled"
    database_session.commit()
    return {
        "success": True,
        "notification_status": notification.status,
        "request_status": notification.blood_request.status,
    }


@router.get("/{notification_id:int}/export")
def export_notification_report(
    notification_id: int,
    database_session: Session = Depends(get_db),
    _: User = Depends(require_administrator),
):
    """Export the selected blood-request campaign and donor responses as CSV."""
    notification = _notification_or_404(database_session, notification_id)
    request = notification.blood_request
    recipients = crud.get_notification_recipients(database_session, notification.id)

    output = io.StringIO(newline="")
    writer = csv.writer(output)
    writer.writerow([
        "Campaign ID", "Request ID", "Patient", "Hospital", "Blood Group",
        "Request Status", "Campaign Sent At", "Donor", "Donor Email",
        "Recipient Status", "Recipient Sent At", "Responded At", "Distance",
    ])
    for recipient in recipients:
        writer.writerow([
            notification.id,
            request.id,
            request.patient_name,
            request.hospital_name,
            request.blood_group,
            request.status,
            notification.sent_at.isoformat() if notification.sent_at else "",
            recipient.donor.full_name,
            recipient.email,
            _recipient_response_status(recipient.status),
            recipient.sent_at.isoformat() if recipient.sent_at else "",
            recipient.responded_at.isoformat() if recipient.responded_at else "",
            recipient.distance if recipient.distance is not None else "",
        ])

    filename = f"blood-request-{request.id}-report.csv"
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.delete("/{notification_id:int}")
def delete_notification_request(
    notification_id: int,
    database_session: Session = Depends(get_db),
    _: User = Depends(require_administrator),
) -> dict:
    """Delete an unfulfilled request and all of its campaign response data."""
    notification = _notification_or_404(database_session, notification_id)
    request = notification.blood_request
    has_donations = database_session.scalar(
        select(DonationHistory.id).where(DonationHistory.blood_request_id == request.id)
    )
    if has_donations is not None:
        raise HTTPException(
            status_code=409,
            detail="A request with confirmed donations cannot be deleted. Mark it completed instead.",
        )

    database_session.execute(
        delete(SavedMatch).where(SavedMatch.blood_request_id == request.id)
    )
    database_session.delete(request)
    database_session.commit()
    return {"success": True, "deleted_request_id": request.id}
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

    # Older portal-only responses have no NotificationRecipient row. Include
    # only those donors, never a recipient that belongs to another campaign
    # for this request. Otherwise a campaign with zero emails can incorrectly
    # display responses (and totals) from a separate campaign.
    recipient_donor_ids = set(database_session.scalars(
        select(NotificationRecipient.donor_id)
        .join(Notification)
        .where(Notification.blood_request_id == notification.blood_request_id)
    ).all())
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
