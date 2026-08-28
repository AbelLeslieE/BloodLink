"""Public QR-linked donor registration and protected QR generation APIs."""

from __future__ import annotations

from io import BytesIO
import re
from typing import Annotated

import qrcode
from fastapi import APIRouter, Depends, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, EmailStr, Field, field_validator
from sqlalchemy.orm import Session

from backend.auth.dependencies import require_administrator
from backend.config.settings import get_settings
from backend.database.database import get_db
from backend.database.models import User
from backend.services.donor_account_service import create_donor_account


router = APIRouter(prefix="/api/donor-registration", tags=["donor registration"])


ALLOWED_BLOOD_GROUPS = {"A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"}
ALLOWED_GENDERS = {"Female", "Male", "Non-binary", "Other", "Not Specified"}
USERNAME_PATTERN = re.compile(r"^[A-Za-z0-9._-]+$")


class DonorRegistration(BaseModel):
    full_name: str = Field(max_length=200)
    email: EmailStr
    phone: str = Field(max_length=30)
    username: str = Field(max_length=100)
    password: str = Field(max_length=128)
    blood_group: str = Field(max_length=5)
    department: str | None = Field(default=None, max_length=150)
    gender: str | None = Field(default=None, max_length=20)

    @field_validator("full_name")
    @classmethod
    def validate_full_name(cls, value: str) -> str:
        clean_value = " ".join(value.split())
        if len(clean_value) < 2:
            raise ValueError("Enter your full name using at least 2 characters.")
        if not any(character.isalpha() for character in clean_value):
            raise ValueError("Full name must contain letters.")
        if any(
            not (character.isalpha() or character in " .'-")
            for character in clean_value
        ):
            raise ValueError(
                "Full name can use letters, spaces, apostrophes, hyphens, and periods only."
            )
        return clean_value

    @field_validator("email")
    @classmethod
    def normalise_email(cls, value: EmailStr) -> str:
        return str(value).strip().lower()

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, value: str) -> str:
        clean_value = value.strip()
        if not clean_value:
            raise ValueError("Enter a phone number.")
        return clean_value

    @field_validator("username")
    @classmethod
    def validate_username(cls, value: str) -> str:
        if value != value.strip():
            raise ValueError("Username cannot start or end with a space.")
        if len(value) < 3:
            raise ValueError("Username must contain at least 3 characters.")
        if any(character.isspace() for character in value):
            raise ValueError("Username cannot contain spaces.")
        if not USERNAME_PATTERN.fullmatch(value):
            raise ValueError(
                "Username can use letters, numbers, periods, underscores, and hyphens only."
            )
        return value.lower()

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        if len(value) < 8:
            raise ValueError("Password must contain at least 8 characters.")
        if value != value.strip():
            raise ValueError("Password cannot start or end with a space.")
        if not any(character.isalpha() for character in value):
            raise ValueError("Password must include at least one letter.")
        if not any(character.isdigit() for character in value):
            raise ValueError("Password must include at least one number.")
        return value

    @field_validator("blood_group")
    @classmethod
    def validate_blood_group(cls, value: str) -> str:
        clean_value = value.strip().upper().replace(" ", "")
        if clean_value not in ALLOWED_BLOOD_GROUPS:
            raise ValueError("Select a valid blood group.")
        return clean_value

    @field_validator("department")
    @classmethod
    def normalise_department(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return " ".join(value.split()) or None

    @field_validator("gender")
    @classmethod
    def validate_gender(cls, value: str | None) -> str | None:
        if value is None or not value.strip():
            return None
        clean_value = value.strip()
        if clean_value not in ALLOWED_GENDERS:
            raise ValueError("Select a valid gender option.")
        return clean_value


def _create_account(db: Session, data: DonorRegistration) -> dict:
    donor, account = create_donor_account(db, **data.model_dump())
    return {"success": True, "message": "Your donor account has been created. You can now sign in.",
            "donor": {"id": donor.id, "donor_code": donor.donor_code},
            "user": {"id": account.id, "username": account.username}}


@router.post("", status_code=status.HTTP_201_CREATED)
def register_donor(data: DonorRegistration, db: Annotated[Session, Depends(get_db)]) -> dict:
    """Public endpoint opened by the registration QR code."""
    return _create_account(db, data)


@router.post("/admin", status_code=status.HTTP_201_CREATED)
def administrator_register_donor(
    data: DonorRegistration, db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(require_administrator)],
) -> dict:
    """Let an administrator create a fully linked donor portal account."""
    return _create_account(db, data)


@router.get("/qr")
def registration_qr(_: Annotated[User, Depends(require_administrator)]) -> StreamingResponse:
    """Return a printable QR code that opens the public registration page."""
    registration_url = f"{get_settings().backend_url.rstrip('/')}/donor-register"
    image = qrcode.make(registration_url)
    data = BytesIO()
    image.save(data, format="PNG")
    data.seek(0)
    return StreamingResponse(data, media_type="image/png", headers={"Content-Disposition": "inline; filename=BloodLink-donor-registration-qr.png"})
