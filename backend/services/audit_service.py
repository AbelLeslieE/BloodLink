"""Append-only security audit events with per-record integrity signatures."""

from __future__ import annotations

import hashlib
import hmac
import json
from datetime import datetime, timezone
from typing import Any

from fastapi import Request
from sqlalchemy.orm import Session

from backend.config.settings import get_settings
from backend.database.models import AuditLog, User


_SENSITIVE_KEYS = {
    "password", "current_password", "new_password", "secret", "token",
    "recovery_code", "recovery_codes", "authorization", "cookie",
}


def _safe_details(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            str(key): "[REDACTED]" if str(key).lower() in _SENSITIVE_KEYS else _safe_details(item)
            for key, item in value.items()
        }
    if isinstance(value, (list, tuple)):
        return [_safe_details(item) for item in value]
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    return str(value)


def _request_context(request: Request | None) -> tuple[str | None, str | None, str | None, str | None]:
    if request is None:
        return None, None, None, None
    forwarded = request.headers.get("x-forwarded-for", "").split(",", 1)[0].strip()
    ip_address = forwarded or (request.client.host if request.client else None)
    return (
        ip_address[:64] if ip_address else None,
        request.headers.get("user-agent", "")[:500] or None,
        request.method[:10],
        request.url.path[:500],
    )


def _signature_payload(event: AuditLog) -> bytes:
    created_at = event.created_at
    if created_at.tzinfo is None:
        created_at = created_at.replace(tzinfo=timezone.utc)
    payload = {
        "created_at": created_at.astimezone(timezone.utc).isoformat(),
        "actor_user_id": event.actor_user_id,
        "actor_username": event.actor_username,
        "category": event.category,
        "action": event.action,
        "result": event.result,
        "target_type": event.target_type,
        "target_id": event.target_id,
        "ip_address": event.ip_address,
        "user_agent": event.user_agent,
        "request_method": event.request_method,
        "request_path": event.request_path,
        "details_json": event.details_json,
    }
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()


def _sign(event: AuditLog) -> str:
    key = hashlib.sha256((get_settings().secret_key + ":audit:v1").encode()).digest()
    return hmac.new(key, _signature_payload(event), hashlib.sha256).hexdigest()


def record_audit_event(
    database_session: Session,
    *,
    category: str,
    action: str,
    result: str = "SUCCESS",
    actor: User | None = None,
    actor_username: str | None = None,
    target_type: str | None = None,
    target_id: str | int | None = None,
    request: Request | None = None,
    details: dict[str, Any] | None = None,
) -> AuditLog:
    """Add an audit event to the caller's transaction without committing it."""
    ip_address, user_agent, method, path = _request_context(request)
    event = AuditLog(
        created_at=datetime.now(timezone.utc),
        actor_user_id=actor.id if actor else None,
        actor_username=(actor.username if actor else actor_username) or None,
        category=category.strip().upper()[:50],
        action=action.strip().upper()[:120],
        result=result.strip().upper()[:30],
        target_type=target_type.strip()[:80] if target_type else None,
        target_id=str(target_id)[:120] if target_id is not None else None,
        ip_address=ip_address,
        user_agent=user_agent,
        request_method=method,
        request_path=path,
        details_json=json.dumps(_safe_details(details or {}), sort_keys=True, separators=(",", ":")),
        integrity_hash="",
    )
    event.integrity_hash = _sign(event)
    database_session.add(event)
    return event


def verify_audit_event(event: AuditLog) -> bool:
    """Return whether an audit row still matches its integrity signature."""
    return hmac.compare_digest(event.integrity_hash, _sign(event))
