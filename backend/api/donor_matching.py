"""
BloodLink Donor Matching API
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.auth.dependencies import require_authentication
from backend.database.database import get_db
from backend.database.models import User
from backend.database import crud
from backend.database.schemas import FindMatchRequest
from backend.services import donor_matching_service
from backend.database.schemas import (
    FindMatchRequest,
    SendNotificationRequest,
)

from backend.services import notification_service
router = APIRouter(
    prefix="/api/match",
    tags=["Donor Matching"],
)
# ==========================================================
# FIND MATCH
# ==========================================================

@router.post("/find")
def find_matching_donors(
    request: FindMatchRequest,
    database_session: Session = Depends(get_db),
    _: User = Depends(require_authentication),
):
    """
    Return ranked compatible donors for a blood request.
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

    compatible_groups = (
        donor_matching_service.get_compatible_blood_groups(
            blood_request.blood_group,
        )
    )

    donors = crud.get_eligible_donors(
        database_session,
        compatible_groups,
    )

    ranked = donor_matching_service.rank_matching_donors(
        patient_blood_group=blood_request.blood_group,
        patient_district=None,
        patient_city=None,
        donors=donors,
    )

    return {
        "blood_request_id": blood_request.id,
        "total_matches": len(ranked),
        "matches": [
            {
                "rank": donor.rank,
                "score": donor.score.total_score,
                "donor": {
                    "id": donor.donor.id,
                    "name": donor.donor.full_name,
                    "blood_group": donor.donor.blood_group,
                    "phone": donor.donor.phone,
                    "email": donor.donor.email,
                    "district": donor.donor.district,
                    "status": donor.donor.status,
                },
            }
            for donor in ranked
        ],
    }
# ==========================================================
# SEND EMAIL CAMPAIGN
# ==========================================================

@router.post("/send")
def send_notification_campaign(
    request: SendNotificationRequest,
    database_session: Session = Depends(get_db),
    _: User = Depends(require_authentication),
):
    """
    Send notification emails to the selected donors.
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

    compatible_donors = []

    for donor_id in request.donor_ids:

        donor = crud.get_donor_by_id(
            database_session,
            donor_id,
        )

        if donor is None:
            continue

        compatible_donors.append(
            (
                donor,
                0.0,   # Placeholder distance (replace later with actual calculation)
            )
        )

    if not compatible_donors:
        raise HTTPException(
            status_code=400,
            detail="No valid donors selected.",
        )

    campaign = notification_service.send_notification_campaign(
        database_session=database_session,
        blood_request=blood_request,
        compatible_donors=compatible_donors,
    )

    return {
        "success": True,
        "campaign_id": campaign.id,
        "emails_sent": len(compatible_donors),
        "message": "Notification campaign created successfully.",
    }