"""Authentication API endpoints for NSS volunteers."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
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
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    database_session: Annotated[Session, Depends(get_db)],
) -> TokenResponse:
    """Authenticate an NSS volunteer and return an expiring JWT access token."""
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
    return TokenResponse(
        access_token=create_access_token(volunteer.username),
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
    _: Annotated[User, Depends(require_authentication)],
) -> LogoutResponse:
    """Provide the logout API contract until server-side revocation is added."""
    # TODO: Add JWT revocation when a token blacklist or rotation strategy exists.
    return LogoutResponse(
        detail="Token revocation is not implemented; remove the token on the client."
    )
