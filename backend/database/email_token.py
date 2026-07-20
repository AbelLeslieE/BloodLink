"""
==========================================================
Email Token Model
==========================================================

Stores secure one-time email tokens generated for donors.
Each selected donor receives one unique token for a specific
blood request.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database.database import Base


class EmailToken(Base):
    """Stores one secure email token per donor per blood request."""

    __tablename__ = "email_tokens"

    # ======================================================
    # PRIMARY KEY
    # ======================================================

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    # ======================================================
    # RELATIONSHIPS
    # ======================================================

    recipient = relationship(
        "NotificationRecipient",
        back_populates="email_token",
        uselist=False,
    )

    responses = relationship(
        "DonorResponse",
        back_populates="email_token",
        cascade="all, delete-orphan",
    )

    # ======================================================
    # TOKEN DATA
    # ======================================================

    token: Mapped[str] = mapped_column(
        String(512),
        unique=True,
        nullable=False,
    )

    used: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        server_default="false",
        nullable=False,
    )

    # ======================================================
    # TIMESTAMPS
    # ======================================================

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
    )

    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    # ======================================================
    # ORM RELATIONSHIPS
    # ======================================================

    recipient = relationship(
        "NotificationRecipient",
        back_populates="email_token",
        uselist=False,
    )

    responses = relationship(
        "DonorResponse",
        back_populates="email_token",
        cascade="all, delete-orphan",
    )