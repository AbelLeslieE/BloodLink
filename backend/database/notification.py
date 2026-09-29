"""
Notification (Campaign) Model

One notification represents one email campaign for a blood request.

A campaign contains multiple notification recipients.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database.database import Base


class Notification(Base):
    __tablename__ = "notifications"

    # ---------------------------------------------------------
    # Primary Key
    # ---------------------------------------------------------

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    # ---------------------------------------------------------
    # Campaign Information
    # ---------------------------------------------------------

    blood_request_id: Mapped[int] = mapped_column(
        ForeignKey("blood_requests.id"),
        index=True,
        nullable=False,
    )

    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(50),
        default="ACTIVE",
        server_default="ACTIVE",
        nullable=False,
    )

    # ---------------------------------------------------------
    # Statistics
    # ---------------------------------------------------------

    total_sent: Mapped[int] = mapped_column(
        default=0,
        server_default="0",
        nullable=False,
    )

    accepted_count: Mapped[int] = mapped_column(
        default=0,
        server_default="0",
        nullable=False,
    )

    declined_count: Mapped[int] = mapped_column(
        default=0,
        server_default="0",
        nullable=False,
    )

    pending_count: Mapped[int] = mapped_column(
        default=0,
        server_default="0",
        nullable=False,
    )

    queued_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        server_default="0",
        nullable=False,
    )

    # Donors are contacted in ranked batches.  Later stages remain queued until
    # an administrator releases them after the cooldown and only while the
    # campaign still needs more acceptances.
    stage_size: Mapped[int] = mapped_column(
        Integer,
        default=5,
        server_default="5",
        nullable=False,
    )

    stage_delay_minutes: Mapped[int] = mapped_column(
        Integer,
        default=30,
        server_default="30",
        nullable=False,
    )

    current_stage: Mapped[int] = mapped_column(
        Integer,
        default=0,
        server_default="0",
        nullable=False,
    )

    target_acceptances: Mapped[int] = mapped_column(
        Integer,
        default=1,
        server_default="1",
        nullable=False,
    )

    # ---------------------------------------------------------
    # Audit
    # ---------------------------------------------------------

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    sent_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    last_stage_sent_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    next_stage_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # ---------------------------------------------------------
    # Relationships
    # ---------------------------------------------------------

    blood_request: Mapped["BloodRequest"] = relationship(
        back_populates="notifications"
    )

    recipients: Mapped[list["NotificationRecipient"]] = relationship(
        back_populates="notification",
        cascade="all, delete-orphan",
    )
