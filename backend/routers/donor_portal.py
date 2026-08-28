"""Private donor dashboard and administrator donation verification APIs."""

from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import Response
from pydantic import BaseModel, Field
from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.auth.dependencies import require_administrator, require_authentication, require_donor
from backend.config.rewards import POINTS_PER_CONFIRMED_DONATION, badge_for
from backend.database.database import get_db
from backend.database.donor_response import DonorResponse
from backend.database.models import BloodRequest, DonationCertificate, DonationHistory, Donor, User
from backend.services.certificate_service import ensure_certificate, render_certificate
from backend.services.donor_matching_service import get_compatible_blood_groups


donor_router = APIRouter(prefix="/api/donor-dashboard", tags=["donor dashboard"])
admin_router = APIRouter(prefix="/api/admin/donations", tags=["donation verification"])
DONOR_RESPONSE_OPEN_STATUSES = {"Pending", "Open", "Sent", "In Progress", "Donor Responded", "Awaiting Donation"}


class DonorDecision(BaseModel):
    response: str = Field(pattern="^(Yes|No)$")


def _donor_for_user(db: Session, user: User) -> Donor:
    donor = user.donor
    if donor is None:
        donor = db.scalar(select(Donor).where(func.lower(Donor.email) == user.email.lower()))
    if donor is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This account is not linked to a donor record. Ask an administrator to link it.",
        )
    return donor


def _response_label(response: DonorResponse | None, donation: DonationHistory | None) -> str:
    if donation is not None:
        return "Points Awarded"
    if response is None:
        return "Pending"
    if response.response.upper() in {"YES", "ACCEPTED"}:
        return "Waiting for Admin Verification"
    return "Responded No"


def _safe_request_payload(request: BloodRequest, response: DonorResponse | None, donation: DonationHistory | None) -> dict:
    """Return only the details a donor needs; never expose patient/bystander contacts."""
    return {
        "id": request.id,
        "blood_group": request.blood_group,
        "hospital_name": request.hospital_name,
        "hospital_location": request.hospital_location,
        "required_date": request.required_date,
        "priority": request.priority,
        "units_required": request.units_required,
        "message": f"{request.priority} blood requirement at {request.hospital_name}.",
        "request_status": request.status,
        "response": None if response is None else ("Yes" if response.response.upper() in {"YES", "ACCEPTED"} else "No"),
        "donor_status": _response_label(response, donation),
        "points_awarded": 0 if donation is None else donation.points_awarded,
    }


@donor_router.get("/summary")
def donor_summary(
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(require_donor)],
) -> dict:
    donor = _donor_for_user(db, user)
    history = list(db.scalars(select(DonationHistory).where(DonationHistory.donor_id == donor.id).order_by(DonationHistory.awarded_at.desc())))
    pending = db.scalar(
        select(func.count()).select_from(DonorResponse).where(
            DonorResponse.donor_id == donor.id,
            DonorResponse.response.in_(["YES", "ACCEPTED"]),
        )
    ) or 0
    return {
        "donor": {
            "name": donor.full_name,
            "blood_group": donor.blood_group,
            "donor_code": donor.donor_code,
            "email": user.email,
            "phone": user.phone,
            "department": donor.class_department,
        },
        "total_points": donor.total_points,
        "donation_count": donor.donation_count,
        "badge": badge_for(donor.total_points, donor.donation_count),
        "pending_verification": max(0, pending - len(history)),
        "eligibility_reminder": "Final eligibility must be confirmed by the hospital or blood bank.",
        "recent_donations": [
            {"id": item.id, "hospital_name": item.hospital_name, "donation_date": item.donation_date,
             "points_awarded": item.points_awarded, "status": item.status}
            for item in history[:5]
        ],
    }


@donor_router.get("/requests")
def donor_requests(
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(require_donor)],
) -> list[dict]:
    donor = _donor_for_user(db, user)
    open_requests = list(db.scalars(select(BloodRequest).where(
        BloodRequest.status.in_(["Pending", "In Progress", "Open", "Sent"]),
    ).order_by(BloodRequest.required_date, BloodRequest.id.desc())))
    requests = [
        item for item in open_requests
        if donor.blood_group in get_compatible_blood_groups(item.blood_group)
    ]
    responses = {item.blood_request_id: item for item in db.scalars(select(DonorResponse).where(DonorResponse.donor_id == donor.id))}
    donations = {item.blood_request_id: item for item in db.scalars(select(DonationHistory).where(DonationHistory.donor_id == donor.id))}
    return [_safe_request_payload(item, responses.get(item.id), donations.get(item.id)) for item in requests]


@donor_router.post("/requests/{request_id}/response")
def submit_response(
    request_id: int, decision: DonorDecision,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(require_donor)],
) -> dict:
    donor = _donor_for_user(db, user)
    request = db.get(BloodRequest, request_id)
    if request is None or request.status not in DONOR_RESPONSE_OPEN_STATUSES:
        raise HTTPException(status_code=404, detail="This blood request is no longer available.")
    if donor.blood_group not in get_compatible_blood_groups(request.blood_group):
        raise HTTPException(status_code=403, detail="This request is not compatible with your donor blood group.")
    if db.scalar(select(DonationHistory).where(DonationHistory.donor_id == donor.id, DonationHistory.blood_request_id == request_id)):
        raise HTTPException(status_code=409, detail="Donation has already been confirmed for this request.")
    response = db.scalar(select(DonorResponse).where(DonorResponse.donor_id == donor.id, DonorResponse.blood_request_id == request_id))
    if response is None:
        response = DonorResponse(donor_id=donor.id, blood_request_id=request_id, response=decision.response.upper())
        db.add(response)
    else:
        response.response = decision.response.upper()
        response.responded_at = datetime.now(timezone.utc)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        # The unique constraint prevents concurrent portal/email submissions
        # from creating two responses for one donor and request.
        raise HTTPException(status_code=409, detail="A response for this request was just recorded. Refresh to view it.")
    return {"success": True, "response": decision.response, "points_awarded": 0,
            "status": "Waiting for Admin Verification" if decision.response == "Yes" else "Responded No"}


@donor_router.patch("/privacy/leaderboard")
def update_leaderboard_privacy(
    hidden: bool,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(require_donor)],
) -> dict:
    donor = _donor_for_user(db, user)
    donor.hide_from_leaderboard = hidden
    user.hide_from_leaderboard = hidden
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Unable to update leaderboard privacy.")
    return {"hide_from_leaderboard": hidden}


@donor_router.get("/leaderboard")
def leaderboard(db: Annotated[Session, Depends(get_db)], _: Annotated[User, Depends(require_authentication)]) -> list[dict]:
    donors = db.scalars(select(Donor).where(Donor.hide_from_leaderboard.is_(False)).order_by(Donor.total_points.desc(), Donor.donation_count.desc()).limit(10))
    return [{"name": donor.full_name, "points": donor.total_points, "donations": donor.donation_count,
             "badge": badge_for(donor.total_points, donor.donation_count)} for donor in donors]


@donor_router.get("/certificates")
def donor_certificates(
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(require_donor)],
) -> list[dict]:
    """List every certificate earned by the signed-in donor."""
    donor = _donor_for_user(db, user)
    donations = list(db.scalars(select(DonationHistory).where(
        DonationHistory.donor_id == donor.id
    ).order_by(DonationHistory.donation_date.desc())))
    certificates = [ensure_certificate(db, donation) for donation in donations]
    if certificates:
        db.commit()
    return [{"id": certificate.id, "certificate_number": certificate.certificate_number,
             "issued_at": certificate.issued_at, "hospital_name": certificate.donation.hospital_name,
             "donation_date": certificate.donation.donation_date,
             "download_url": f"/api/donor-dashboard/certificates/{certificate.id}/download"}
            for certificate in certificates]


@donor_router.get("/certificates/{certificate_id}/download")
def download_certificate(
    certificate_id: int,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(require_donor)],
) -> Response:
    """Download a donor-owned certificate as a PDF."""
    donor = _donor_for_user(db, user)
    certificate = db.get(DonationCertificate, certificate_id)
    if certificate is None or certificate.donation.donor_id != donor.id:
        raise HTTPException(status_code=404, detail="Certificate not found.")
    content = render_certificate(certificate.donation, certificate)
    filename = f"BloodLink-certificate-{certificate.certificate_number}.pdf"
    return Response(content=content, media_type="application/pdf",
                    headers={"Content-Disposition": f'attachment; filename="{filename}"'})


@admin_router.get("/requests/{request_id}/responses")
def admin_responses(
    request_id: int, db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(require_administrator)],
) -> list[dict]:
    if db.get(BloodRequest, request_id) is None:
        raise HTTPException(status_code=404, detail="Blood request not found.")
    responses = db.scalars(select(DonorResponse).where(DonorResponse.blood_request_id == request_id))
    result = []
    for response in responses:
        donor = response.donor
        donation = db.scalar(select(DonationHistory).where(DonationHistory.donor_id == donor.id, DonationHistory.blood_request_id == request_id))
        result.append({"donor_id": donor.id, "donor_name": donor.full_name, "blood_group": donor.blood_group,
                       "email": donor.email, "phone": donor.phone, "response": response.response,
                       "donation_confirmed": donation is not None, "points_awarded": 0 if donation is None else donation.points_awarded,
                       "total_points": donor.total_points})
    return result


@admin_router.post("/requests/{request_id}/donors/{donor_id}/confirm")
def confirm_donation(
    request_id: int, donor_id: int,
    db: Annotated[Session, Depends(get_db)],
    administrator: Annotated[User, Depends(require_administrator)],
) -> dict:
    request, donor = db.get(BloodRequest, request_id), db.get(Donor, donor_id)
    if request is None or donor is None:
        raise HTTPException(status_code=404, detail="Blood request or donor not found.")
    response = db.scalar(select(DonorResponse).where(DonorResponse.donor_id == donor_id, DonorResponse.blood_request_id == request_id))
    if response is None or response.response.upper() not in {"YES", "ACCEPTED"}:
        raise HTTPException(status_code=409, detail="Only donors who responded Yes can be confirmed.")
    existing = db.scalar(select(DonationHistory).where(DonationHistory.donor_id == donor_id, DonationHistory.blood_request_id == request_id))
    if existing is not None:
        return {"success": True, "already_confirmed": True, "points_awarded": existing.points_awarded,
                "total_points": donor.total_points}
    now = datetime.now(timezone.utc)
    donation = DonationHistory(donor_id=donor_id, blood_request_id=request_id, hospital_name=request.hospital_name,
                               donation_date=date.today(), recorded_by=administrator.id,
                               points_awarded=POINTS_PER_CONFIRMED_DONATION, status="Points Awarded", awarded_at=now)
    donor.total_points += POINTS_PER_CONFIRMED_DONATION
    donor.donation_count += 1
    linked_users = db.scalars(select(User).where(or_(User.donor_id == donor_id, func.lower(User.email) == func.lower(donor.email)))).all()
    for account in linked_users:
        account.total_points += POINTS_PER_CONFIRMED_DONATION
        account.donation_count += 1
    db.add(donation)
    try:
        db.flush()
        ensure_certificate(db, donation)
        db.commit()
    except IntegrityError:
        # The database unique constraint is the final guard when two admins
        # confirm the same donation concurrently.
        db.rollback()
        existing = db.scalar(select(DonationHistory).where(
            DonationHistory.donor_id == donor_id,
            DonationHistory.blood_request_id == request_id,
        ))
        if existing is None:
            raise
        return {"success": True, "already_confirmed": True,
                "points_awarded": existing.points_awarded,
                "total_points": donor.total_points}
    return {"success": True, "already_confirmed": False, "points_awarded": POINTS_PER_CONFIRMED_DONATION,
            "total_points": donor.total_points, "badge": badge_for(donor.total_points, donor.donation_count)}
