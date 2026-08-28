"""Public QR-linked donor registration and protected QR generation APIs."""

from __future__ import annotations

from io import BytesIO
from typing import Annotated

import qrcode
from fastapi import APIRouter, Depends, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session

from backend.auth.dependencies import require_administrator
from backend.config.settings import get_settings
from backend.database.database import get_db
from backend.database.models import User
from backend.services.donor_account_service import create_donor_account


router = APIRouter(prefix="/api/donor-registration", tags=["donor registration"])


class DonorRegistration(BaseModel):
    full_name: str = Field(min_length=2, max_length=200)
    email: EmailStr
    phone: str = Field(min_length=7, max_length=30)
    username: str = Field(min_length=3, max_length=100, pattern=r"^[A-Za-z0-9._-]+$")
    password: str = Field(min_length=8, max_length=128)
    blood_group: str = Field(min_length=2, max_length=5)
    department: str | None = Field(default=None, max_length=150)
    gender: str | None = Field(default=None, max_length=20)


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
