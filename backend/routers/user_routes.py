from datetime import datetime

import bcrypt
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.database.database import get_db
from backend.database.models import User

router = APIRouter(
    prefix="/api/users",
    tags=["users"],
)


class UserCreate(BaseModel):
    full_name: str
    department: str
    role: str
    email: str
    phone: str
    username: str
    password: str


class UserUpdate(BaseModel):
    full_name: str
    department: str
    role: str
    email: str
    phone: str
    username: str
    password: str = ""


@router.get("")
def get_users(db: Session = Depends(get_db)):
    users = db.query(User).all()

    return [
        {
            "id": user.id,
            "full_name": user.full_name,
            "department": user.department,
            "role": user.role,
            "email": user.email,
            "phone": user.phone,
            "username": user.username,
            "active": user.active,
        }
        for user in users
    ]


@router.post("/register")
def register(data: UserCreate, db: Session = Depends(get_db)):
    existing = (
        db.query(User)
        .filter(User.username == data.username.lower().strip())
        .first()
    )

    if existing:
        raise HTTPException(
            status_code=400,
            detail="Username already exists.",
        )

    hashed = bcrypt.hashpw(
        data.password.encode(),
        bcrypt.gensalt(),
    ).decode()

    user = User(
        full_name=data.full_name,
        department=data.department,
        role=data.role,
        email=data.email,
        phone=data.phone,
        username=data.username.lower().strip(),
        password_hash=hashed,
        active=True,
        created_at=datetime.utcnow(),
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return {
        "success": True,
        "message": "User created successfully.",
    }


@router.put("/{user_id}")
def update_user(
    user_id: int,
    data: UserUpdate,
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found.",
        )

    existing = (
        db.query(User)
        .filter(
            User.username == data.username.lower().strip(),
            User.id != user_id,
        )
        .first()
    )

    if existing:
        raise HTTPException(
            status_code=400,
            detail="Username already exists.",
        )

    user.full_name = data.full_name
    user.department = data.department
    user.role = data.role
    user.email = data.email
    user.phone = data.phone
    user.username = data.username.lower().strip()

    if data.password.strip():
        user.password_hash = bcrypt.hashpw(
            data.password.encode(),
            bcrypt.gensalt(),
        ).decode()

    db.commit()
    db.refresh(user)

    return {
        "success": True,
        "message": "User updated successfully.",
    }


@router.delete("/{user_id}")
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found.",
        )

    db.delete(user)
    db.commit()

    return {
        "success": True,
        "message": "User deleted successfully.",
    }