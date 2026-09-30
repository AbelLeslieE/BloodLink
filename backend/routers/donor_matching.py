"""
BloodLink Donor Matching API
"""

from __future__ import annotations

from collections import Counter

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
    donor_eligibility_service,
    donor_matching_service,
    email_service,
    notification_service,
)

router = APIRouter(
    prefix="/api/match",
    tags=["Donor Matching"],
)

MATCHABLE_REQUEST_STATUSES = {
    "Pending", "Open", "Sent", "In Progress", "Donor Responded", "Awaiting Donation",
    "Partially Fulfilled",
}


def _compatible_donors(database_session: Session, blood_request_id: int) -> tuple[object, list, dict, dict, object, int]:
    """Resolve and rank currently eligible donors for a blood request."""
    blood_request = crud.get_blood_request_by_id(database_session, blood_request_id)
    if blood_request is None:
        raise HTTPException(status_code=404, detail="Blood request not found.")
    if blood_request.status not in MATCHABLE_REQUEST_STATUSES:
        raise HTTPException(
            status_code=409,
            detail="This blood request is no longer open for donor matching.",
        )
    compatible_groups = donor_matching_service.get_compatible_blood_groups(
        blood_request.blood_group
    )
    donors = crud.get_eligible_donors(database_session, compatible_groups)
    policy = donor_eligibility_service.current_policy(database_session)
    evaluations = {
        donor.id: donor_eligibility_service.evaluate_donor(
            database_session, donor, policy=policy
        )
        for donor in donors
    }
    included = [donor for donor in donors if evaluations[donor.id].match_allowed]
    excluded_reasons = Counter(
        reason
        for donor in donors
        if not evaluations[donor.id].match_allowed
        for reason in (evaluations[donor.id].reasons or ("Operational eligibility policy",))
    )
    ranked = donor_matching_service.rank_matching_donors(
        patient_blood_group=blood_request.blood_group,
        # Historical requests only have hospital_location.  Keep it as a
        # fallback district hint until an administrator records structured data.
        patient_district=(blood_request.hospital_district or blood_request.hospital_location),
        patient_city=blood_request.hospital_city,
        donors=included,
        request_latitude=blood_request.hospital_latitude,
        request_longitude=blood_request.hospital_longitude,
    )
    preference_filtered = []
    for item in ranked:
        reason = donor_eligibility_service.outreach_preference_block_reason(
            item.donor,
            distance_km=item.score.distance_km,
        )
        if reason:
            excluded_reasons[reason] += 1
        else:
            preference_filtered.append(item)
    return (
        blood_request,
        preference_filtered,
        evaluations,
        dict(excluded_reasons),
        policy,
        len(donors) - len(preference_filtered),
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

    blood_request, ranked, evaluations, excluded_reasons, policy, excluded_count = _compatible_donors(
        database_session, request.blood_request_id
    )

    return {
        "blood_request_id": blood_request.id,
        "total_matches": len(ranked),
        "matches": [
            {
                "rank": item.rank,
                "score": item.score.total_score,
                "compatibility_percent": item.score.blood_group_score,
                "compatibility_type": (
                    "Exact match"
                    if item.score.blood_group_score == donor_matching_service.EXACT_BLOOD_MATCH_SCORE
                    else "Compatible match"
                ),
                "distance_km": item.score.distance_km,
                "location_match_type": item.score.location_match_type,
                "location_score": item.score.location_score,
                "screening": {
                    "passed": evaluations[item.donor.id].screening_passed,
                    "mode": evaluations[item.donor.id].policy_mode,
                    "reasons": list(evaluations[item.donor.id].reasons),
                    "warnings": list(evaluations[item.donor.id].warnings),
                    "final_decision_required": True,
                },
                "donor": {
                    "id": item.donor.id,
                    "name": item.donor.full_name,
                    "blood_group": item.donor.blood_group,
                    "phone": item.donor.phone,
                    "email": item.donor.email,
                    "district": item.donor.district,
                    "city": item.donor.city,
                    "status": item.donor.status,
                    "last_donation_date": item.donor.last_donation_date,
                    "availability_paused_until": item.donor.availability_paused_until,
                    "travel_radius_km": item.donor.travel_radius_km,
                    "contact_window_start": item.donor.contact_window_start,
                    "contact_window_end": item.donor.contact_window_end,
                },
            }
            for item in ranked
        ],
        "eligibility_policy": {
            "mode": policy.enforcement_mode,
            "version": policy.version,
            "excluded_count": excluded_count,
            "excluded_reasons": excluded_reasons,
            "final_decision_required": True,
        },
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

    blood_request, ranked, _, _, _, _ = _compatible_donors(
        database_session,
        request.blood_request_id,
    )
    selected_donor_ids = set(request.donor_ids)
    eligible_ids = {item.donor.id for item in ranked}
    invalid_ids = selected_donor_ids - eligible_ids
    if invalid_ids:
        raise HTTPException(
            status_code=409,
            detail="One or more selected donors are no longer eligible for this request.",
        )

    # Preserve the match engine's ranking instead of the order in which boxes
    # happened to be selected in the browser.
    selected_donors = [
        (item.donor, item.score.distance_km)
        for item in ranked
        if item.donor.id in selected_donor_ids
    ]
    missing_email = next((donor.id for donor, _ in selected_donors if not donor.email), None)
    if missing_email is not None:
        raise HTTPException(
            status_code=422,
            detail=f"Donor {missing_email} does not have an email address.",
        )

    if not selected_donors:
        raise HTTPException(
            status_code=400,
            detail="No donors selected.",
        )

    configuration_error = email_service.delivery_configuration_error()
    if configuration_error:
        raise HTTPException(status_code=503, detail=configuration_error)

    campaign, delivery = notification_service.send_notification_campaign(
        database_session=database_session,
        blood_request=blood_request,
        compatible_donors=selected_donors,
        stage_size=request.stage_size,
        stage_delay_minutes=request.stage_delay_minutes,
    )

    if delivery.sent == 0:
        raise HTTPException(
            status_code=502,
            detail=(
                "The email provider rejected every delivery. Check the Resend API key, "
                "verified EMAIL_FROM sender, and Resend delivery logs, then retry the campaign."
            ),
        )

    return {
        "success": delivery.failed == 0,
        "campaign_id": campaign.id,
        "current_stage": delivery.stage_number,
        "emails_attempted": delivery.attempted,
        "emails_sent": delivery.sent,
        "failed_count": delivery.failed,
        "queued_count": delivery.queued_remaining,
        "target_acceptances": campaign.target_acceptances,
        "next_stage_at": delivery.next_stage_at,
    }


@router.get("/availability")
def blood_availability(
    database_session: Session = Depends(get_db),
    _: User = Depends(require_administrator),
) -> list[dict]:
    """Return the actual count of currently available donors by blood group."""
    donor_eligibility_service.restore_expired_deferrals(database_session)
    groups = ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"]
    donors = database_session.scalars(
        select(Donor).where(Donor.status == "Available")
    ).all()
    policy = donor_eligibility_service.current_policy(database_session)
    donors = [
        donor for donor in donors
        if donor_eligibility_service.is_donor_match_allowed(
            database_session, donor, policy=policy
        )
    ]
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
    blood_request, ranked, _, _, _, _ = _compatible_donors(database_session, request.blood_request_id)
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
