"""Authentication API endpoints for NSS volunteers."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from backend.config.settings import get_settings
from backend.security.rate_limit import consume_limit
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from backend.auth.auth import authenticate_volunteer
from backend.auth.dependencies import require_authentication
from backend.auth.security import create_access_token
from backend.auth.token import LogoutResponse, TokenResponse
from backend.database import crud
from backend.database.database import get_db
from backend.database.models import User
from backend.database.schemas import UserResponse


router = APIRouter(prefix="/api/auth", tags=["authentication"])


@router.post("/login", response_model=TokenResponse)
def login(
    request: Request,
    response: Response,
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    database_session: Annotated[Session, Depends(get_db)],
) -> TokenResponse:
    """Authenticate an NSS volunteer and return an expiring JWT access token."""
    if not consume_limit(form_data.username.strip().lower(), "login-account", 10, 900):
        raise HTTPException(status_code=429, detail="Too many attempts. Please try again later.", headers={"Retry-After": "900"})
    volunteer = authenticate_volunteer(
        database_session,
        form_data.username,
        form_data.password,
    )
    if volunteer is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

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
