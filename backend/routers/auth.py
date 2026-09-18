"""Authentication API endpoints for NSS volunteers."""

from __future__ import annotations

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.orm import Session

from backend.auth.auth import authenticate_volunteer
from backend.auth.dependencies import require_authentication
from backend.auth.security import create_access_token, hash_password, validate_password_strength, verify_password
from backend.auth.token import LogoutResponse, TokenResponse
from backend.config.settings import get_settings
from backend.database import crud
from backend.database.database import get_db
from backend.database.models import User
from backend.database.schemas import UserResponse
from backend.security.rate_limit import clear_limit, client_address, consume_limit


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/auth", tags=["authentication"])

LOGIN_FAILURE_LIMIT, LOGIN_FAILURE_WINDOW = 5, 900
ACCOUNT_WATCH_LIMIT, ACCOUNT_WATCH_WINDOW = 50, 3600


class PasswordChange(BaseModel):
    current_password: str = Field(min_length=1, max_length=1024)
    new_password: str = Field(max_length=128)

    @field_validator("new_password")
    @classmethod
    def check_strength(cls, value: str) -> str:
        return validate_password_strength(value)


def _too_many_attempts() -> HTTPException:
    return HTTPException(status_code=429, detail="Too many attempts. Please try again later.", headers={"Retry-After": "900"})


@router.post("/login", response_model=TokenResponse)
def login(
    request: Request,
    response: Response,
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    database_session: Annotated[Session, Depends(get_db)],
) -> TokenResponse:
    """Authenticate an NSS volunteer and return an expiring JWT access token."""
    username = form_data.username.strip().lower()
    # Failures are counted per client and account together: a stranger can only
    # exhaust attempts for pairs they occupy, never lock the real holder out.
    identity = f"{client_address(request)}|{username}"
    if not consume_limit(identity, "login-failures", LOGIN_FAILURE_LIMIT, LOGIN_FAILURE_WINDOW):
        raise _too_many_attempts()
    volunteer = authenticate_volunteer(
        database_session,
        form_data.username,
        form_data.password,
    )
    if volunteer is None:
        if not consume_limit(username, "login-account-watch", ACCOUNT_WATCH_LIMIT, ACCOUNT_WATCH_WINDOW):
            logger.warning("Sustained failed sign-in attempts against one account from multiple clients.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    clear_limit(identity, "login-failures")

    crud.update_user_last_login(database_session, volunteer)
    token = create_access_token(volunteer.username, volunteer.auth_version)
    if request.headers.get("x-session-mode") == "cookie":
        settings = get_settings()
        response.set_cookie("bloodlink_session", token, httponly=True,
                            secure=settings.production or request.url.scheme == "https",
                            samesite="strict", path="/",
                            max_age=settings.access_token_expire_minutes * 60)
        # A non-secret marker preserves the existing frontend API contract.
        token = "cookie-session"
    return TokenResponse(
        access_token=token,
        volunteer_name=volunteer.full_name,
    )


@router.get("/me", response_model=UserResponse)
def get_current_volunteer(
    current_user: Annotated[User, Depends(require_authentication)],
) -> User:
    """Return the authenticated volunteer without exposing password data."""
    return current_user


@router.post("/change-password")
def change_password(
    data: PasswordChange,
    response: Response,
    current_user: Annotated[User, Depends(require_authentication)],
    database_session: Annotated[Session, Depends(get_db)],
) -> dict[str, str]:
    """Replace the caller's password after proving the current one; revokes every session."""
    if not consume_limit(str(current_user.id), "change-password", 5, 900):
        raise _too_many_attempts()
    if not verify_password(data.current_password, current_user.password_hash):
        raise HTTPException(status_code=400, detail="The current password is incorrect.")
    if data.new_password == data.current_password:
        raise HTTPException(status_code=400, detail="Choose a password that differs from the current one.")
    current_user.password_hash = hash_password(data.new_password)
    current_user.auth_version += 1
    database_session.commit()
    response.delete_cookie("bloodlink_session", path="/", samesite="strict")
    return {"detail": "Password updated. Sign in again with your new password."}


@router.post("/logout", response_model=LogoutResponse)
def logout(
    response: Response,
    current_user: Annotated[User, Depends(require_authentication)],
    database_session: Annotated[Session, Depends(get_db)],
) -> LogoutResponse:
    """Invalidate active tokens for the authenticated account."""
    response.delete_cookie("bloodlink_session", path="/", samesite="strict")
    current_user.auth_version += 1
    database_session.commit()
    return LogoutResponse(
        detail="Signed out successfully."
    )
