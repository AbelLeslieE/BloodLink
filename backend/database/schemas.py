"""Pydantic schemas for the BloodLink database models."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class SchemaBase(BaseModel):
    """Shared Pydantic configuration for request and response schemas."""

    model_config = ConfigDict(from_attributes=True)


class UserBase(SchemaBase):
    """Fields shared by user create and response schemas."""

    username: str = Field(min_length=1, max_length=100)
    full_name: str = Field(min_length=1, max_length=200)
    active: bool = True


class UserCreate(UserBase):
    """Fields required to create a user record."""

    password_hash: str = Field(min_length=1, max_length=255)


class UserUpdate(SchemaBase):
    """Fields that may be supplied when updating a user record."""

    username: str | None = Field(default=None, min_length=1, max_length=100)
    password_hash: str | None = Field(default=None, min_length=1, max_length=255)
    full_name: str | None = Field(default=None, min_length=1, max_length=200)
    active: bool | None = None


class UserResponse(UserBase):
    """Safe user representation returned by the application."""

    id: int
    created_at: datetime
    last_login: datetime | None


# ==========================================================
# DONOR SCHEMAS
# ==========================================================

# ==========================================================
# DONOR SCHEMAS
# ==========================================================

class DonorBase(SchemaBase):
    """
    Shared donor information.

    Optional fields support incomplete historical records
    imported from Excel.
    """

    # ======================================================
    # PERSONAL INFORMATION
    # ======================================================

    full_name: str = Field(
        min_length=1,
        max_length=200,
    )

    blood_group: str = Field(
        min_length=1,
        max_length=5,
    )

    gender: str | None = Field(
        default=None,
        max_length=20,
    )

    date_of_birth: date | None = None

    # ======================================================
    # CONTACT INFORMATION
    # ======================================================

    phone: str | None = Field(
        default=None,
        max_length=30,
    )

    email: str | None = Field(
        default=None,
        max_length=255,
    )

    # ======================================================
    # COLLEGE / ORGANIZATION
    # ======================================================

    class_department: str | None = Field(
        default=None,
        max_length=150,
    )

    # ======================================================
    # LOCATION
    # ======================================================

    district: str | None = Field(
        default=None,
        max_length=100,
    )

    city: str | None = Field(
        default=None,
        max_length=100,
    )

    address: str | None = None

    latitude: Decimal | None = Field(
        default=None,
        max_digits=9,
        decimal_places=6,
    )

    longitude: Decimal | None = Field(
        default=None,
        max_digits=9,
        decimal_places=6,
    )

    # ======================================================
    # HEALTH / ELIGIBILITY
    # ======================================================

    weight: Decimal | None = Field(
        default=None,
        max_digits=5,
        decimal_places=2,
    )

    hb_above_12_5: str = Field(
        default="Not Recorded",
        max_length=20,
    )

    regular_medication: str = Field(
        default="Not Recorded",
        max_length=20,
    )

    bp_normal: str = Field(
        default="Not Recorded",
        max_length=20,
    )

    medical_conditions: str | None = None

    # ======================================================
    # DONATION INFORMATION
    # ======================================================

    last_donation_date: date | None = None

    total_donations: int = Field(
        default=0,
        ge=0,
    )

    status: str = Field(
        default="Available",
        min_length=1,
        max_length=50,
    )


# ==========================================================
# CREATE DONOR
# ==========================================================

class DonorCreate(DonorBase):
    """
    Data accepted when registering a donor.

    donor_code is intentionally excluded because BloodLink
    generates it automatically.
    """

    pass


# ==========================================================
# UPDATE DONOR
# ==========================================================

class DonorUpdate(SchemaBase):
    """Fields that may be changed for an existing donor."""

    full_name: str | None = Field(
        default=None,
        min_length=1,
        max_length=200,
    )

    blood_group: str | None = Field(
        default=None,
        min_length=1,
        max_length=5,
    )

    gender: str | None = Field(
        default=None,
        max_length=20,
    )

    date_of_birth: date | None = None

    phone: str | None = Field(
        default=None,
        max_length=30,
    )

    email: str | None = Field(
        default=None,
        max_length=255,
    )

    class_department: str | None = Field(
        default=None,
        max_length=150,
    )

    district: str | None = Field(
        default=None,
        max_length=100,
    )

    city: str | None = Field(
        default=None,
        max_length=100,
    )

    address: str | None = None

    latitude: Decimal | None = Field(
        default=None,
        max_digits=9,
        decimal_places=6,
    )

    longitude: Decimal | None = Field(
        default=None,
        max_digits=9,
        decimal_places=6,
    )

    weight: Decimal | None = Field(
        default=None,
        max_digits=5,
        decimal_places=2,
    )

    hb_above_12_5: str | None = Field(
        default=None,
        max_length=20,
    )

    regular_medication: str | None = Field(
        default=None,
        max_length=20,
    )

    bp_normal: str | None = Field(
        default=None,
        max_length=20,
    )

    medical_conditions: str | None = None

    last_donation_date: date | None = None

    total_donations: int | None = Field(
        default=None,
        ge=0,
    )

    status: str | None = Field(
        default=None,
        min_length=1,
        max_length=50,
    )


# ==========================================================
# DONOR RESPONSE
# ==========================================================

class DonorResponse(DonorBase):
    """Complete donor record returned by BloodLink."""

    id: int

    donor_code: str

    created_at: datetime

    updated_at: datetime

# ==========================================================
# BLOOD REQUEST SCHEMAS
# ==========================================================

class BloodRequestBase(SchemaBase):
    """
    Shared fields for BloodLink blood requests.

    These fields represent the information normally received
    from a patient, bystander, hospital, or blood requester.
    """

    # ======================================================
    # PERSON / CASE DETAILS
    # ======================================================

    patient_name: str = Field(
        min_length=1,
        max_length=200,
    )

    case_details: str = Field(
        min_length=1,
        max_length=255,
    )


    # ======================================================
    # BLOOD REQUIREMENT
    # ======================================================

    blood_group: str = Field(
        min_length=1,
        max_length=5,
    )

    units_required: int = Field(
        gt=0,
        le=20,
    )

    required_date: date


    # ======================================================
    # INTERNAL URGENCY
    # ======================================================

    priority: str = Field(
        min_length=1,
        max_length=50,
    )


    # ======================================================
    # HOSPITAL DETAILS
    # ======================================================

    hospital_name: str = Field(
        min_length=1,
        max_length=200,
    )

    hospital_location: str = Field(
        min_length=1,
        max_length=255,
    )


    # ======================================================
    # BYSTANDER / CONTACT DETAILS
    # ======================================================

    contact_person: str = Field(
        min_length=1,
        max_length=200,
    )

    contact_phone: str = Field(
        min_length=1,
        max_length=30,
    )


    # ======================================================
    # OPTIONAL INFORMATION
    # ======================================================

    additional_notes: str | None = None

class MatchResult(BaseModel):
    rank: int
    score: int
    donor_id: int
    donor_code: str
    donor_name: str
    blood_group: str
    phone: str | None
    email: str | None
    status: str
# ==========================================================
# CREATE BLOOD REQUEST
# ==========================================================

class BloodRequestCreate(BloodRequestBase):
    """
    Data accepted when creating a new blood request.

    Status and created_by are controlled by the backend
    and must not be trusted from the browser.
    """

    pass


# ==========================================================
# UPDATE BLOOD REQUEST
# ==========================================================

class BloodRequestUpdate(SchemaBase):
    """Fields that may be changed on an existing blood request."""

    patient_name: str | None = Field(
        default=None,
        min_length=1,
        max_length=200,
    )

    case_details: str | None = Field(
        default=None,
        min_length=1,
        max_length=255,
    )

    blood_group: str | None = Field(
        default=None,
        min_length=1,
        max_length=5,
    )

    units_required: int | None = Field(
        default=None,
        gt=0,
        le=20,
    )

    required_date: date | None = None

    priority: str | None = Field(
        default=None,
        min_length=1,
        max_length=50,
    )

    status: str | None = Field(
        default=None,
        min_length=1,
        max_length=50,
    )

    hospital_name: str | None = Field(
        default=None,
        min_length=1,
        max_length=200,
    )

    hospital_location: str | None = Field(
        default=None,
        min_length=1,
        max_length=255,
    )

    contact_person: str | None = Field(
        default=None,
        min_length=1,
        max_length=200,
    )

    contact_phone: str | None = Field(
        default=None,
        min_length=1,
        max_length=30,
    )

    additional_notes: str | None = None

# ==========================================================
# BLOOD REQUEST STATUS UPDATE
# ==========================================================

class BloodRequestStatusUpdate(SchemaBase):
    """Status change submitted for an existing blood request."""

    status: str = Field(
        min_length=1,
        max_length=50,
    )
# ==========================================================
# BLOOD REQUEST RESPONSE
# ==========================================================

class BloodRequestResponse(BloodRequestBase):
    """Blood request returned by the BloodLink API."""

    id: int

    status: str

    created_by: int

    created_at: datetime
class DonationHistoryBase(SchemaBase):
    """Fields shared by donation history create and response schemas."""

    donor_id: int = Field(gt=0)
    blood_request_id: int = Field(gt=0)
    hospital_name: str = Field(min_length=1, max_length=200)
    donation_date: date
    remarks: str | None = None
    recorded_by: int = Field(gt=0)


class DonationHistoryCreate(DonationHistoryBase):
    """Fields required to create a donation history record."""


class DonationHistoryUpdate(SchemaBase):
    """Fields that may be supplied when updating a donation record."""

    donor_id: int | None = Field(default=None, gt=0)
    blood_request_id: int | None = Field(default=None, gt=0)
    hospital_name: str | None = Field(default=None, min_length=1, max_length=200)
    donation_date: date | None = None
    remarks: str | None = None
    recorded_by: int | None = Field(default=None, gt=0)


class DonationHistoryResponse(DonationHistoryBase):
    """Donation history representation returned by the application."""

    id: int
    created_at: datetime


class NotificationBase(SchemaBase):
    """Fields shared by notification create and response schemas."""

    blood_request_id: int = Field(gt=0)
    donor_id: int = Field(gt=0)
    notification_status: str = Field(min_length=1, max_length=50)
    response: str | None = Field(default=None, max_length=100)


class NotificationCreate(NotificationBase):
    """Fields required to create a notification record."""


class NotificationUpdate(SchemaBase):
    """Fields that may be supplied when updating a notification record."""

    notification_status: str | None = Field(
        default=None,
        min_length=1,
        max_length=50,
    )
    response: str | None = Field(default=None, max_length=100)
    responded_at: datetime | None = None


class NotificationResponse(NotificationBase):
    """Notification representation returned by the application."""

    id: int
    sent_at: datetime
    responded_at: datetime | None
# ==========================================================
# DONOR MATCHING API SCHEMAS
# ==========================================================

from pydantic import BaseModel


class FindMatchRequest(BaseModel):
    """
    Request body for finding compatible donors.
    """

    blood_request_id: int


class SendNotificationRequest(BaseModel):
    """
    Request body for sending notification emails.
    """

    blood_request_id: int

    donor_ids: list[int]