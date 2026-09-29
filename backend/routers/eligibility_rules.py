"""Administrator controls for operational donor eligibility pre-screening."""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field, model_validator
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.auth.dependencies import require_administrator
from backend.database.database import get_db
from backend.database.models import Donor, EligibilityPolicy, User
from backend.services import donor_eligibility_service
from backend.services.audit_service import record_audit_event


router = APIRouter(
    prefix="/api/admin/technical/eligibility-policy",
    tags=["eligibility policy"],
)


class EligibilityPolicyUpdate(BaseModel):
    enforcement_mode: Literal["ADVISORY", "ENFORCED"]
    minimum_age_years: int = Field(ge=18, le=65)
    maximum_age_years: int = Field(ge=18, le=65)
    minimum_weight_kg: Decimal = Field(ge=Decimal("45.00"), le=Decimal("150.00"))
    require_complete_profile: bool = False
    reviewer_name: str | None = Field(default=None, max_length=200)
    review_notes: str | None = Field(default=None, max_length=2000)
    clinical_review_confirmed: bool = False

    @model_validator(mode="after")
    def validate_policy(self):
        if self.minimum_age_years > self.maximum_age_years:
            raise ValueError("Minimum age cannot be greater than maximum age.")
        if self.enforcement_mode == "ENFORCED":
            if not self.clinical_review_confirmed:
                raise ValueError("Confirm medical-officer review before enforcing this policy.")
            if not (self.reviewer_name or "").strip():
                raise ValueError("Medical officer reviewer name is required for enforcement.")
            if len((self.review_notes or "").strip()) < 10:
                raise ValueError("Add review notes of at least 10 characters before enforcement.")
        return self


def _evaluation_payload(evaluation: donor_eligibility_service.EligibilityEvaluation) -> dict:
    return {
        "screening_passed": evaluation.screening_passed,
        "match_allowed": evaluation.match_allowed,
        "reasons": list(evaluation.reasons),
        "warnings": list(evaluation.warnings),
        "policy_mode": evaluation.policy_mode,
        "final_decision_required": True,
    }


def _policy_payload(database_session: Session, policy: EligibilityPolicy) -> dict:
    donors = list(database_session.scalars(select(Donor).order_by(Donor.id)).all())
    evaluations = [
        donor_eligibility_service.evaluate_donor(database_session, donor, policy=policy)
        for donor in donors
    ]
    return {
        "id": policy.id,
        "enforcement_mode": policy.enforcement_mode,
        "minimum_age_years": policy.minimum_age_years,
        "maximum_age_years": policy.maximum_age_years,
        "minimum_weight_kg": policy.minimum_weight_kg,
        "require_complete_profile": policy.require_complete_profile,
        "reviewer_name": policy.reviewer_name,
        "review_notes": policy.review_notes,
        "reviewed_at": policy.reviewed_at,
        "source_reference": policy.source_reference,
        "version": policy.version,
        "updated_at": policy.updated_at,
        "summary": {
            "total_donors": len(evaluations),
            "screening_passed": sum(item.screening_passed for item in evaluations),
            "review_needed": sum(bool(item.reasons or item.warnings) for item in evaluations),
            "matching_allowed": sum(item.match_allowed for item in evaluations),
            "matching_blocked": sum(not item.match_allowed for item in evaluations),
        },
        "fixed_safeguards": [
            "Recorded haemoglobin below 12.5 g/dL is blocked when enforced.",
            "Recorded blood pressure outside the accepted range is blocked when enforced.",
            "Medication and medical conditions always require human review.",
            "Final donor fitness remains a blood-centre medical decision.",
        ],
    }


@router.get("")
def get_eligibility_policy(
    _: Annotated[User, Depends(require_administrator)],
    database_session: Annotated[Session, Depends(get_db)],
) -> dict:
    policy = donor_eligibility_service.current_policy(database_session)
    return _policy_payload(database_session, policy)


@router.put("")
def update_eligibility_policy(
    data: EligibilityPolicyUpdate,
    request: Request,
    administrator: Annotated[User, Depends(require_administrator)],
    database_session: Annotated[Session, Depends(get_db)],
) -> dict:
    policy = database_session.get(EligibilityPolicy, donor_eligibility_service.POLICY_ID)
    if policy is None:
        policy = EligibilityPolicy(
            id=donor_eligibility_service.POLICY_ID,
            source_reference=donor_eligibility_service.OFFICIAL_SOURCE_REFERENCE,
        )
        database_session.add(policy)

    previous = {
        "mode": policy.enforcement_mode,
        "minimum_age": policy.minimum_age_years,
        "maximum_age": policy.maximum_age_years,
        "minimum_weight_kg": str(policy.minimum_weight_kg),
        "require_complete_profile": policy.require_complete_profile,
        "version": policy.version,
    }
    policy.enforcement_mode = data.enforcement_mode
    policy.minimum_age_years = data.minimum_age_years
    policy.maximum_age_years = data.maximum_age_years
    policy.minimum_weight_kg = data.minimum_weight_kg
    policy.require_complete_profile = data.require_complete_profile
    policy.updated_by = administrator.id
    policy.version = int(policy.version or 0) + 1
    if data.enforcement_mode == donor_eligibility_service.ENFORCED:
        policy.reviewer_name = data.reviewer_name.strip()
        policy.review_notes = data.review_notes.strip()
        policy.reviewed_at = datetime.now(timezone.utc)
    else:
        policy.reviewer_name = None
        policy.review_notes = None
        policy.reviewed_at = None

    record_audit_event(
        database_session,
        category="ELIGIBILITY",
        action="ELIGIBILITY_POLICY_UPDATED",
        actor=administrator,
        target_type="eligibility_policy",
        target_id=policy.id,
        request=request,
        details={
            "previous": previous,
            "current": {
                "mode": policy.enforcement_mode,
                "minimum_age": policy.minimum_age_years,
                "maximum_age": policy.maximum_age_years,
                "minimum_weight_kg": str(policy.minimum_weight_kg),
                "require_complete_profile": policy.require_complete_profile,
                "version": policy.version,
                "reviewer_name": policy.reviewer_name,
            },
        },
    )
    database_session.commit()
    database_session.refresh(policy)
    return _policy_payload(database_session, policy)


@router.get("/donors/{donor_id}")
def donor_eligibility_review(
    donor_id: int,
    _: Annotated[User, Depends(require_administrator)],
    database_session: Annotated[Session, Depends(get_db)],
) -> dict:
    donor = database_session.get(Donor, donor_id)
    if donor is None:
        raise HTTPException(status_code=404, detail="Donor not found.")
    policy = donor_eligibility_service.current_policy(database_session)
    return {
        "donor_id": donor.id,
        "donor_name": donor.full_name,
        "evaluation": _evaluation_payload(
            donor_eligibility_service.evaluate_donor(
                database_session, donor, policy=policy
            )
        ),
    }
