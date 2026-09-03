"""Transactional pending donor registration and one-time password setup."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
import hashlib
import secrets

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.auth.security import hash_password
from backend.database import crud
from backend.database.donor_profile import DonorProfile
from backend.database.models import Donor, User
from backend.services.donor_account_service import _phone_key, normalise_phone


SETUP_TOKEN_TTL = timedelta(minutes=30)
SETUP_EMAIL_COOLDOWN = timedelta(seconds=60)


def token_hash(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _pending_status(user: User) -> bool:
    return user.registration_status != "ACTIVE" or not user.active


def _profile_summary(data) -> str:
    if data.current_status == "Student":
        return " · ".join(item for item in ["Student", data.education_level, data.institution_name, data.course_name] if item)[:150]
    if data.current_status == "Employed":
        return " · ".join(item for item in ["Employed", data.occupation, data.organization_name] if item)[:150]
    if data.current_status == "Self-employed / Business":
        return " · ".join(item for item in ["Self-employed", data.occupation, data.organization_name] if item)[:150]
    return data.current_status[:150]


def _profile_values(data) -> dict:
    fields = (
        "current_status", "education_level", "education_level_other", "institution_name", "school_class",
        "education_board", "education_board_other", "stream", "course_level", "course_level_other",
        "course_name", "academic_department", "semester_or_year", "university", "expected_graduation_year",
        "employment_type", "employment_type_other", "occupation", "organization_name",
        "employment_department", "industry", "industry_other", "work_location", "previous_occupation",
        "area_of_interest", "status_description",
    )
    return {field: getattr(data, field) for field in fields}


def _find_phone_conflict(
    db: Session, phone: str, ignored_user_id: int | None = None, ignored_donor_id: int | None = None,
) -> bool:
    user_phones = db.scalars(select(User.phone).where(User.id != ignored_user_id) if ignored_user_id else select(User.phone)).all()
    donor_statement = select(Donor.phone)
    if ignored_donor_id is not None:
        donor_statement = donor_statement.where(Donor.id != ignored_donor_id)
    donor_phones = db.scalars(donor_statement).all()
    return any(_phone_key(item) == _phone_key(phone) for item in [*user_phones, *donor_phones])


def verify_registration_details(db: Session, data) -> User:
    """Upsert only a matching pending account; never create a login password."""
    clean_email = data.email.strip().lower()
    clean_username = data.username.strip().lower()
    clean_phone = normalise_phone(data.phone)

    existing_username = db.scalar(select(User).where(func.lower(User.username) == clean_username))
    if existing_username is not None:
        if not _pending_status(existing_username):
            raise HTTPException(status_code=409, detail="This username is already in use. Please choose another username.")
        if existing_username.email != clean_email or _phone_key(existing_username.phone) != _phone_key(clean_phone):
            raise HTTPException(status_code=409, detail="This username is already in use. Please choose another username.")
        user = existing_username
    else:
        email_user = db.scalar(select(User).where(func.lower(User.email) == clean_email))
        email_donor = db.scalar(select(Donor).where(func.lower(Donor.email) == clean_email))
        if email_user is not None or email_donor is not None:
            raise HTTPException(status_code=409, detail="That email address is already registered.")
        if _find_phone_conflict(db, clean_phone):
            raise HTTPException(status_code=409, detail="That phone number is already registered.")
        donor = Donor(
            donor_code=crud.generate_donor_code(db), full_name=data.full_name,
            blood_group=data.blood_group, gender=data.gender or "Not Specified",
            phone=clean_phone, email=clean_email, class_department=_profile_summary(data),
            status="Available", hb_above_12_5="Not Recorded", regular_medication="Not Recorded", bp_normal="Not Recorded",
        )
        db.add(donor)
        db.flush()
        user = User(
            full_name=data.full_name, department=_profile_summary(data)[:100], role="Donor",
            email=clean_email, phone=clean_phone, username=clean_username,
            password_hash=hash_password(secrets.token_urlsafe(32)), donor_id=donor.id,
            active=False, registration_status="DETAILS_VERIFIED",
        )
        db.add(user)
        db.flush()

    donor = user.donor
    if donor is None:
        raise HTTPException(status_code=409, detail="This pending registration is incomplete. Please contact BloodLink support.")
    if _find_phone_conflict(db, clean_phone, user.id, donor.id):
        raise HTTPException(status_code=409, detail="That phone number is already registered.")
    donor.full_name, donor.blood_group, donor.gender = data.full_name, data.blood_group, data.gender or "Not Specified"
    donor.phone, donor.email, donor.class_department = clean_phone, clean_email, _profile_summary(data)
    user.full_name, user.email, user.phone, user.department = data.full_name, clean_email, clean_phone, donor.class_department[:100]
    user.active, user.registration_status = False, "DETAILS_VERIFIED"
    user.password_setup_token_hash = user.password_setup_expires_at = user.password_setup_sent_at = None

    profile = donor.profile or DonorProfile(donor_id=donor.id, current_status=data.current_status)
    for name, value in _profile_values(data).items():
        setattr(profile, name, value)
    if donor.profile is None:
        db.add(profile)
    try:
        db.commit()
    except IntegrityError as error:
        db.rollback()
        raise HTTPException(status_code=409, detail="This registration conflicts with an existing account. Please review your details.") from error
    db.refresh(user)
    return user


def issue_password_setup_token(db: Session, user: User) -> str:
    """Replace any earlier setup token and return the raw value for email only."""
    now = datetime.now(timezone.utc)
    previous_sent = user.password_setup_sent_at
    if previous_sent is not None:
        if previous_sent.tzinfo is None:
            previous_sent = previous_sent.replace(tzinfo=timezone.utc)
        if now - previous_sent < SETUP_EMAIL_COOLDOWN:
            raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Please wait one minute before requesting another setup email.")
    token = secrets.token_urlsafe(48)
    user.password_setup_token_hash = token_hash(token)
    user.password_setup_expires_at = now + SETUP_TOKEN_TTL
    user.password_setup_sent_at = now
    user.registration_status = "PASSWORD_SETUP_SENT"
    db.commit()
    return token


def fail_password_setup_delivery(db: Session, user: User) -> None:
    user.password_setup_token_hash = user.password_setup_expires_at = user.password_setup_sent_at = None
    user.registration_status = "DETAILS_VERIFIED"
    db.commit()


def complete_password_setup(db: Session, token: str, password: str) -> User:
    user = db.scalar(select(User).where(User.password_setup_token_hash == token_hash(token)))
    now = datetime.now(timezone.utc)
    expires_at = user.password_setup_expires_at if user else None
    if expires_at is not None and expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if user is None or expires_at is None or expires_at <= now or user.registration_status != "PASSWORD_SETUP_SENT":
        raise HTTPException(status_code=400, detail="This password setup link is invalid, expired, or has already been used.")
    user.password_hash = hash_password(password)
    user.active, user.registration_status = True, "ACTIVE"
    user.email_verified_at = now
    user.password_setup_token_hash = user.password_setup_expires_at = user.password_setup_sent_at = None
    user.auth_version += 1
    db.commit()
    return user
