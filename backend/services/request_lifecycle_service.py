"""Automatic escalation and expiry for blood requests."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.config.settings import get_settings
from backend.database.models import BloodRequest


OPEN_REQUEST_STATUSES = frozenset({
    "Pending",
    "Open",
    "Sent",
    "In Progress",
    "Donor Responded",
    "Awaiting Donation",
    "Partially Fulfilled",
})
TERMINAL_REQUEST_STATUSES = frozenset({"Fulfilled", "Closed", "Cancelled", "Expired"})
CLOSURE_REQUEST_STATUSES = frozenset({"Closed", "Cancelled", "Expired"})


@dataclass(frozen=True)
class LifecycleRefreshResult:
    evaluated: int
    initialized: int
    escalated: int
    expired: int


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def request_deadline(required_date: date) -> datetime:
    """Return midnight after the required day in the configured timezone."""

    local_timezone = ZoneInfo(get_settings().request_timezone)
    return datetime.combine(
        required_date + timedelta(days=1),
        time.min,
        tzinfo=local_timezone,
    ).astimezone(timezone.utc)


def local_today() -> date:
    """Return today's date in the deployment's request timezone."""

    return datetime.now(ZoneInfo(get_settings().request_timezone)).date()


def deadline_has_passed(
    request: BloodRequest,
    *,
    now: datetime | None = None,
) -> bool:
    deadline = request.expires_at or request_deadline(request.required_date)
    return _as_utc(now or datetime.now(timezone.utc)) >= _as_utc(deadline)


def _target_escalation(request: BloodRequest, now: datetime) -> tuple[int, str | None]:
    deadline = _as_utc(request.expires_at or request_deadline(request.required_date))
    remaining_seconds = (deadline - now).total_seconds()
    priority = (request.priority or "").strip().casefold()

    candidates: list[tuple[int, str]] = []
    if priority == "emergency":
        candidates.append((3, "Emergency-priority request"))
    elif priority == "urgent":
        candidates.append((1, "Urgent-priority request"))

    if remaining_seconds <= 6 * 60 * 60:
        candidates.append((3, "Required within 6 hours"))
    elif remaining_seconds <= 24 * 60 * 60:
        candidates.append((2, "Required within 24 hours"))
    elif remaining_seconds <= 48 * 60 * 60:
        candidates.append((1, "Required within 48 hours"))

    return max(candidates, default=(0, None), key=lambda item: item[0])


def apply_request_lifecycle(
    request: BloodRequest,
    *,
    now: datetime | None = None,
) -> str | None:
    """Update one request in memory and return the transition that occurred."""

    current_time = _as_utc(now or datetime.now(timezone.utc))
    if request.expires_at is None:
        request.expires_at = request_deadline(request.required_date)

    if request.status not in OPEN_REQUEST_STATUSES:
        return None

    deadline = _as_utc(request.expires_at)
    if current_time >= deadline:
        request.status = "Expired"
        request.escalation_level = 3
        request.escalation_reason = "Required date passed"
        request.escalated_at = request.escalated_at or current_time
        request.closure_reason = (
            "Automatically expired after the required date passed with "
            f"{request.units_remaining} unit(s) still outstanding."
        )
        request.closed_at = current_time
        return "expired"

    target_level, target_reason = _target_escalation(request, current_time)
    if target_level > (request.escalation_level or 0):
        request.escalation_level = target_level
        request.escalation_reason = target_reason
        request.escalated_at = current_time
        return "escalated"

    return None


def refresh_request_lifecycles(
    database_session: Session,
    *,
    request_id: int | None = None,
    now: datetime | None = None,
) -> LifecycleRefreshResult:
    """Persist due lifecycle transitions and signed system audit records."""

    statement = select(BloodRequest).where(BloodRequest.status.in_(OPEN_REQUEST_STATUSES))
    if request_id is not None:
        statement = statement.where(BloodRequest.id == request_id)
    requests = list(database_session.scalars(statement).all())

    initialized = 0
    escalated = 0
    expired = 0
    for blood_request in requests:
        if blood_request.expires_at is None:
            initialized += 1
        previous_status = blood_request.status
        previous_level = blood_request.escalation_level
        transition = apply_request_lifecycle(blood_request, now=now)
        if transition is None:
            continue

        from backend.services.audit_service import record_audit_event

        if transition == "expired":
            expired += 1
            action = "REQUEST_AUTO_EXPIRED"
        else:
            escalated += 1
            action = "REQUEST_AUTO_ESCALATED"
        record_audit_event(
            database_session,
            category="REQUEST_LIFECYCLE",
            action=action,
            actor_username="system",
            target_type="blood_request",
            target_id=blood_request.id,
            details={
                "previous_status": previous_status,
                "new_status": blood_request.status,
                "previous_escalation_level": previous_level,
                "new_escalation_level": blood_request.escalation_level,
                "reason": blood_request.closure_reason or blood_request.escalation_reason,
            },
        )

    if initialized or escalated or expired:
        database_session.commit()

    return LifecycleRefreshResult(
        evaluated=len(requests),
        initialized=initialized,
        escalated=escalated,
        expired=expired,
    )
