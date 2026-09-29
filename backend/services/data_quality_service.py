"""Read-only donor data-quality analysis for administrator remediation queues."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import re

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.database.models import Donor


EMAIL_PATTERN = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
SEVERITY_ORDER = {"HIGH": 0, "REVIEW": 1, "INFO": 2}


@dataclass(frozen=True)
class DataQualityIssue:
    code: str
    category: str
    severity: str
    message: str


@dataclass(frozen=True)
class DonorQualityResult:
    donor: Donor
    completeness_percent: int
    issues: tuple[DataQualityIssue, ...]

    @property
    def highest_severity(self) -> str:
        if not self.issues:
            return "COMPLETE"
        return min(self.issues, key=lambda issue: SEVERITY_ORDER[issue.severity]).severity


def normalize_email(value: str | None) -> str | None:
    normalized = (value or "").strip().lower()
    return normalized or None


def normalize_phone(value: str | None) -> str | None:
    digits = "".join(character for character in (value or "") if character.isdigit())
    if not digits:
        return None
    # Indian records commonly mix local 10-digit numbers with +91 notation.
    # Use the final 10 digits only for duplicate suggestions, never auto-merge.
    return digits[-10:] if len(digits) >= 10 else digits


def normalize_name(value: str | None) -> str:
    return " ".join(re.findall(r"[a-z0-9]+", (value or "").lower()))


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _duplicate_indexes(donors: list[Donor]) -> dict[int, set[str]]:
    email_groups: dict[str, list[int]] = defaultdict(list)
    phone_groups: dict[str, list[int]] = defaultdict(list)
    identity_groups: dict[tuple[str, object], list[int]] = defaultdict(list)
    for donor in donors:
        email = normalize_email(donor.email)
        phone = normalize_phone(donor.phone)
        if email:
            email_groups[email].append(donor.id)
        if phone and len(phone) == 10:
            phone_groups[phone].append(donor.id)
        if donor.date_of_birth and normalize_name(donor.full_name):
            identity_groups[(normalize_name(donor.full_name), donor.date_of_birth)].append(donor.id)

    duplicate_reasons: dict[int, set[str]] = defaultdict(set)
    for label, groups in (
        ("email address", email_groups),
        ("phone number", phone_groups),
        ("name and date of birth", identity_groups),
    ):
        for donor_ids in groups.values():
            if len(donor_ids) < 2:
                continue
            for donor_id in donor_ids:
                duplicate_reasons[donor_id].add(label)
    return duplicate_reasons


def _completeness_percent(donor: Donor) -> int:
    checks = (
        bool((donor.full_name or "").strip()),
        bool((donor.blood_group or "").strip()),
        bool(normalize_email(donor.email) or normalize_phone(donor.phone)),
        donor.date_of_birth is not None,
        bool((donor.gender or "").strip()),
        donor.weight is not None,
        (donor.hb_above_12_5 or "").strip().lower() in {"yes", "no"},
        (donor.bp_normal or "").strip().lower() in {"yes", "no"},
        (donor.regular_medication or "").strip().lower() in {"yes", "no"},
        bool((donor.district or "").strip() or (donor.city or "").strip()),
    )
    return round(sum(checks) * 100 / len(checks))


def analyze_donors(
    database_session: Session,
    *,
    stale_after_days: int = 365,
    now: datetime | None = None,
) -> list[DonorQualityResult]:
    """Build a deterministic, non-destructive cleanup queue for every donor."""
    donors = list(database_session.scalars(select(Donor).order_by(Donor.id)).all())
    duplicates = _duplicate_indexes(donors)
    cutoff = (now or datetime.now(timezone.utc)) - timedelta(days=stale_after_days)
    results: list[DonorQualityResult] = []

    for donor in donors:
        issues: list[DataQualityIssue] = []
        missing_screening: list[str] = []
        if donor.date_of_birth is None:
            missing_screening.append("date of birth")
        if not (donor.gender or "").strip():
            missing_screening.append("gender")
        if donor.weight is None:
            missing_screening.append("weight")
        if (donor.hb_above_12_5 or "").strip().lower() not in {"yes", "no"}:
            missing_screening.append("haemoglobin")
        if (donor.bp_normal or "").strip().lower() not in {"yes", "no"}:
            missing_screening.append("blood pressure")
        if (donor.regular_medication or "").strip().lower() not in {"yes", "no"}:
            missing_screening.append("medication")
        if missing_screening:
            issues.append(DataQualityIssue(
                code="INCOMPLETE_ELIGIBILITY",
                category="ELIGIBILITY",
                severity="REVIEW",
                message="Missing screening data: " + ", ".join(missing_screening) + ".",
            ))

        email = normalize_email(donor.email)
        phone_digits = "".join(character for character in (donor.phone or "") if character.isdigit())
        if not email and not phone_digits:
            issues.append(DataQualityIssue(
                code="NO_CONTACT",
                category="CONTACT",
                severity="HIGH",
                message="No email address or phone number is recorded.",
            ))
        else:
            invalid: list[str] = []
            if email and not EMAIL_PATTERN.fullmatch(email):
                invalid.append("email address")
            if phone_digits and not 10 <= len(phone_digits) <= 15:
                invalid.append("phone number")
            if invalid:
                issues.append(DataQualityIssue(
                    code="INVALID_CONTACT",
                    category="CONTACT",
                    severity="HIGH",
                    message="Check the recorded " + " and ".join(invalid) + ".",
                ))

        if donor.id in duplicates:
            issues.append(DataQualityIssue(
                code="POSSIBLE_DUPLICATE",
                category="DUPLICATE",
                severity="HIGH",
                message="Possible duplicate based on " + ", ".join(sorted(duplicates[donor.id])) + ". Review manually; records were not merged.",
            ))

        if not (donor.district or "").strip() and not (donor.city or "").strip():
            issues.append(DataQualityIssue(
                code="MISSING_LOCATION",
                category="LOCATION",
                severity="REVIEW",
                message="District and city are not recorded.",
            ))

        if donor.updated_at and _as_utc(donor.updated_at) <= cutoff:
            issues.append(DataQualityIssue(
                code="STALE_PROFILE",
                category="STALE",
                severity="INFO",
                message=f"Profile has not been updated in at least {stale_after_days} days.",
            ))

        issues.sort(key=lambda issue: (SEVERITY_ORDER[issue.severity], issue.code))
        results.append(DonorQualityResult(
            donor=donor,
            completeness_percent=_completeness_percent(donor),
            issues=tuple(issues),
        ))

    results.sort(key=lambda item: (
        SEVERITY_ORDER.get(item.highest_severity, 3),
        item.completeness_percent,
        item.donor.full_name.lower(),
        item.donor.id,
    ))
    return results


def quality_summary(results: list[DonorQualityResult]) -> dict[str, int]:
    def has_code(item: DonorQualityResult, code: str) -> bool:
        return any(issue.code == code for issue in item.issues)

    return {
        "total_donors": len(results),
        "donors_with_issues": sum(bool(item.issues) for item in results),
        "complete_profiles": sum(not item.issues for item in results),
        "high_priority": sum(item.highest_severity == "HIGH" for item in results),
        "incomplete_eligibility": sum(has_code(item, "INCOMPLETE_ELIGIBILITY") for item in results),
        "possible_duplicates": sum(has_code(item, "POSSIBLE_DUPLICATE") for item in results),
        "invalid_or_missing_contact": sum(
            has_code(item, "INVALID_CONTACT") or has_code(item, "NO_CONTACT")
            for item in results
        ),
        "stale_profiles": sum(has_code(item, "STALE_PROFILE") for item in results),
    }
