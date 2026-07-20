"""
Notification Recipient Model

Each recipient represents one donor that received an email
for a notification campaign.

Notification (Campaign)
        │
        ├── Recipient 1
        ├── Recipient 2
        ├── Recipient 3
        └── Recipient N
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database.database import Base


class NotificationRecipient(Base):
    __tablename__ = "notification_recipients"

    # ==========================================================
    # PRIMARY KEY
    # ==========================================================

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    # ==========================================================
    # FOREIGN KEYS
    # ==========================================================

    notification_id: Mapped[int] = mapped_column(
        ForeignKey("notifications.id"),
        index=True,
        nullable=False,
    )

    donor_id: Mapped[int] = mapped_column(
        ForeignKey("donors.id"),
        index=True,
        nullable=False,
    )

    email_token_id: Mapped[int | None] = mapped_column(
        ForeignKey("email_tokens.id"),
        nullable=True,
    )

    # ==========================================================
    # RECIPIENT INFORMATION
    # ==========================================================

    email: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    distance: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    # ==========================================================
    # STATUS
    # ==========================================================

    status: Mapped[str] = mapped_column(
        String(20),
        default="PENDING",
        server_default="PENDING",
        nullable=False,
    )

    # ==========================================================
    # TIMESTAMPS
    # ==========================================================

    sent_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    responded_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # ==========================================================
    # RELATIONSHIPS
    # ==========================================================

    notification: Mapped["Notification"] = relationship(
        back_populates="recipients"
    )

    donor: Mapped["Donor"] = relationship(
        back_populates="notification_recipients"
    )

    email_token: Mapped["EmailToken | None"] = relationship(
        back_populates="recipient",
        uselist=False,
    )