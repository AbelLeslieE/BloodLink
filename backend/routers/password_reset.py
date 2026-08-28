"""Public, email-based password recovery for donor portal accounts."""

from __future__ import annotations

import logging
from html import escape
from typing import Annotated
from urllib.parse import quote

from fastapi import APIRouter, Depends, HTTPException, status
from jose import JWTError
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.auth.security import (
    create_password_reset_token,
    get_password_reset_data,
    hash_password,
)
from backend.config.settings import get_settings
from backend.database.database import get_db
from backend.database.models import User
from backend.services.email_service import send_email


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/auth/password-reset", tags=["password recovery"])

GENERIC_REQUEST_MESSAGE = (
    "If a donor account uses this email address, a password reset link has been sent."
)


class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordResetConfirmation(BaseModel):
    token: str = Field(min_length=20, max_length=4096)
    new_password: str = Field(min_length=8, max_length=128)


def _is_donor_account(user: User) -> bool:
    return user.role.strip().lower() == "donor"


def _build_reset_email(reset_url: str, full_name: str) -> str:
    safe_url = escape(reset_url, quote=True)
    safe_name = escape(full_name)
    return f"""
    <!doctype html>
    <html><body style="margin:0;padding:32px;background:#f4f7fc;font-family:Arial,sans-serif;color:#17213b;">
      <main style="max-width:560px;margin:auto;padding:32px;background:#fff;border-radius:16px;">
        <h1 style="margin:0 0 16px;font-size:24px;">Reset your BloodLink password</h1>
        <p>Hello {safe_name},</p>
        <p>Use the button below to choose a new donor portal password. This link expires in 30 minutes and can be used once.</p>
        <p style="margin:28px 0;"><a href="{safe_url}" style="display:inline-block;padding:12px 18px;border-radius:8px;background:#c91d3f;color:#fff;text-decoration:none;font-weight:700;">Reset password</a></p>
        <p style="color:#66748a;font-size:13px;line-height:1.5;">If you did not request this, you can safely ignore this email. Your password will not change.</p>
      </main>
    </body></html>
    """


@router.post("/request", status_code=status.HTTP_202_ACCEPTED)
def request_password_reset(
    data: PasswordResetRequest,
    database_session: Annotated[Session, Depends(get_db)],
) -> dict[str, str]:
    """Email a recovery link without exposing whether an account exists."""
    email = str(data.email).strip().lower()
    user = database_session.scalar(select(User).where(User.email == email))

    if user and user.active and _is_donor_account(user):
        settings = get_settings()
        token = create_password_reset_token(user.username, user.auth_version)
        reset_url = (
            f"{settings.frontend_url.rstrip('/')}/reset-password"
            f"?token={quote(token, safe='')}"
        )
        delivered = send_email(
            recipient_email=user.email,
            subject="Reset your BloodLink donor password",
            html_body=_build_reset_email(reset_url, user.full_name),
        )
        if not delivered:
            logger.error("Password reset email could not be delivered for donor account %s", user.id)

    return {"detail": GENERIC_REQUEST_MESSAGE}


@router.post("/confirm")
def confirm_password_reset(
    data: PasswordResetConfirmation,
    database_session: Annotated[Session, Depends(get_db)],
) -> dict[str, str]:
    """Set a new donor password and revoke all existing sessions."""
    if data.new_password.isspace():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Password cannot contain only spaces.",
        )

    try:
        username, token_auth_version = get_password_reset_data(data.token)
    except JWTError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This password reset link is invalid or has expired. Request a new one.",
        ) from error

    user = database_session.scalar(select(User).where(User.username == username))
    if (
        user is None
        or not user.active
        or not _is_donor_account(user)
        or user.auth_version != token_auth_version
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This password reset link is invalid or has expired. Request a new one.",
        )

    user.password_hash = hash_password(data.new_password)
    user.auth_version += 1
    database_session.commit()
    return {"detail": "Password updated. You can now sign in with your new password."}
