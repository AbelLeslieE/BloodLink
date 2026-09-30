"""Donor availability, deferrals, and operational pre-screening rules.

BloodLink uses these checks as operational safeguards only. They decide who
may appear in automated matching and outreach; a qualified medical officer at
the blood centre remains responsible for final donor selection.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal
from zoneinfo import ZoneInfo

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from backend.config.settings import get_settings
from backend.database.models import Donor, EligibilityPolicy


AVAILABLE = "Available"
UNAVAILABLE = "Unavailable"
DEFERRED = "Deferred"
ALLOWED_AVAILABILITY_STATUSES = {AVAILABLE, UNAVAILABLE, DEFERRED}
ADVISORY = "ADVISORY"
ENFORCED = "ENFORCED"
POLICY_ID = 1
OFFICIAL_MINIMUM_AGE = 18
OFFICIAL_MAXIMUM_AGE = 65
OFFICIAL_MINIMUM_WEIGHT_KG = Decimal("45.00")
OFFICIAL_SOURCE_REFERENCE = (
    "https://clinicalestablishments.mohfw.gov.in/sites/default/files/2023-03/1491_0.pdf"
)


@dataclass(frozen=True)
class EligibilityEvaluation:
    """One donor's operational pre-screening result."""

    screening_passed: bool
    match_allowed: bool
    reasons: tuple[str, ...]
    warnings: tuple[str, ...]
    policy_mode: str


def current_policy(database_session: Session) -> EligibilityPolicy:
    """Return the configured singleton policy or safe in-memory defaults."""
    policy = database_session.scalar(
        select(EligibilityPolicy).where(EligibilityPolicy.id == POLICY_ID)
    )
    if policy is not None:
        return policy
    return EligibilityPolicy(
        id=POLICY_ID,
        enforcement_mode=ADVISORY,
        minimum_age_years=OFFICIAL_MINIMUM_AGE,
        maximum_age_years=OFFICIAL_MAXIMUM_AGE,
        minimum_weight_kg=OFFICIAL_MINIMUM_WEIGHT_KG,
        require_complete_profile=False,
        source_reference=OFFICIAL_SOURCE_REFERENCE,
        version=1,
    )


def donor_age(donor: Donor, *, as_of: date | None = None) -> int | None:
    """Calculate completed years without approximate day arithmetic."""
    if donor.date_of_birth is None:
        return None
    today = as_of or date.today()
    return today.year - donor.date_of_birth.year - (
        (today.month, today.day) < (donor.date_of_birth.month, donor.date_of_birth.day)
    )


def _as_utc(value: datetime | None) -> datetime:
    current = value or datetime.now(timezone.utc)
    if current.tzinfo is None:
        return current.replace(tzinfo=timezone.utc)
    return current.astimezone(timezone.utc)


def is_availability_pause_active(
    donor: Donor,
    *,
    now: datetime | None = None,
) -> bool:
    """Return whether a donor-controlled temporary pause is still active."""
    paused_until = donor.availability_paused_until
    if paused_until is None:
        return False
    if paused_until.tzinfo is None:
        paused_until = paused_until.replace(tzinfo=timezone.utc)
    return paused_until.astimezone(timezone.utc) > _as_utc(now)


def is_contact_window_open(
    donor: Donor,
    *,
    now: datetime | None = None,
) -> bool:
    """Evaluate the donor's preferred outreach window in deployment local time."""
    start = donor.contact_window_start
    end = donor.contact_window_end
    if start is None and end is None:
        return True
    if start is None or end is None or start == end:
        return False
    local_time = _as_utc(now).astimezone(
        ZoneInfo(get_settings().request_timezone)
    ).time().replace(tzinfo=None)
    start = time(start.hour, start.minute, start.second)
    end = time(end.hour, end.minute, end.second)
    if start < end:
        return start <= local_time < end
    return local_time >= start or local_time < end


def travel_radius_allows(distance_km: float | None, donor: Donor) -> bool:
    """Apply a distance preference only when both locations can be measured."""
    return (
        distance_km is None
        or donor.travel_radius_km is None
        or distance_km <= donor.travel_radius_km
    )


def outreach_preference_block_reason(
    donor: Donor,
    *,
    distance_km: float | None = None,
    now: datetime | None = None,
    include_contact_window: bool = True,
) -> str | None:
    """Explain why automated outreach should not contact this donor now."""
    if is_availability_pause_active(donor, now=now):
        return "Donor-controlled availability pause is active."
    if not travel_radius_allows(distance_km, donor):
        return "Request is outside the donor's preferred travel radius."
    if include_contact_window and not is_contact_window_open(donor, now=now):
        return "Current time is outside the donor's preferred contact hours."
    return None


def evaluate_donor(
    database_session: Session,
    donor: Donor,
    *,
    policy: EligibilityPolicy | None = None,
    as_of: date | None = None,
    now: datetime | None = None,
) -> EligibilityEvaluation:
    """Evaluate known data without claiming clinical fitness to donate."""
    policy = policy or current_policy(database_session)
    reasons: list[str] = []
    warnings: list[str] = []

    if not is_donor_currently_available(donor, as_of=as_of, now=now):
        if is_availability_pause_active(donor, now=now):
            reasons.append(
                "Donor-controlled availability is paused until "
                f"{donor.availability_paused_until.isoformat()}."
            )
        elif is_active_deferral(donor, as_of=as_of):
            reasons.append(f"Temporary deferral is active until {donor.deferred_until.isoformat()}.")
        else:
            reasons.append("Donor is not marked available.")

    age = donor_age(donor, as_of=as_of)
    if age is None:
        message = "Date of birth is not recorded."
        (reasons if policy.require_complete_profile else warnings).append(message)
    elif age < policy.minimum_age_years:
        reasons.append(f"Recorded age is below the configured minimum of {policy.minimum_age_years}.")
    elif age > policy.maximum_age_years:
        reasons.append(f"Recorded age is above the configured maximum of {policy.maximum_age_years}.")

    if donor.weight is None:
        message = "Weight is not recorded."
        (reasons if policy.require_complete_profile else warnings).append(message)
    elif Decimal(donor.weight) < Decimal(policy.minimum_weight_kg):
        reasons.append(f"Recorded weight is below {Decimal(policy.minimum_weight_kg):g} kg.")

    hb_status = (donor.hb_above_12_5 or "Not Recorded").strip().lower()
    if hb_status == "no":
        reasons.append("Haemoglobin is recorded below 12.5 g/dL.")
    elif hb_status != "yes":
        message = "Haemoglobin screening is not recorded."
        (reasons if policy.require_complete_profile else warnings).append(message)

    bp_status = (donor.bp_normal or "Not Recorded").strip().lower()
    if bp_status == "no":
        reasons.append("Blood pressure screening is recorded outside the accepted range.")
    elif bp_status != "yes":
        message = "Blood pressure screening is not recorded."
        (reasons if policy.require_complete_profile else warnings).append(message)

    medication = (donor.regular_medication or "Not Recorded").strip().lower()
    if medication == "yes":
        warnings.append("Regular medication requires medical-officer review; it is not automatically disqualifying.")
    elif medication != "no":
        warnings.append("Medication information is not recorded.")

    condition = (donor.medical_conditions or "").strip()
    if condition and condition.lower() not in {"no", "none", "nil", "n/a", "na"}:
        warnings.append("Recorded medical conditions require medical-officer review.")

    screening_passed = not reasons
    enforced = (policy.enforcement_mode or ADVISORY).upper() == ENFORCED
    # Advisory mode reports problems without disrupting existing operations.
    # Enforced mode blocks automated matching until all configured checks pass.
    match_allowed = is_donor_currently_available(donor, as_of=as_of, now=now) and (
        screening_passed or not enforced
    )
    return EligibilityEvaluation(
        screening_passed=screening_passed,
        match_allowed=match_allowed,
        reasons=tuple(reasons),
        warnings=tuple(warnings),
        policy_mode=ENFORCED if enforced else ADVISORY,
    )


def is_donor_match_allowed(
    database_session: Session,
    donor: Donor,
    *,
    policy: EligibilityPolicy | None = None,
    as_of: date | None = None,
    now: datetime | None = None,
) -> bool:
    """Return whether automated matching/outreach may include this donor."""
    return evaluate_donor(
        database_session, donor, policy=policy, as_of=as_of, now=now
    ).match_allowed


def post_donation_deferral_days(donor: Donor) -> int:
    """Return the configured whole-blood interval for this donor."""
    settings = get_settings()
    gender = (donor.gender or "").strip().lower()
    if gender == "male":
        return settings.donor_deferral_days_male
    if gender == "female":
        return settings.donor_deferral_days_female
    # Use the more conservative configured interval when the profile does not
    # map to the two guideline-specific categories.
    return settings.donor_deferral_days_other


def apply_post_donation_deferral(donor: Donor, donation_date: date) -> date:
    """Start the configured recovery interval after a confirmed donation."""
    days = post_donation_deferral_days(donor)
    donor.status = DEFERRED
    donor.deferred_until = donation_date + timedelta(days=days)
    donor.deferral_reason = f"Post-donation recovery period ({days} days)"
    return donor.deferred_until


def is_active_deferral(donor: Donor, *, as_of: date | None = None) -> bool:
    """Return whether a donor is still inside a recorded deferral period."""
    today = as_of or date.today()
    return bool(
        donor.deferred_until
        and donor.deferred_until > today
        and donor.status == DEFERRED
    )


def is_donor_currently_available(
    donor: Donor,
    *,
    as_of: date | None = None,
    now: datetime | None = None,
) -> bool:
    """Evaluate availability without requiring a scheduled restoration job."""
    today = as_of or date.today()
    if is_availability_pause_active(donor, now=now):
        return False
    if donor.deferred_until and donor.deferred_until > today:
        return False
    if donor.status == DEFERRED:
        return donor.deferred_until is not None and donor.deferred_until <= today
    return donor.status == AVAILABLE


def restore_expired_deferrals(
    database_session: Session,
    *,
    as_of: date | None = None,
    commit: bool = True,
) -> int:
    """Persist automatic restoration for every elapsed time-bound deferral."""
    today = as_of or date.today()
    result = database_session.execute(
        update(Donor)
        .where(
            Donor.status == DEFERRED,
            Donor.deferred_until.is_not(None),
            Donor.deferred_until <= today,
        )
        .values(status=AVAILABLE)
        .execution_options(synchronize_session="fetch")
    )
    restored = int(result.rowcount or 0)
    if restored and commit:
        database_session.commit()
    return restored


def restore_donor_if_due(
    database_session: Session,
    donor: Donor,
    *,
    as_of: date | None = None,
    commit: bool = True,
) -> bool:
    """Restore one elapsed deferral and report whether the row changed."""
    today = as_of or date.today()
    if donor.status != DEFERRED or not donor.deferred_until or donor.deferred_until > today:
        return False
    donor.status = AVAILABLE
    if commit:
        database_session.commit()
        database_session.refresh(donor)
    return True


def eligibility_message(
    donor: Donor,
    *,
    database_session: Session | None = None,
    as_of: date | None = None,
) -> str:
    """Return a donor-friendly operational status message."""
    if is_availability_pause_active(donor):
        return (
            "You paused matching until "
            f"{donor.availability_paused_until.isoformat()}. You can resume early from your dashboard."
        )
    if is_active_deferral(donor, as_of=as_of):
        reason = donor.deferral_reason or "Temporary donor deferral"
        return f"Deferred until {donor.deferred_until.isoformat()}: {reason}. Final eligibility is confirmed by the blood bank."
    if donor.status == UNAVAILABLE:
        return "You are currently marked unavailable. Contact the BloodLink administrator when this changes."
    if database_session is not None:
        evaluation = evaluate_donor(database_session, donor, as_of=as_of)
        if evaluation.policy_mode == ENFORCED and not evaluation.match_allowed:
            return "Your donor profile needs blood-bank review before automated matching. Final eligibility is confirmed by the blood bank."
        if evaluation.reasons or evaluation.warnings:
            return "Your donor profile has screening items for blood-bank review. Final eligibility is confirmed by the blood bank."
    return "Available for matching. Final eligibility must still be confirmed by the hospital or blood bank."
