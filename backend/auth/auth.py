"""Authentication service functions for NSS volunteer accounts."""

from __future__ import annotations

from sqlalchemy.orm import Session

from backend.auth.security import verify_password, hash_password, password_context

_DUMMY_HASH = hash_password("timing-only-not-a-real-account")
from backend.database import crud
from backend.database.models import User


def authenticate_volunteer(
    database_session: Session,
    username: str,
    password: str,
) -> User | None:
    """Return an active volunteer when the supplied credentials are valid."""
    if len(username) > 100 or len(password) > 1024:
        return None
    user = crud.get_user_by_username(database_session, username)
    valid = verify_password(password, user.password_hash if user else _DUMMY_HASH)
    if user is None or not user.active or not valid:
        return None
    if password_context.needs_update(user.password_hash):
        user.password_hash = hash_password(password)

    return user
