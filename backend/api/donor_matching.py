"""
BloodLink Donor Matching API
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.auth.dependencies import require_administrator
from backend.database.database import get_db
from backend.database.models import User
from backend.database import crud
from backend.database.schemas import (
    FindMatchRequest,
    SendNotificationRequest,
)

from backend.services import donor_eligibility_service, donor_matching_service, email_service, notification_service
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
    _: User = Depends(require_administrator),
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

    policy = donor_eligibility_service.current_policy(database_session)
    donors = [
        donor for donor in donors
        if donor_eligibility_service.is_donor_match_allowed(
            database_session, donor, policy=policy
        )
    ]
    ranked = donor_matching_service.rank_matching_donors(
        patient_blood_group=blood_request.blood_group,
        patient_district=(blood_request.hospital_district or blood_request.hospital_location),
        patient_city=blood_request.hospital_city,
        donors=donors,
        request_latitude=blood_request.hospital_latitude,
        request_longitude=blood_request.hospital_longitude,
    )

    return {
        "blood_request_id": blood_request.id,
        "total_matches": len(ranked),
        "matches": [
            {
                "rank": donor.rank,
                "score": donor.score.total_score,
                "compatibility_percent": donor.score.blood_group_score,
                "compatibility_type": (
                    "Exact match"
                    if donor.score.blood_group_score == donor_matching_service.EXACT_BLOOD_MATCH_SCORE
                    else "Compatible match"
                ),
                "distance_km": donor.score.distance_km,
                "location_match_type": donor.score.location_match_type,
                "location_score": donor.score.location_score,
                "donor": {
                    "id": donor.donor.id,
                    "name": donor.donor.full_name,
                    "blood_group": donor.donor.blood_group,
                    "phone": donor.donor.phone,
                    "email": donor.donor.email,
                    "district": donor.donor.district,
                    "city": donor.donor.city,
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
    _: User = Depends(require_administrator),
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

        if (
            not donor_eligibility_service.is_donor_match_allowed(database_session, donor)
            or not donor_matching_service.is_compatible_donor(
                blood_request.blood_group, donor.blood_group
            )
        ):
            raise HTTPException(
                status_code=409,
                detail=f"Donor {donor_id} is not eligible for this request.",
            )

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

    configuration_error = email_service.delivery_configuration_error()
    if configuration_error:
        raise HTTPException(status_code=503, detail=configuration_error)

    campaign, emails_sent = notification_service.send_notification_campaign(
        database_session=database_session,
        blood_request=blood_request,
        compatible_donors=compatible_donors,
    )

    attempted = len(compatible_donors)
    failed_count = attempted - emails_sent
    if emails_sent == 0:
        raise HTTPException(
            status_code=502,
            detail="The email provider rejected every delivery. Check the Resend configuration and retry.",
        )

    return {
        "success": failed_count == 0,
        "campaign_id": campaign.id,
        "emails_attempted": attempted,
        "emails_sent": emails_sent,
        "failed_count": failed_count,
    }
