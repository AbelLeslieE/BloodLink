"""QR donor registration: verified details, then one-time email password setup."""

from __future__ import annotations

from html import escape
from io import BytesIO
import re
from typing import Annotated
from urllib.parse import quote

import qrcode
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.auth.dependencies import require_administrator
from backend.config.settings import get_settings
from backend.database.database import get_db
from backend.database.models import User
from backend.services.donor_account_service import create_donor_account
from backend.services.email_service import send_email
from backend.services.pending_registration_service import (
    complete_direct_registration, complete_password_setup, fail_password_setup_delivery, issue_password_setup_token,
    verify_registration_details,
)


router = APIRouter(prefix="/api/donor-registration", tags=["donor registration"])
ALLOWED_BLOOD_GROUPS = {"A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"}
ALLOWED_GENDERS = {"Female", "Male", "Non-binary", "Other", "Not Specified"}
USERNAME_PATTERN = re.compile(r"^[A-Za-z0-9._-]+$")
STATUS_VALUES = {"Student", "Employed", "Self-employed / Business", "Unemployed", "Other"}


class RegistrationDetails(BaseModel):
    full_name: str = Field(max_length=200)
    email: EmailStr
    phone: str = Field(max_length=30)
    username: str = Field(max_length=100)
    blood_group: str = Field(max_length=5)
    gender: str | None = Field(default=None, max_length=20)
    current_status: str = Field(max_length=40)

    education_level: str | None = Field(default=None, max_length=40)
    education_level_other: str | None = Field(default=None, max_length=150)
    institution_name: str | None = Field(default=None, max_length=255)
    school_class: str | None = Field(default=None, max_length=40)
    education_board: str | None = Field(default=None, max_length=100)
    education_board_other: str | None = Field(default=None, max_length=150)
    stream: str | None = Field(default=None, max_length=60)
    course_level: str | None = Field(default=None, max_length=100)
    course_level_other: str | None = Field(default=None, max_length=150)
    course_name: str | None = Field(default=None, max_length=150)
    academic_department: str | None = Field(default=None, max_length=150)
    semester_or_year: str | None = Field(default=None, max_length=40)
    university: str | None = Field(default=None, max_length=150)
    expected_graduation_year: int | None = Field(default=None, ge=2020, le=2100)
    employment_type: str | None = Field(default=None, max_length=60)
    employment_type_other: str | None = Field(default=None, max_length=150)
    occupation: str | None = Field(default=None, max_length=150)
    organization_name: str | None = Field(default=None, max_length=200)
    employment_department: str | None = Field(default=None, max_length=150)
    industry: str | None = Field(default=None, max_length=100)
    industry_other: str | None = Field(default=None, max_length=150)
    work_location: str | None = Field(default=None, max_length=200)
    previous_occupation: str | None = Field(default=None, max_length=150)
    area_of_interest: str | None = Field(default=None, max_length=150)
    status_description: str | None = Field(default=None, max_length=300)

    @field_validator("full_name")
    @classmethod
    def validate_full_name(cls, value: str) -> str:
        value = " ".join(value.split())
        if len(value) < 2 or not any(character.isalpha() for character in value):
            raise ValueError("Enter your full name using at least 2 characters.")
        if any(not (character.isalpha() or character in " .'-") for character in value):
            raise ValueError("Full name can use letters, spaces, apostrophes, hyphens, and periods only.")
        return value

    @field_validator("email")
    @classmethod
    def normalise_email(cls, value: EmailStr) -> str:
        return str(value).strip().lower()

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Enter a phone number.")
        return value.strip()

    @field_validator("username")
    @classmethod
    def validate_username(cls, value: str) -> str:
        if value != value.strip() or len(value) < 3 or any(character.isspace() for character in value):
            raise ValueError("Username must use at least 3 characters with no spaces.")
        if not USERNAME_PATTERN.fullmatch(value):
            raise ValueError("Username can use letters, numbers, periods, underscores, and hyphens only.")
        return value.lower()

    @field_validator("blood_group")
    @classmethod
    def validate_blood_group(cls, value: str) -> str:
        value = value.strip().upper().replace(" ", "")
        if value not in ALLOWED_BLOOD_GROUPS:
            raise ValueError("Select a valid blood group.")
        return value

    @field_validator("gender")
    @classmethod
    def validate_gender(cls, value: str | None) -> str | None:
        if not value:
            return None
        value = value.strip()
        if value not in ALLOWED_GENDERS:
            raise ValueError("Select a valid gender option.")
        return value

    @field_validator(
        "education_level", "education_level_other", "institution_name", "school_class", "education_board",
        "education_board_other", "stream", "course_level", "course_level_other", "course_name",
        "academic_department", "semester_or_year", "university", "employment_type", "employment_type_other",
        "occupation", "organization_name", "employment_department", "industry", "industry_other",
        "work_location", "previous_occupation", "area_of_interest", "status_description", mode="before",
    )
    @classmethod
    def normalise_optional_text(cls, value: str | None) -> str | None:
        return " ".join(value.split()) if isinstance(value, str) and value.strip() else None

    @model_validator(mode="after")
    def validate_dynamic_profile(self) -> "RegistrationDetails":
        if self.current_status not in STATUS_VALUES:
            raise ValueError("Select a valid current status.")

        def require(*fields: str) -> None:
            if any(not getattr(self, field) for field in fields):
                raise ValueError(f"Complete the required {self.current_status.lower()} profile details.")

        if self.current_status == "Student":
            require("education_level")
            if self.education_level == "School":
                require("institution_name", "school_class", "education_board")
                if self.education_board == "Other": require("education_board_other")
            elif self.education_level == "College / University":
                require("institution_name", "course_level", "course_name", "semester_or_year", "university")
                if self.course_level == "Other": require("course_level_other")
            elif self.education_level == "Other":
                require("education_level_other", "institution_name")
            else:
                raise ValueError("Select School, College / University, or Other for education level.")
        elif self.current_status == "Employed":
            require("employment_type", "occupation", "organization_name", "industry")
            if self.employment_type == "Other": require("employment_type_other")
            if self.industry == "Other": require("industry_other")
        elif self.current_status == "Self-employed / Business":
            require("occupation", "industry")
            if self.industry == "Other": require("industry_other")
        elif self.current_status == "Other":
            require("status_description")
        return self


class SetupEmailRequest(BaseModel):
    username: str = Field(min_length=3, max_length=100)
    @field_validator("username")
    @classmethod
    def normalise_username(cls, value: str) -> str:
        return value.strip().lower()


class DirectRegistration(RegistrationDetails):
    """Public registration payload for deployments without email delivery."""

    password: str = Field(min_length=8, max_length=128)
    confirm_password: str = Field(min_length=8, max_length=128)

    @model_validator(mode="after")
    def validate_passwords(self) -> "DirectRegistration":
        if self.password != self.confirm_password:
            raise ValueError("Passwords do not match.")
        if self.password != self.password.strip() or not any(character.isalpha() for character in self.password) or not any(character.isdigit() for character in self.password):
            raise ValueError("Password must contain at least 8 characters, including a letter and a number.")
        return self


class PasswordSetupConfirmation(BaseModel):
    token: str = Field(min_length=20, max_length=4096)
    new_password: str = Field(max_length=128)
    @field_validator("new_password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        if len(value) < 8 or value != value.strip() or not any(item.isalpha() for item in value) or not any(item.isdigit() for item in value):
            raise ValueError("Password must contain at least 8 characters, including a letter and a number.")
        return value


class AdministratorDonorRegistration(BaseModel):
    full_name: str = Field(min_length=2, max_length=200); email: EmailStr; phone: str = Field(min_length=7, max_length=30)
    username: str = Field(min_length=3, max_length=100); password: str = Field(min_length=8, max_length=128)
    blood_group: str = Field(max_length=5); department: str | None = Field(default=None, max_length=150); gender: str | None = Field(default=None, max_length=20)


def _setup_email_html(setup_url: str, full_name: str) -> str:
    return f"""<!doctype html><html><body style=\"font-family:Arial,sans-serif;background:#f4f7fc;padding:32px;color:#17213b\"><main style=\"max-width:560px;margin:auto;padding:32px;background:#fff;border-radius:16px\"><h1>Set up your BloodLink password</h1><p>Hello {escape(full_name)},</p><p>Your registration details were verified. Use this secure link to create your password. It expires in 30 minutes and can be used once.</p><p style=\"margin:28px 0\"><a href=\"{escape(setup_url, quote=True)}\" style=\"padding:12px 18px;border-radius:8px;background:#c91d3f;color:#fff;text-decoration:none;font-weight:700\">Set up password</a></p><p style=\"color:#66748a;font-size:13px\">If you did not start this registration, you can ignore this email.</p></main></body></html>"""


@router.post("/verify-details")
@router.post("")
def verify_details(data: RegistrationDetails, db: Annotated[Session, Depends(get_db)]) -> dict:
    user = verify_registration_details(db, data)
    return {"success": True, "username": user.username, "registration_status": user.registration_status, "message": "Your details have been verified. Continue to send your password setup email."}


@router.post("/complete", status_code=status.HTTP_201_CREATED)
def complete_direct_donor_registration(data: DirectRegistration, db: Annotated[Session, Depends(get_db)]) -> dict:
    """Create a donor account immediately using the password from registration."""
    user = complete_direct_registration(db, data, data.password)
    return {
        "success": True,
        "message": "Your donor account has been created. You can now sign in.",
        "username": user.username,
        "login_url": "/login",
    }


@router.post("/password-setup/send", status_code=status.HTTP_202_ACCEPTED)
def send_password_setup_email(data: SetupEmailRequest, db: Annotated[Session, Depends(get_db)]) -> dict:
    user = db.scalar(select(User).where(User.username == data.username))
    if user is None or user.registration_status not in {"DETAILS_VERIFIED", "PASSWORD_SETUP_SENT"} or user.active:
        raise HTTPException(status_code=400, detail="Verify your registration details before requesting a password setup email.")
    token = issue_password_setup_token(db, user)
    setup_url = f"{get_settings().backend_url.rstrip('/')}/setup-password?token={quote(token, safe='')}"
    if not send_email(user.email, "Set up your BloodLink password", _setup_email_html(setup_url, user.full_name)):
        fail_password_setup_delivery(db, user)
        raise HTTPException(status_code=503, detail="We could not send the setup email. Please try again shortly.")
    return {"detail": "A secure password setup link has been sent to your email address."}


@router.post("/password-setup/confirm")
def confirm_password_setup(data: PasswordSetupConfirmation, db: Annotated[Session, Depends(get_db)]) -> dict:
    complete_password_setup(db, data.token, data.new_password)
    return {"detail": "Your password has been created successfully. You can now sign in."}


@router.post("/admin", status_code=status.HTTP_201_CREATED)
def administrator_register_donor(data: AdministratorDonorRegistration, db: Annotated[Session, Depends(get_db)], _: Annotated[User, Depends(require_administrator)]) -> dict:
    donor, account = create_donor_account(db, **data.model_dump())
    return {"success": True, "message": "Your donor account has been created. You can now sign in.", "donor": {"id": donor.id, "donor_code": donor.donor_code}, "user": {"id": account.id, "username": account.username}}


@router.get("/qr")
def registration_qr(_: Annotated[User, Depends(require_administrator)]) -> StreamingResponse:
    image = qrcode.make(f"{get_settings().backend_url.rstrip('/')}/donor-register")
    data = BytesIO(); image.save(data, format="PNG"); data.seek(0)
    return StreamingResponse(data, media_type="image/png", headers={"Content-Disposition": "inline; filename=BloodLink-donor-registration-qr.png"})
