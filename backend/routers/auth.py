"""Authentication API endpoints for NSS volunteers."""

from __future__ import annotations

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, Form, HTTPException, status, Request, Response
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
from backend.services.audit_service import record_audit_event
from backend.services.mfa_service import verify_user_code
from backend.services.session_service import create_session, revoke_all_sessions


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
    mfa_code: Annotated[str | None, Form(max_length=64)] = None,
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
        record_audit_event(
            database_session,
            category="AUTHENTICATION",
            action="LOGIN",
            result="FAILED",
            actor_username=username,
            request=request,
            details={"reason": "invalid_credentials"},
        )
        database_session.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    clear_limit(identity, "login-failures")

    mfa_verified = False
    if volunteer.mfa_enabled:
        if not mfa_code:
            record_audit_event(
                database_session,
                category="AUTHENTICATION",
                action="LOGIN_MFA_CHALLENGE",
                result="PENDING",
                actor=volunteer,
                request=request,
            )
            database_session.commit()
            raise HTTPException(
                status_code=428,
                detail={"code": "MFA_REQUIRED", "message": "Enter your authenticator or recovery code."},
            )
        if not consume_limit(identity, "login-mfa", 8, LOGIN_FAILURE_WINDOW) or not verify_user_code(volunteer, mfa_code):
            record_audit_event(
                database_session,
                category="AUTHENTICATION",
                action="LOGIN_MFA",
                result="FAILED",
                actor=volunteer,
                request=request,
                details={"reason": "invalid_code"},
            )
            database_session.commit()
            raise HTTPException(status_code=401, detail="The verification code is invalid or has already been used.")
        clear_limit(identity, "login-mfa")
        mfa_verified = True

    crud.update_user_last_login(database_session, volunteer)
    tracked_session = create_session(
        database_session, volunteer, request, mfa_verified=mfa_verified
    )
    record_audit_event(
        database_session,
        category="AUTHENTICATION",
        action="LOGIN",
        actor=volunteer,
        target_type="session",
        target_id=tracked_session.id,
        request=request,
        details={"mfa_verified": mfa_verified},
    )
    database_session.commit()
    token = create_access_token(
        volunteer.username,
        volunteer.auth_version,
        session_id=tracked_session.id,
        mfa_verified=mfa_verified,
    )
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
    request: Request,
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
    revoked_count = revoke_all_sessions(database_session, current_user.id)
    record_audit_event(
        database_session,
        category="SECURITY",
        action="PASSWORD_CHANGED",
        actor=current_user,
        target_type="user",
        target_id=current_user.id,
        request=request,
        details={"sessions_revoked": revoked_count},
    )
    database_session.commit()
    response.delete_cookie("bloodlink_session", path="/", samesite="strict")
    return {"detail": "Password updated. Sign in again with your new password."}


@router.post("/logout", response_model=LogoutResponse)
def logout(
    request: Request,
    response: Response,
    current_user: Annotated[User, Depends(require_authentication)],
    database_session: Annotated[Session, Depends(get_db)],
) -> LogoutResponse:
    """Invalidate active tokens for the authenticated account."""
    response.delete_cookie("bloodlink_session", path="/", samesite="strict")
    # Preserve BloodLink's established high-security logout behavior: the
    # normal logout action closes every session. The Technical Portal exposes
    # independent revocation when an administrator wants to close only one.
    revoked_count = revoke_all_sessions(database_session, current_user.id)
    current_user.auth_version += 1
    target_id = getattr(request.state, "session_id", None) or "legacy-all"
    record_audit_event(
        database_session,
        category="AUTHENTICATION",
        action="LOGOUT",
        actor=current_user,
        target_type="session",
        target_id=target_id,
        request=request,
        details={"sessions_revoked": revoked_count, "scope": "all"},
    )
    database_session.commit()
    return LogoutResponse(
        detail="Signed out successfully."
    )
