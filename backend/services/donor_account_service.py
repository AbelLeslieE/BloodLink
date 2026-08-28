"""Creation and validation of linked public donor accounts."""

from __future__ import annotations

import re

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.auth.security import hash_password
from backend.database import crud
from backend.database.models import Donor, User


ALLOWED_BLOOD_GROUPS = {"A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"}


def normalise_phone(phone: str) -> str:
    """Store a phone number consistently and reject unusable input."""
    value = re.sub(r"[\s()-]", "", phone)
    if value.startswith("00"):
        value = f"+{value[2:]}"
    digits = value[1:] if value.startswith("+") else value
    if not digits.isdigit() or not 7 <= len(digits) <= 15:
        raise HTTPException(status_code=422, detail="Enter a valid phone number.")
    return value


def _phone_key(phone: str | None) -> str | None:
    """Return a comparison key that treats common Indian formats as equal."""
    if not phone:
        return None
    digits = re.sub(r"\D", "", phone)
    if len(digits) == 12 and digits.startswith("91"):
        return digits[2:]
    return digits


def create_donor_account(
    db: Session,
    *,
    full_name: str,
    email: str,
    phone: str,
    username: str,
    password: str,
    blood_group: str,
    department: str | None = None,
    gender: str | None = None,
) -> tuple[Donor, User]:
    """Create matching Donor and User records in one database transaction."""
    clean_email = email.strip().lower()
    clean_username = username.strip().lower()
    clean_phone = normalise_phone(phone)
    clean_group = blood_group.strip().upper().replace(" ", "")
    if clean_group not in ALLOWED_BLOOD_GROUPS:
        raise HTTPException(status_code=422, detail="Select a valid blood group.")

    if db.scalar(select(User.id).where(func.lower(User.username) == clean_username)):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="That username is already registered.")
    registered_phones = list(db.scalars(select(User.phone))) + list(db.scalars(select(Donor.phone)))
    if any(_phone_key(phone) == _phone_key(clean_phone) for phone in registered_phones):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="That phone number is already registered.")
    if db.scalar(select(User.id).where(func.lower(User.email) == clean_email)):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="That email address is already registered.")
    if db.scalar(select(Donor.id).where(func.lower(Donor.email) == clean_email)):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="That email address is already registered.")

    donor = Donor(
        donor_code=crud.generate_donor_code(db),
        full_name=full_name.strip(), blood_group=clean_group,
        gender=(gender or "Not Specified").strip(), phone=clean_phone,
        email=clean_email, class_department=(department or "Donor registration").strip(),
        status="Available", hb_above_12_5="Not Recorded",
        regular_medication="Not Recorded", bp_normal="Not Recorded",
    )
    db.add(donor)
    db.flush()
    account = User(
        full_name=donor.full_name, department=donor.class_department or "Donor registration",
        role="Donor", email=clean_email, phone=clean_phone, username=clean_username,
        password_hash=hash_password(password), donor_id=donor.id, active=True,
    )
    db.add(account)
    try:
        db.commit()
    except IntegrityError as error:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "This account conflicts with an existing record. Try a different "
                "username, phone number, or email address."
            ),
        ) from error
    db.refresh(donor)
    db.refresh(account)
    return donor, account
