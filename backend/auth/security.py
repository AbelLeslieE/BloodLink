"""Password hashing and JSON Web Token helpers."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt
from passlib.context import CryptContext

from backend.config.settings import get_settings


password_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Create a bcrypt hash without retaining the plain-text password."""
    return password_context.hash(password)


def verify_password(plain_password: str, password_hash: str) -> bool:
    """Safely compare a plain-text password with its stored bcrypt hash."""
    try:
        return password_context.verify(plain_password, password_hash)
    except (TypeError, ValueError):
        return False


def create_access_token(subject: str) -> str:
    """Create a time-limited access token for an authenticated volunteer."""
    settings = get_settings()
    expires_at = datetime.now(timezone.utc) + timedelta(
        minutes=settings.access_token_expire_minutes
    )
    payload = {"sub": subject, "exp": expires_at}
    return jwt.encode(
        payload,
        settings.secret_key,
        algorithm=settings.jwt_algorithm,
    )


def get_token_subject(token: str) -> str:
    """Decode a token and return its subject or raise a JWT validation error."""
    settings = get_settings()
    payload = jwt.decode(
        token,
        settings.secret_key,
        algorithms=[settings.jwt_algorithm],
    )
    subject = payload.get("sub")
    if not isinstance(subject, str) or not subject:
        raise JWTError("Token subject is missing.")
    return subject
