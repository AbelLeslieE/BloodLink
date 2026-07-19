"""
API routes for BloodLink donor matching.
"""

from __future__ import annotations

from fastapi import APIRouter
from fastapi import Depends
from sqlalchemy.orm import Session

from backend.auth.dependencies import require_authentication
from backend.database.database import get_db
from backend.database.models import User

router = APIRouter(
    prefix="/api/match",
    tags=["Donor Matching"],
)