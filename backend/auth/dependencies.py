"""Reusable FastAPI dependencies for protecting authenticated endpoints."""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends, HTTPException, status, Request
from backend.config.settings import get_settings
from fastapi.security import OAuth2PasswordBearer
from jwt import InvalidTokenError as JWTError
from sqlalchemy.orm import Session

from backend.auth.security import get_token_auth_version, get_token_subject
from backend.database import crud
from backend.database.database import get_db
from backend.database.models import User


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)


def _authentication_exception() -> HTTPException:
    """Create the standard response for missing or invalid bearer tokens."""
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate authentication credentials.",
        headers={"WWW-Authenticate": "Bearer"},
    )


def get_current_user(
    request: Request,
    token: Annotated[str | None, Depends(oauth2_scheme)],
    database_session: Annotated[Session, Depends(get_db)],
) -> User:
    """Resolve the active volunteer represented by a valid JWT."""
    if token is None or token == "cookie-session":
        token = request.cookies.get("bloodlink_session")
        if token and request.method not in {"GET", "HEAD", "OPTIONS"}:
            settings = get_settings()
            origin = request.base_url.replace(scheme="https") if settings.production else request.base_url
            allowed = {str(origin).rstrip("/"), settings.frontend_url.rstrip("/")}
            if request.headers.get("origin") not in allowed:
                raise HTTPException(status_code=403, detail="A same-origin request is required.")
    if not token:
        raise _authentication_exception()
    try:
        username = get_token_subject(token)
        token_auth_version = get_token_auth_version(token)
    except JWTError as error:
        raise _authentication_exception() from error

    user = crud.get_user_by_username(database_session, username)
    if user is None or not user.active or user.auth_version != token_auth_version:
        raise _authentication_exception()

    return user


def require_authentication(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """Reusable dependency that protects future volunteer-only endpoints."""
    return current_user


def require_administrator(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """Require a server-side administrator role for administrative actions."""
    if current_user.role.strip().lower() not in {"administrator", "admin"}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrator permission is required.",
        )
    return current_user


def require_donor(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """Require an account intended for the donor-facing portal."""
    if current_user.role.strip().lower() not in {"donor", "nss volunteer"}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="A donor account is required.",
        )
    return current_user
