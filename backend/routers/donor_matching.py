"""
BloodLink Donor Matching API
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.auth.dependencies import require_administrator
from backend.database.database import get_db
from backend.database.models import Donor, SavedMatch, User
from backend.database import crud
from backend.database.schemas import (
    FindMatchRequest,
    SendNotificationRequest,
)

from backend.services import (
    donor_matching_service,
    notification_service,
)

router = APIRouter(
    prefix="/api/match",
    tags=["Donor Matching"],
)

MATCHABLE_REQUEST_STATUSES = {
    "Pending", "Open", "Sent", "In Progress", "Donor Responded", "Awaiting Donation"
}


def _compatible_donors(database_session: Session, blood_request_id: int) -> tuple[object, list]:
    """Resolve and rank currently eligible donors for a blood request."""
    blood_request = crud.get_blood_request_by_id(database_session, blood_request_id)
    if blood_request is None:
        raise HTTPException(status_code=404, detail="Blood request not found.")
    if blood_request.status not in MATCHABLE_REQUEST_STATUSES:
        raise HTTPException(
            status_code=409,
            detail="This blood request is no longer open for donor matching.",
        )
    compatible_groups = [blood_request.blood_group.strip().upper()]
    donors = crud.get_eligible_donors(database_session, compatible_groups)
    return blood_request, donor_matching_service.rank_matching_donors(
        patient_blood_group=blood_request.blood_group,
        patient_district=blood_request.hospital_location,
        patient_city=None,
        donors=donors,
    )


# ==========================================================
# FIND MATCH
# ==========================================================

@router.post("/find")
def find_matching_donors(
    request: FindMatchRequest,
    database_session: Session = Depends(get_db),
    _: User = Depends(require_administrator),
):
    """
    Find and rank compatible donors.
    """

    blood_request, ranked = _compatible_donors(
        database_session, request.blood_request_id
    )

    return {
        "blood_request_id": blood_request.id,
        "total_matches": len(ranked),
        "matches": [
            {
                "rank": item.rank,
                "score": item.score.total_score,
                "donor": {
                    "id": item.donor.id,
                    "name": item.donor.full_name,
                    "blood_group": item.donor.blood_group,
                    "phone": item.donor.phone,
                    "email": item.donor.email,
                    "district": item.donor.district,
                    "status": item.donor.status,
                    "last_donation_date": item.donor.last_donation_date,
                },
            }
            for item in ranked
        ],
    }


# ==========================================================
# SEND NOTIFICATIONS
# ==========================================================

@router.post("/send")
def send_notifications(
    request: SendNotificationRequest,
    database_session: Session = Depends(get_db),
    _: User = Depends(require_administrator),
):
    """
    Send notification emails to selected donors.
    """

    blood_request = crud.get_blood_request_by_id(
        database_session,
        request.blood_request_id,
    )

    if blood_request is None:
        raise HTTPException(
            status_code=404,
            detail="Blood request not found.",
        )

    if blood_request.status not in MATCHABLE_REQUEST_STATUSES:
        raise HTTPException(
            status_code=409,
            detail="Notifications cannot be sent for a request that is no longer open for matching.",
        )

    selected_donors = []
    selected_donor_ids: set[int] = set()
    compatible_groups = [blood_request.blood_group.strip().upper()]

    for donor_id in request.donor_ids:

        if donor_id in selected_donor_ids:
            continue
        selected_donor_ids.add(donor_id)

        donor = crud.get_donor_by_id(
            database_session,
            donor_id,
        )

        if donor is None:
            raise HTTPException(status_code=404, detail=f"Donor {donor_id} was not found.")
        if donor.blood_group not in compatible_groups or donor.status != "Available":
            raise HTTPException(status_code=409, detail=f"Donor {donor_id} is not eligible for this request.")
        if not donor.email:
            raise HTTPException(status_code=422, detail=f"Donor {donor_id} does not have an email address.")

        selected_donors.append(
            (
                donor,
                0.0,
            )
        )

    if not selected_donors:
        raise HTTPException(
            status_code=400,
            detail="No donors selected.",
        )

    campaign, emails_sent = notification_service.send_notification_campaign(
        database_session=database_session,
        blood_request=blood_request,
        compatible_donors=selected_donors,
    )

    return {
        "success": True,
        "campaign_id": campaign.id,
        "emails_sent": emails_sent,
    }


@router.get("/availability")
def blood_availability(
    database_session: Session = Depends(get_db),
    _: User = Depends(require_administrator),
) -> list[dict]:
    """Return the actual count of currently available donors by blood group."""
    groups = ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"]
    donors = database_session.scalars(
        select(Donor).where(Donor.status == "Available")
    ).all()
    return [
        {"group": group, "available_donors": sum(donor.blood_group == group for donor in donors)}
        for group in groups
    ]


@router.get("/saved/{blood_request_id}")
def saved_matches(
    blood_request_id: int,
    database_session: Session = Depends(get_db),
    _: User = Depends(require_administrator),
) -> dict:
    donor_ids = database_session.scalars(
        select(SavedMatch.donor_id).where(SavedMatch.blood_request_id == blood_request_id)
    ).all()
    return {"donor_ids": donor_ids}


@router.post("/save")
def save_matches(
    request: SendNotificationRequest,
    database_session: Session = Depends(get_db),
    administrator: User = Depends(require_administrator),
) -> dict:
    blood_request, ranked = _compatible_donors(database_session, request.blood_request_id)
    eligible_ids = {item.donor.id for item in ranked}
    selected_ids = set(request.donor_ids)
    if not selected_ids:
        raise HTTPException(status_code=400, detail="Select at least one compatible donor.")
    invalid_ids = selected_ids - eligible_ids
    if invalid_ids:
        raise HTTPException(status_code=409, detail="One or more selected donors are no longer eligible.")
    database_session.execute(
        delete(SavedMatch).where(SavedMatch.blood_request_id == blood_request.id)
    )
    database_session.add_all(
        [
            SavedMatch(
                blood_request_id=blood_request.id,
                donor_id=donor_id,
                saved_by=administrator.id,
            )
            for donor_id in selected_ids
        ]
    )
    try:
        database_session.commit()
    except IntegrityError as error:
        database_session.rollback()
        raise HTTPException(status_code=409, detail="Unable to save this donor selection.") from error
    return {"success": True, "saved_count": len(selected_ids)}
