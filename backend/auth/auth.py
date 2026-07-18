"""Authentication service functions for NSS volunteer accounts."""

from __future__ import annotations

from sqlalchemy.orm import Session

from backend.auth.security import verify_password
from backend.database import crud
from backend.database.models import User


def authenticate_volunteer(
    database_session: Session,
    username: str,
    password: str,
) -> User | None:
    """Return an active volunteer when the supplied credentials are valid."""
    user = crud.get_user_by_username(database_session, username)
    if user is None or not user.active:
        return None

    if not verify_password(password, user.password_hash):
        return None

    return user
