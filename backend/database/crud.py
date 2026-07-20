"""Reserved location for database CRUD operations."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime, timezone
from typing import Any, TypeVar

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from backend.database.models import BloodRequest, Donor, User
from backend.database.notification import Notification
from backend.database.notification_recipient import NotificationRecipient
from backend.database.email_token import EmailToken
from backend.database.donor_response import DonorResponse

from backend.database.schemas import (
    BloodRequestCreate,
    DonorCreate,
    DonorUpdate,
    UserCreate,
)


ModelType = TypeVar("ModelType")


def create_record(
    database_session: Session,
    model_type: type[ModelType],
    values: Mapping[str, Any],
) -> ModelType:
    """Create a database record.

    TODO: Add approved persistence logic for the supplied model and values.
    """
    raise NotImplementedError("CRUD implementation will be added in a later phase.")


def read_record(
    database_session: Session,
    model_type: type[ModelType],
    record_id: int,
) -> ModelType | None:
    """Read one database record by its identifier.

    TODO: Add approved lookup logic for the supplied model and identifier.
    """
    raise NotImplementedError("CRUD implementation will be added in a later phase.")


def update_record(
    database_session: Session,
    record: ModelType,
    values: Mapping[str, Any],
) -> ModelType:
    """Update an existing database record.

    TODO: Add approved update logic for the supplied record and values.
    """
    raise NotImplementedError("CRUD implementation will be added in a later phase.")


def delete_record(database_session: Session, record: ModelType) -> None:
    """Delete an existing database record.

    TODO: Add approved deletion logic for the supplied record.
    """
    raise NotImplementedError("CRUD implementation will be added in a later phase.")


def get_user_by_username(database_session: Session, username: str) -> User | None:
    """Return one volunteer account matching the supplied username."""
    statement = select(User).where(User.username == username)
    return database_session.scalar(statement)


def volunteer_exists(database_session: Session) -> bool:
    """Return whether at least one NSS volunteer account exists."""
    statement = select(User.id).limit(1)
    return database_session.scalar(statement) is not None


def create_user(
    database_session: Session,
    user_data: UserCreate,
) -> User:
    """Persist a user record whose password has already been securely hashed."""

    user = User(
        username=user_data.username,
        password_hash=user_data.password_hash,
        full_name=user_data.full_name,
        active=user_data.active,
    )

    database_session.add(user)

    _commit_and_refresh(
        database_session,
        user,
    )

    return user


def update_user_last_login(
    database_session: Session,
    user: User,
) -> User:
    """Record the time at which a volunteer successfully authenticated."""

    user.last_login = datetime.now(timezone.utc)

    _commit_and_refresh(
        database_session,
        user,
    )

    return user
# ==========================================================
# NOTIFICATION CRUD
# ==========================================================

def create_notification(
    database_session: Session,
    blood_request_id: int,
    title: str,
) -> Notification:
    """
    Create a notification campaign.
    """

    notification = Notification(
        blood_request_id=blood_request_id,
        title=title,
        status="ACTIVE",
    )

    database_session.add(notification)

    _commit_and_refresh(
        database_session,
        notification,
    )

    return notification


def get_notification_by_id(
    database_session: Session,
    notification_id: int,
) -> Notification | None:
    """
    Return one notification campaign.
    """

    statement = (
        select(Notification)
        .where(Notification.id == notification_id)
    )

    return database_session.scalar(statement)


def get_notifications(
    database_session: Session,
) -> list[Notification]:
    """
    Return all notification campaigns.
    """

    statement = (
        select(Notification)
        .order_by(Notification.created_at.desc())
    )

    return list(
        database_session.scalars(statement).all()
    )


# ==========================================================
# NOTIFICATION RECIPIENT CRUD
# ==========================================================

def create_notification_recipient(
    database_session: Session,
    notification_id: int,
    donor: Donor,
    distance: float,
) -> NotificationRecipient:
    """
    Create one recipient entry for a donor.
    """

    recipient = NotificationRecipient(
        notification_id=notification_id,
        donor_id=donor.id,
        email=donor.email,
        distance=distance,
        status="PENDING",
    )

    database_session.add(recipient)

    _commit_and_refresh(
        database_session,
        recipient,
    )

    return recipient


def get_notification_recipients(
    database_session: Session,
    notification_id: int,
) -> list[NotificationRecipient]:
    """
    Return all recipients belonging to a campaign.
    """

    statement = (
        select(NotificationRecipient)
        .where(
            NotificationRecipient.notification_id == notification_id
        )
        .order_by(NotificationRecipient.id)
    )

    return list(
        database_session.scalars(statement).all()
    )
# ==========================================================
# NOTIFICATION RECIPIENT STATUS
# ==========================================================

def get_notification_recipient_by_token(
    database_session: Session,
    email_token_id: int,
) -> NotificationRecipient | None:
    """
    Return one notification recipient using its email token.
    """

    statement = (
        select(NotificationRecipient)
        .where(
            NotificationRecipient.email_token_id == email_token_id
        )
    )

    return database_session.scalar(statement)


def update_notification_recipient_status(
    database_session: Session,
    recipient: NotificationRecipient,
    status: str,
) -> NotificationRecipient:
    """
    Update a recipient's response status.
    """

    recipient.status = status
    recipient.responded_at = datetime.now(timezone.utc)

    _commit_and_refresh(
        database_session,
        recipient,
    )

    return recipient
# ==========================================================
# NOTIFICATION CAMPAIGN STATISTICS
# ==========================================================

def refresh_notification_statistics(
    database_session: Session,
    notification: Notification,
) -> Notification:
    """
    Refresh notification statistics based on recipient responses.
    """

    recipients = get_notification_recipients(
        database_session,
        notification.id,
    )

    notification.total_sent = len(recipients)

    notification.accepted_count = sum(
        1 for recipient in recipients
        if recipient.status == "ACCEPTED"
    )

    notification.declined_count = sum(
        1 for recipient in recipients
        if recipient.status == "DECLINED"
    )

    notification.pending_count = sum(
        1 for recipient in recipients
        if recipient.status == "PENDING"
    )

    _commit_and_refresh(
        database_session,
        notification,
    )

    return notification
# ==========================================================
# EMAIL TOKEN CRUD
# ==========================================================

def create_email_token(
    database_session: Session,
    recipient: NotificationRecipient,
    token: str,
    expires_at: datetime,
) -> EmailToken:
    """
    Create and save an email token for a notification recipient.
    """

    email_token = EmailToken(
        token=token,
        expires_at=expires_at,
    )

    database_session.add(email_token)

    _commit_and_refresh(
        database_session,
        email_token,
    )

    recipient.email_token_id = email_token.id

    _commit_and_refresh(
        database_session,
        recipient,
    )

    return email_token

def get_email_token(
    database_session: Session,
    token: str,
) -> EmailToken | None:
    """
    Return an email token using the token string.
    """

    statement = (
        select(EmailToken)
        .where(
            EmailToken.token == token
        )
    )

    return database_session.scalar(statement)


def mark_email_token_used(
    database_session: Session,
    email_token: EmailToken,
) -> EmailToken:
    """
    Mark an email token as used.
    """

    email_token.used = True

    _commit_and_refresh(
        database_session,
        email_token,
    )

    return email_token


def email_token_expired(
    email_token: EmailToken,
) -> bool:
    """
    Return whether an email token has expired.

    Works correctly with both SQLite (naive datetime)
    and PostgreSQL (timezone-aware datetime).
    """

    expires_at = email_token.expires_at

    # SQLite returns naive datetimes
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(
            tzinfo=timezone.utc,
        )

    return (
        datetime.now(timezone.utc)
        >= expires_at
    )
# ==========================================================
# UPDATE BLOOD REQUEST STATUS (AUTO)
# ==========================================================

def update_blood_request_status(
    database_session,
    blood_request,
    new_status: str,
):
    """
    Update the status of a blood request.
    """

    blood_request.status = new_status

    database_session.add(
        blood_request,
    )

    database_session.commit()

    database_session.refresh(
        blood_request,
    )

    return blood_request
# ==========================================================
# DONOR RESPONSE CRUD
# ==========================================================

def create_donor_response(
    database_session: Session,
    email_token: EmailToken,
    response: str,
    remarks: str | None = None,
) -> DonorResponse:
    """
    Store a donor's response for a blood request.
    """

    recipient = get_notification_recipient_by_token(
        database_session,
        email_token.id,
    )

    if recipient is None:
        raise ValueError("Notification recipient not found.")

    donor_response = DonorResponse(
        email_token_id=email_token.id,
        donor_id=recipient.donor_id,
        blood_request_id=recipient.notification.blood_request_id,
        response=response,
        remarks=remarks,
    )

    database_session.add(donor_response)

    _commit_and_refresh(
        database_session,
        donor_response,
    )

    return donor_response
# ==========================================================
# DONOR CRUD
# ==========================================================


def generate_donor_code(
    database_session: Session,
) -> str:
    """
    Generate the next BloodLink donor code.

    Example:
        DNR0001
        DNR0002
        DNR0003

    The database ID is used to determine the next available
    sequence while the unique database constraint remains the
    final protection against duplicate donor codes.
    """

    statement = (
        select(Donor.id)
        .order_by(Donor.id.desc())
        .limit(1)
    )

    latest_id = database_session.scalar(statement)

    next_number = (latest_id or 0) + 1

    return f"DNR{next_number:04d}"


# ==========================================================
# CREATE DONOR
# ==========================================================


def create_donor(
    database_session: Session,
    donor_data: DonorCreate,
) -> Donor:
    """
    Create and save a donor record.

    The donor code is generated by BloodLink rather than
    being manually entered by the user.
    """

    donor_values = donor_data.model_dump(
        exclude={"donor_code"}
    )

    donor = Donor(
        donor_code=generate_donor_code(database_session),
        **donor_values,
    )

    database_session.add(donor)

    _commit_and_refresh(
        database_session,
        donor,
    )

    return donor


# ==========================================================
# GET ALL DONORS
# ==========================================================


def get_donors(
    database_session: Session,
) -> list[Donor]:
    """
    Return all donors.

    Newest donor records are returned first.
    """

    statement = (
        select(Donor)
        .order_by(Donor.id.desc())
    )

    return list(
        database_session.scalars(
            statement
        ).all()
    )


# ==========================================================
# GET DONOR BY ID
# ==========================================================


def get_donor_by_id(
    database_session: Session,
    donor_id: int,
) -> Donor | None:
    """Return one donor using the database ID."""

    statement = (
        select(Donor)
        .where(Donor.id == donor_id)
    )

    return database_session.scalar(statement)


# ==========================================================
# GET DONOR BY CODE
# ==========================================================


def get_donor_by_code(
    database_session: Session,
    donor_code: str,
) -> Donor | None:
    """Return one donor using the BloodLink donor code."""

    statement = (
        select(Donor)
        .where(Donor.donor_code == donor_code)
    )

    return database_session.scalar(statement)


# ==========================================================
# DUPLICATE CHECKS
# ==========================================================


def get_donor_by_phone(
    database_session: Session,
    phone: str,
) -> Donor | None:
    """
    Find a donor by phone number.

    Used for duplicate detection during manual registration
    and Excel import.
    """

    statement = (
        select(Donor)
        .where(Donor.phone == phone)
    )

    return database_session.scalar(statement)

def get_eligible_donors(
    database_session: Session,
    compatible_groups: list[str],
) -> list[Donor]:
    """
    Return available donors belonging to compatible blood groups.
    """

    statement = (
        select(Donor)
        .where(
            Donor.blood_group.in_(compatible_groups),
            Donor.status == "Available",
        )
    )

    return list(
        database_session.scalars(statement).all()
    )
def get_donor_by_email(
    database_session: Session,
    email: str,
) -> Donor | None:
    """
    Find a donor by email address.

    Used as an additional duplicate-detection mechanism.
    """

    statement = (
        select(Donor)
        .where(Donor.email == email)
    )

    return database_session.scalar(statement)


# ==========================================================
# UPDATE DONOR
# ==========================================================


def update_donor(
    database_session: Session,
    donor: Donor,
    donor_data: DonorUpdate,
) -> Donor:
    """
    Update only donor fields explicitly supplied by the client.

    Unspecified fields remain unchanged.
    """

    update_values = donor_data.model_dump(
        exclude_unset=True,
        exclude={"donor_code"},
    )

    for field_name, value in update_values.items():

        setattr(
            donor,
            field_name,
            value,
        )

    _commit_and_refresh(
        database_session,
        donor,
    )

    return donor
# ==========================================================
# DELETE DONOR
# ==========================================================

def delete_donor(
    database_session: Session,
    donor: Donor,
) -> None:
    """
    Permanently delete a donor record.
    """

    try:

        database_session.delete(donor)

        database_session.commit()

    except SQLAlchemyError:

        database_session.rollback()

        raise
# ==========================================================
# BLOOD REQUEST CRUD
# ==========================================================

def create_blood_request(
    database_session: Session,
    request_data: BloodRequestCreate,
    created_by: int,
) -> BloodRequest:
    """
    Create and save a new blood request.

    The authenticated user's ID is supplied separately so
    created_by cannot be controlled by frontend form data.
    """

    blood_request = BloodRequest(

        # --------------------------------------------------
        # Person / Case Details
        # --------------------------------------------------

        patient_name=request_data.patient_name,

        case_details=request_data.case_details,


        # --------------------------------------------------
        # Blood Requirement
        # --------------------------------------------------

        blood_group=request_data.blood_group,

        units_required=request_data.units_required,

        required_date=request_data.required_date,

        priority=request_data.priority,


        # --------------------------------------------------
        # Hospital Details
        # --------------------------------------------------

        hospital_name=request_data.hospital_name,

        hospital_location=request_data.hospital_location,


        # --------------------------------------------------
        # Bystander / Contact
        # --------------------------------------------------

        contact_person=request_data.contact_person,

        contact_phone=request_data.contact_phone,


        # --------------------------------------------------
        # Optional Information
        # --------------------------------------------------

        additional_notes=request_data.additional_notes,


        # --------------------------------------------------
        # BloodLink Managed Fields
        # --------------------------------------------------

        status="Pending",

        created_by=created_by,

    )

    database_session.add(
        blood_request
    )

    _commit_and_refresh(
        database_session,
        blood_request,
    )

    return blood_request


# ==========================================================
# GET ALL BLOOD REQUESTS
# ==========================================================

def get_blood_requests(
    database_session: Session,
) -> list[BloodRequest]:
    """
    Return all blood requests.

    Newest requests are returned first.
    """

    statement = (

        select(BloodRequest)

        .order_by(
            BloodRequest.created_at.desc()
        )

    )

    return list(

        database_session.scalars(
            statement
        ).all()

    )
# ==========================================================
# GET BLOOD REQUEST BY ID
# ==========================================================

def get_blood_request_by_id(
    database_session: Session,
    request_id: int,
) -> BloodRequest | None:
    """Return one blood request by its database ID."""

    statement = (
        select(BloodRequest)
        .where(
            BloodRequest.id == request_id
        )
    )

    return database_session.scalar(
        statement
    )
# ==========================================================
# BLOOD REQUEST STATUS UPDATE
# ==========================================================

def update_blood_request_status(
    database_session: Session,
    blood_request: BloodRequest,
    new_status: str,
) -> BloodRequest:
    """
    Update the status of an existing blood request
    and save the change permanently to the database.
    """

    blood_request.status = new_status

    _commit_and_refresh(
        database_session,
        blood_request,
    )

    return blood_request
def _commit_and_refresh(
    database_session: Session,
    record: ModelType,
) -> None:
    """Commit a database write and refresh the persisted record."""

    try:

        database_session.commit()

        database_session.refresh(
            record
        )

    except SQLAlchemyError:

        database_session.rollback()

        raise
