"""Reusable FastAPI dependencies for protecting authenticated endpoints."""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from sqlalchemy.orm import Session

from backend.auth.security import get_token_subject
from backend.database import crud
from backend.database.database import get_db
from backend.database.models import User


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def _authentication_exception() -> HTTPException:
    """Create the standard response for missing or invalid bearer tokens."""
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate authentication credentials.",
        headers={"WWW-Authenticate": "Bearer"},
    )


def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    database_session: Annotated[Session, Depends(get_db)],
) -> User:
    """Resolve the active volunteer represented by a valid JWT."""
    try:
        username = get_token_subject(token)
    except JWTError as error:
        raise _authentication_exception() from error

    user = crud.get_user_by_username(database_session, username)
    if user is None or not user.active:
        raise _authentication_exception()

    return user


def require_authentication(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """Reusable dependency that protects future volunteer-only endpoints."""
    return current_user
