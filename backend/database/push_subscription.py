"""Persistent, server-owned browser push subscriptions."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database.database import Base


class PushSubscription(Base):
    """One browser/device subscription owned by an authenticated user.

    Recipient targeting is derived from the linked donor record at delivery
    time, so a donor's blood group, availability, or district change takes
    effect without recreating a browser subscription.
    """

    __tablename__ = "push_subscriptions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    endpoint: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    p256dh: Mapped[str] = mapped_column(String(255), nullable=False)
    auth: Mapped[str] = mapped_column(String(255), nullable=False)
    enabled: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default="true"
    )
    # A policy hook for future urgency filtering. Existing opt-ins receive all
    # valid requests; later UI may set this to Urgent or Emergency.
    minimum_priority: Mapped[str] = mapped_column(
        String(20), nullable=False, default="Normal", server_default="Normal"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    user: Mapped["User"] = relationship(back_populates="push_subscriptions")
