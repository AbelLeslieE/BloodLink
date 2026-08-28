"""Administrator-only management of BloodLink user accounts."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.auth.dependencies import require_administrator
from backend.auth.security import hash_password
from backend.database.database import get_db
from backend.database.models import Donor, User


router = APIRouter(prefix="/api/users", tags=["users"])
ALLOWED_ROLES = {"administrator": "Administrator", "admin": "Administrator", "donor": "Donor", "nss volunteer": "Donor"}


class UserCreate(BaseModel):
    full_name: str = Field(min_length=1, max_length=200)
    department: str = Field(min_length=1, max_length=100)
    role: str = Field(default="Donor", min_length=1, max_length=50)
    email: str = Field(min_length=3, max_length=255)
    phone: str = Field(min_length=1, max_length=20)
    username: str = Field(min_length=3, max_length=100)
    password: str = Field(min_length=8, max_length=128)
    donor_id: int | None = Field(default=None, gt=0)


class UserUpdate(UserCreate):
    password: str | None = Field(default=None, min_length=8, max_length=128)


def _normalise_role(role: str) -> str:
    normalised = ALLOWED_ROLES.get(role.strip().lower())
    if normalised is None:
        raise HTTPException(status_code=422, detail="Role must be Administrator or Donor.")
    return normalised


def _serialise(user: User) -> dict:
    return {
        "id": user.id, "full_name": user.full_name, "department": user.department,
        "role": user.role, "email": user.email, "phone": user.phone,
        "username": user.username, "active": user.active, "donor_id": user.donor_id,
        "total_points": user.total_points, "donation_count": user.donation_count,
        "hide_from_leaderboard": user.hide_from_leaderboard,
    }


def _validate_donor(db: Session, donor_id: int | None) -> None:
    if donor_id is not None and db.get(Donor, donor_id) is None:
        raise HTTPException(status_code=422, detail="Selected donor does not exist.")


@router.get("")
def get_users(
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(require_administrator)],
) -> list[dict]:
    return [_serialise(user) for user in db.scalars(select(User).order_by(User.id.desc()))]


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(
    data: UserCreate,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(require_administrator)],
) -> dict:
    username = data.username.lower().strip()
    if db.scalar(select(User).where(User.username == username)):
        raise HTTPException(status_code=409, detail="Username already exists.")
    if db.scalar(select(User).where(User.email == data.email.strip().lower())):
        raise HTTPException(status_code=409, detail="Email already exists.")
    _validate_donor(db, data.donor_id)
    user = User(
        full_name=data.full_name.strip(), department=data.department.strip(),
        role=_normalise_role(data.role), email=data.email.strip().lower(),
        phone=data.phone.strip(), username=username, password_hash=hash_password(data.password),
        donor_id=data.donor_id, active=True,
    )
    db.add(user)
    try:
        db.commit()
    except IntegrityError as error:
        db.rollback()
        raise HTTPException(status_code=409, detail="The user data conflicts with an existing account.") from error
    db.refresh(user)
    return {"success": True, "user": _serialise(user)}


@router.put("/{user_id}")
def update_user(
    user_id: int, data: UserUpdate,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(require_administrator)],
) -> dict:
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found.")
    username = data.username.lower().strip()
    duplicate = db.scalar(select(User).where(User.username == username, User.id != user_id))
    if duplicate:
        raise HTTPException(status_code=409, detail="Username already exists.")
    duplicate_email = db.scalar(select(User).where(
        User.email == data.email.strip().lower(), User.id != user_id
    ))
    if duplicate_email:
        raise HTTPException(status_code=409, detail="Email already exists.")
    _validate_donor(db, data.donor_id)
    user.full_name, user.department, user.role = data.full_name.strip(), data.department.strip(), _normalise_role(data.role)
    user.email, user.phone, user.username, user.donor_id = data.email.strip().lower(), data.phone.strip(), username, data.donor_id
    if data.password:
        user.password_hash = hash_password(data.password)
        user.auth_version += 1
    try:
        db.commit()
    except IntegrityError as error:
        db.rollback()
        raise HTTPException(status_code=409, detail="The user data conflicts with an existing account.") from error
    db.refresh(user)
    return {"success": True, "user": _serialise(user)}


@router.delete("/{user_id}")
def delete_user(
    user_id: int, db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_administrator)],
) -> dict:
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="You cannot delete your own account.")
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found.")
    db.delete(user)
    try:
        db.commit()
    except IntegrityError as error:
        db.rollback()
        raise HTTPException(status_code=409, detail="This user has audit records and cannot be deleted.") from error
    return {"success": True, "message": "User deleted successfully."}
