"""SQLAlchemy ORM models for the BloodLink database foundation."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, Numeric, UniqueConstraint
from sqlalchemy import String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.database.email_token import EmailToken
from backend.database.donor_response import DonorResponse
from backend.database.database import Base
from backend.database.notification import Notification
from backend.database.notification_recipient import NotificationRecipient
from backend.database.push_subscription import PushSubscription
from backend.database.donor_profile import DonorProfile

class User(Base):
    """BloodLink system user."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    username: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        index=True,
        nullable=False,
    )

    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    full_name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )

    department: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        default="Blood Bank",
        server_default="Blood Bank",
    )

    role: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="User",
        server_default="User",
    )

    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
    )

    phone: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

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

    donor_id: Mapped[int | None] = mapped_column(
        ForeignKey("donors.id"), unique=True, nullable=True, index=True
    )

    total_points: Mapped[int] = mapped_column(
        Integer, default=0, server_default="0", nullable=False
    )

    donation_count: Mapped[int] = mapped_column(
        Integer, default=0, server_default="0", nullable=False
    )

    hide_from_leaderboard: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default="false", nullable=False
    )

    # Incrementing this value invalidates every JWT issued before the change.
    # It is used for logout and password-reset revocation without storing raw
    # tokens in the database.
    auth_version: Mapped[int] = mapped_column(
        Integer, default=0, server_default="0", nullable=False
    )

    # The TOTP seed is encrypted at rest. Recovery codes are stored only as
    # keyed hashes and are consumed individually when used.
    mfa_enabled: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default="false", nullable=False
    )
    mfa_secret_encrypted: Mapped[str | None] = mapped_column(Text, nullable=True)
    mfa_recovery_codes: Mapped[str | None] = mapped_column(Text, nullable=True)
    mfa_last_counter: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Existing accounts default to ACTIVE. New QR registrations remain unable
    # to sign in until their one-time email password setup is completed.
    registration_status: Mapped[str] = mapped_column(
        String(30), default="ACTIVE", server_default="ACTIVE", nullable=False
    )
    email_verified_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    password_setup_token_hash: Mapped[str | None] = mapped_column(
        String(128), nullable=True, unique=True
    )
    password_setup_expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    password_setup_sent_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    blood_requests: Mapped[list["BloodRequest"]] = relationship(
        back_populates="created_by_user"
    )

    donation_history_entries: Mapped[list["DonationHistory"]] = relationship(
        back_populates="recorded_by_user"
    )

    donor: Mapped["Donor | None"] = relationship(
        foreign_keys=[donor_id],
        back_populates="user_account",
    )

    push_subscriptions: Mapped[list["PushSubscription"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )

    sessions: Mapped[list["UserSession"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )


class UserSession(Base):
    """One independently revocable authenticated browser session."""

    __tablename__ = "user_sessions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    last_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(64), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(500), nullable=True)
    mfa_verified: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default="false", nullable=False
    )

    user: Mapped["User"] = relationship(back_populates="sessions")


class AuditLog(Base):
    """Append-only, tamper-evident record of security and data operations."""

    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )
    actor_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    actor_username: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    category: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    action: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    result: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    target_type: Mapped[str | None] = mapped_column(String(80), nullable=True)
    target_id: Mapped[str | None] = mapped_column(String(120), nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(64), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(500), nullable=True)
    request_method: Mapped[str | None] = mapped_column(String(10), nullable=True)
    request_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    details_json: Mapped[str] = mapped_column(Text, default="{}", server_default="{}", nullable=False)
    integrity_hash: Mapped[str] = mapped_column(String(64), nullable=False)


class BackupRecord(Base):
    """Metadata for an encrypted logical database snapshot."""

    __tablename__ = "backup_records"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    created_by: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    created_by_username: Mapped[str] = mapped_column(String(100), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    storage_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    size_bytes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    checksum_sha256: Mapped[str | None] = mapped_column(String(64), nullable=True)
    table_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    row_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    error_message: Mapped[str | None] = mapped_column(String(500), nullable=True)


class EligibilityPolicy(Base):
    """Clinician-reviewed operational donor pre-screening policy."""

    __tablename__ = "eligibility_policies"

    # BloodLink currently supports one active policy. Keeping it as a row,
    # rather than environment variables, makes every reviewed change durable
    # and auditable.
    id: Mapped[int] = mapped_column(Integer, primary_key=True, default=1)
    enforcement_mode: Mapped[str] = mapped_column(
        String(20), default="ADVISORY", server_default="ADVISORY", nullable=False
    )
    minimum_age_years: Mapped[int] = mapped_column(
        Integer, default=18, server_default="18", nullable=False
    )
    maximum_age_years: Mapped[int] = mapped_column(
        Integer, default=65, server_default="65", nullable=False
    )
    minimum_weight_kg: Mapped[Decimal] = mapped_column(
        Numeric(5, 2), default=Decimal("45.00"), server_default="45.00", nullable=False
    )
    require_complete_profile: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default="false", nullable=False
    )
    reviewer_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    review_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    source_reference: Mapped[str] = mapped_column(Text, nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1, server_default="1", nullable=False)
    updated_by: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
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

    # A temporary deferral blocks matching until this date. The row is
    # automatically returned to Available when the date arrives; the date and
    # reason remain as useful operational context for administrators.
    deferred_until: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
        index=True,
    )

    deferral_reason: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    total_points: Mapped[int] = mapped_column(
        Integer, default=0, server_default="0", nullable=False
    )

    donation_count: Mapped[int] = mapped_column(
        Integer, default=0, server_default="0", nullable=False
    )

    hide_from_leaderboard: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default="false", nullable=False
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





    # ======================================================
    # RELATIONSHIPS
    # ======================================================

    donation_history_entries: Mapped[
        list["DonationHistory"]
    ] = relationship(
        back_populates="donor"
    )

    notification_recipients: Mapped[
        list["NotificationRecipient"]
    ] = relationship(
        back_populates="donor",
        cascade="all, delete-orphan",
    )

    responses: Mapped[
        list["DonorResponse"]
    ] = relationship(
        back_populates="donor",
        cascade="all, delete-orphan",
    )

    user_account: Mapped["User | None"] = relationship(
        foreign_keys="User.donor_id",
        back_populates="donor",
        uselist=False,
    )

    profile: Mapped["DonorProfile | None"] = relationship(
        back_populates="donor",
        uselist=False,
        cascade="all, delete-orphan",
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

    units_fulfilled: Mapped[int] = mapped_column(
        Integer,
        default=0,
        server_default="0",
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

    # Lifecycle automation uses an exact UTC deadline derived from the
    # required date and deployment timezone.  The remaining fields preserve
    # why and when a request was escalated or closed.
    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
    )

    escalation_level: Mapped[int] = mapped_column(
        Integer,
        default=0,
        server_default="0",
        nullable=False,
    )

    escalation_reason: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    escalated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    closure_reason: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    closed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
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

    # Structured location fields are optional so historical requests that only
    # recorded a free-text place remain valid.  When both coordinates are
    # present the matching service can rank donors by real geographic distance.
    hospital_district: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    hospital_city: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    hospital_latitude: Mapped[Decimal | None] = mapped_column(
        Numeric(9, 6),
        nullable=True,
    )

    hospital_longitude: Mapped[Decimal | None] = mapped_column(
        Numeric(9, 6),
        nullable=True,
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
        back_populates="blood_request",
        cascade="all, delete-orphan",
    )

    responses: Mapped[
        list["DonorResponse"]
    ] = relationship(
        back_populates="blood_request",
        cascade="all, delete-orphan",
    )

    @property
    def units_remaining(self) -> int:
        """Return the unfilled request quantity without exposing negatives."""
        return max(0, self.units_required - (self.units_fulfilled or 0))



class DonationHistory(Base):
    """Recorded donation associated with a donor and blood request."""

    __tablename__ = "donation_history"
    __table_args__ = (
        UniqueConstraint(
            "donor_id", "blood_request_id", name="uq_donation_history_donor_request"
        ),
    )

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

    donor_id: Mapped[int | None] = mapped_column(
        ForeignKey("donors.id"),
        index=True,
        nullable=True,
    )

    # Present only when this request was fulfilled by someone who is not a
    # registered BloodLink donor. External donors never receive account-based
    # rewards, certificates, or donor-history entries.
    external_donor_name: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
    )

    blood_request_id: Mapped[int] = mapped_column(
        ForeignKey("blood_requests.id"),
        index=True,
        nullable=False,
    )

    # ======================================================
    # DONATION INFORMATION
    # ======================================================

    hospital_name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )

    donation_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )

    units: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
        server_default="1",
    )

    donation_type: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="Voluntary",
        server_default="Voluntary",
    )

    remarks: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # ======================================================
    # AUDIT
    # ======================================================

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

    points_awarded: Mapped[int] = mapped_column(
        Integer, default=0, server_default="0", nullable=False
    )
    status: Mapped[str] = mapped_column(
        String(50), default="Donation Confirmed", server_default="Donation Confirmed", nullable=False
    )
    awarded_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # ======================================================
    # RELATIONSHIPS
    # ======================================================

    donor: Mapped["Donor | None"] = relationship(
        back_populates="donation_history_entries"
    )

    blood_request: Mapped["BloodRequest"] = relationship(
        back_populates="donation_history_entries"
    )

    recorded_by_user: Mapped["User"] = relationship(
        back_populates="donation_history_entries"
    )

    certificate: Mapped["DonationCertificate | None"] = relationship(
        back_populates="donation",
        uselist=False,
        cascade="all, delete-orphan",
    )

class DonationCertificate(Base):
    """A downloadable certificate issued for one confirmed donation."""

    __tablename__ = "donation_certificates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    donation_history_id: Mapped[int] = mapped_column(
        ForeignKey("donation_history.id"), unique=True, nullable=False, index=True
    )
    certificate_number: Mapped[str] = mapped_column(
        String(64), unique=True, nullable=False, index=True
    )
    issued_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    donation: Mapped["DonationHistory"] = relationship(back_populates="certificate")


class SavedMatch(Base):
    """An administrator's persisted donor selection for a blood request."""

    __tablename__ = "saved_matches"
    __table_args__ = (
        UniqueConstraint(
            "blood_request_id", "donor_id", name="uq_saved_matches_request_donor"
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    blood_request_id: Mapped[int] = mapped_column(
        ForeignKey("blood_requests.id"), nullable=False, index=True
    )
    donor_id: Mapped[int] = mapped_column(
        ForeignKey("donors.id"), nullable=False, index=True
    )
    saved_by: Mapped[int] = mapped_column(
        ForeignKey("users.id"), nullable=False, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
