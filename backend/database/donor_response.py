"""
==========================================================
Donor Response Model
==========================================================

Stores donor responses to blood donation requests.
Each response belongs to a secure email token, a donor,
and a blood request.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database.database import Base


class DonorResponse(Base):
    """Stores donor responses."""

    __tablename__ = "donor_responses"
    __table_args__ = (
        UniqueConstraint(
            "donor_id", "blood_request_id", name="uq_donor_response_donor_request"
        ),
    )

    # ==========================================================
    # PRIMARY KEY
    # ==========================================================

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    # ==========================================================
    # FOREIGN KEYS
    # ==========================================================

    email_token_id: Mapped[int | None] = mapped_column(
        ForeignKey("email_tokens.id"),
        nullable=True,
        index=True,
    )

    donor_id: Mapped[int] = mapped_column(
        ForeignKey("donors.id"),
        nullable=False,
        index=True,
    )

    blood_request_id: Mapped[int] = mapped_column(
        ForeignKey("blood_requests.id"),
        nullable=False,
        index=True,
    )

    # ==========================================================
    # RESPONSE
    # ==========================================================

    response: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    remarks: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # ==========================================================
    # TIMESTAMP
    # ==========================================================

    responded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
    )

    # ==========================================================
    # RELATIONSHIPS
    # ==========================================================

    email_token = relationship(
        "EmailToken",
        back_populates="responses",
    )

    donor = relationship(
        "Donor",
        back_populates="responses",
    )

    blood_request = relationship(
        "BloodRequest",
        back_populates="responses",
    )
