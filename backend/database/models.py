"""SQLAlchemy ORM models for the BloodLink database foundation."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, Numeric
from sqlalchemy import String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database.database import Base


class User(Base):
    """NSS volunteer account with access to the BloodLink application."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        index=True,
        nullable=False,
    )
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(200), nullable=False)
    active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        server_default="true",
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    last_login: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    blood_requests: Mapped[list["BloodRequest"]] = relationship(
        back_populates="created_by_user"
    )
    donation_history_entries: Mapped[list["DonationHistory"]] = relationship(
        back_populates="recorded_by_user"
    )


# ==========================================================
# DONOR MODEL
# ==========================================================

class Donor(Base):
    """
    Blood donor record managed by BloodLink.

    Donor records may be created manually or imported from
    historical Excel files. Fields that may be unavailable
    in older records are therefore nullable.
    """

    __tablename__ = "donors"

    # ======================================================
    # PRIMARY KEY / BLOODLINK IDENTIFIER
    # ======================================================

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    donor_code: Mapped[str] = mapped_column(
        String(30),
        unique=True,
        index=True,
        nullable=False,
    )

    # ======================================================
    # PERSONAL INFORMATION
    # ======================================================

    full_name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )

    gender: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
    )

    date_of_birth: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    blood_group: Mapped[str] = mapped_column(
        String(5),
        index=True,
        nullable=False,
    )

    # ======================================================
    # CONTACT INFORMATION
    # ======================================================

    phone: Mapped[str | None] = mapped_column(
        String(30),
        index=True,
        nullable=True,
    )

    email: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    # ======================================================
    # COLLEGE / ORGANIZATION INFORMATION
    # ======================================================

    class_department: Mapped[str | None] = mapped_column(
        String(150),
        nullable=True,
    )

    # ======================================================
    # LOCATION INFORMATION
    # ======================================================

    district: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    city: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    address: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    latitude: Mapped[Decimal | None] = mapped_column(
        Numeric(9, 6),
        nullable=True,
    )

    longitude: Mapped[Decimal | None] = mapped_column(
        Numeric(9, 6),
        nullable=True,
    )

    # ======================================================
    # DONOR / HEALTH INFORMATION
    # ======================================================

    weight: Mapped[Decimal | None] = mapped_column(
        Numeric(5, 2),
        nullable=True,
    )

    # These three fields use:
    # "Yes", "No", or "Not Recorded".
    #
    # Manual donor registration will ask Yes/No.
    # "Not Recorded" is used when historical/imported data
    # does not contain the information.

    hb_above_12_5: Mapped[str] = mapped_column(
        String(20),
        default="Not Recorded",
        server_default="Not Recorded",
        nullable=False,
    )

    regular_medication: Mapped[str] = mapped_column(
        String(20),
        default="Not Recorded",
        server_default="Not Recorded",
        nullable=False,
    )

    bp_normal: Mapped[str] = mapped_column(
        String(20),
        default="Not Recorded",
        server_default="Not Recorded",
        nullable=False,
    )

    medical_conditions: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # ======================================================
    # DONATION INFORMATION
    # ======================================================

    last_donation_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    total_donations: Mapped[int] = mapped_column(
        Integer,
        default=0,
        server_default="0",
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(50),
        default="Available",
        server_default="Available",
        nullable=False,
    )

    # ======================================================
    # AUDIT INFORMATION
    # ======================================================

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # ======================================================
    # RELATIONSHIPS
    # ======================================================

    donation_history_entries: Mapped[
        list["DonationHistory"]
    ] = relationship(
        back_populates="donor"
    )

    notifications: Mapped[
        list["Notification"]
    ] = relationship(
        back_populates="donor"
    )
# ==========================================================
# BLOOD REQUEST MODEL
# ==========================================================

# ==========================================================
# BLOOD REQUEST MODEL
# ==========================================================

class BloodRequest(Base):
    """
    Blood requirement received and managed through BloodLink.

    The model stores only information normally available
    from a real blood request, along with internal BloodLink
    management fields.
    """

    __tablename__ = "blood_requests"

    # ======================================================
    # PRIMARY KEY
    # ======================================================

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )


    # ======================================================
    # PERSON / CASE DETAILS
    # ======================================================

    patient_name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )

    case_details: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )


    # ======================================================
    # BLOOD REQUIREMENT
    # ======================================================

    blood_group: Mapped[str] = mapped_column(
        String(5),
        nullable=False,
    )

    units_required: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    required_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )


    # ======================================================
    # INTERNAL PRIORITY / STATUS
    # ======================================================

    priority: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(50),
        default="Pending",
        server_default="Pending",
        nullable=False,
    )


    # ======================================================
    # HOSPITAL DETAILS
    # ======================================================

    hospital_name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )

    hospital_location: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )


    # ======================================================
    # BYSTANDER / CONTACT DETAILS
    # ======================================================

    contact_person: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )

    contact_phone: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )
    # ======================================================
    # ADDITIONAL INFORMATION
    # ======================================================

    additional_notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # ======================================================
    # OWNERSHIP / AUDIT
    # ======================================================

    created_by: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        index=True,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )


    # ======================================================
    # RELATIONSHIPS
    # ======================================================

    created_by_user: Mapped["User"] = relationship(
        back_populates="blood_requests"
    )

    donation_history_entries: Mapped[
        list["DonationHistory"]
    ] = relationship(
        back_populates="blood_request"
    )

    notifications: Mapped[
        list["Notification"]
    ] = relationship(
        back_populates="blood_request"
    )
class DonationHistory(Base):
    """Recorded donation associated with a donor and blood request."""

    __tablename__ = "donation_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    donor_id: Mapped[int] = mapped_column(
        ForeignKey("donors.id"),
        index=True,
        nullable=False,
    )
    blood_request_id: Mapped[int] = mapped_column(
        ForeignKey("blood_requests.id"),
        index=True,
        nullable=False,
    )
    hospital_name: Mapped[str] = mapped_column(String(200), nullable=False)
    donation_date: Mapped[date] = mapped_column(Date, nullable=False)
    remarks: Mapped[str | None] = mapped_column(Text, nullable=True)
    recorded_by: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        index=True,
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    donor: Mapped["Donor"] = relationship(back_populates="donation_history_entries")
    blood_request: Mapped["BloodRequest"] = relationship(
        back_populates="donation_history_entries"
    )
    recorded_by_user: Mapped["User"] = relationship(
        back_populates="donation_history_entries"
    )


class Notification(Base):
    """Notification record sent to a donor for a blood request."""

    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    blood_request_id: Mapped[int] = mapped_column(
        ForeignKey("blood_requests.id"),
        index=True,
        nullable=False,
    )
    donor_id: Mapped[int] = mapped_column(
        ForeignKey("donors.id"),
        index=True,
        nullable=False,
    )
    notification_status: Mapped[str] = mapped_column(String(50), nullable=False)
    response: Mapped[str | None] = mapped_column(String(100), nullable=True)
    sent_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    responded_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    blood_request: Mapped["BloodRequest"] = relationship(
        back_populates="notifications"
    )
    donor: Mapped["Donor"] = relationship(back_populates="notifications")
