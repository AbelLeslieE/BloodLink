"""Create, inspect, and revoke independently tracked login sessions."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import uuid4

from fastapi import Request
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from backend.config.settings import get_settings
from backend.database.models import User, UserSession


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def as_utc(value: datetime) -> datetime:
    return value if value.tzinfo else value.replace(tzinfo=timezone.utc)


def request_identity(request: Request) -> tuple[str | None, str | None]:
    forwarded = request.headers.get("x-forwarded-for", "").split(",", 1)[0].strip()
    ip_address = forwarded or (request.client.host if request.client else None)
    return (
        ip_address[:64] if ip_address else None,
        request.headers.get("user-agent", "")[:500] or None,
    )


def create_session(database_session: Session, user: User, request: Request, *, mfa_verified: bool) -> UserSession:
    ip_address, user_agent = request_identity(request)
    now = utcnow()
    session = UserSession(
        id=str(uuid4()),
        user_id=user.id,
        created_at=now,
        last_seen_at=now,
        expires_at=now + timedelta(minutes=get_settings().access_token_expire_minutes),
        ip_address=ip_address,
        user_agent=user_agent,
        mfa_verified=mfa_verified,
    )
    database_session.add(session)
    database_session.flush()
    return session


def active_session(database_session: Session, session_id: str, user_id: int) -> UserSession | None:
    session = database_session.scalar(
        select(UserSession).where(UserSession.id == session_id, UserSession.user_id == user_id)
    )
    if session is None or session.revoked_at is not None or as_utc(session.expires_at) <= utcnow():
        return None
    return session


def revoke_session(database_session: Session, session: UserSession) -> None:
    if session.revoked_at is None:
        session.revoked_at = utcnow()


def revoke_all_sessions(database_session: Session, user_id: int, *, except_session_id: str | None = None) -> int:
    statement = update(UserSession).where(
        UserSession.user_id == user_id,
        UserSession.revoked_at.is_(None),
    )
    if except_session_id:
        statement = statement.where(UserSession.id != except_session_id)
    result = database_session.execute(statement.values(revoked_at=utcnow()))
    return int(result.rowcount or 0)


def describe_user_agent(value: str | None) -> str:
    text = (value or "").lower()
    browser = next((name for key, name in (("edg/", "Edge"), ("chrome/", "Chrome"), ("firefox/", "Firefox"), ("safari/", "Safari")) if key in text), "Unknown browser")
    system = next((name for key, name in (("windows", "Windows"), ("android", "Android"), ("iphone", "iPhone"), ("ipad", "iPad"), ("mac os", "macOS"), ("linux", "Linux")) if key in text), "Unknown device")
    return f"{browser} on {system}"
