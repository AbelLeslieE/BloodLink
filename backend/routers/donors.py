"""API routes for BloodLink donor management."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.database import crud
from backend.database.database import get_db
from backend.database.schemas import (
    DonorCreate,
    DonorResponse,
    DonorUpdate,
)
# ==========================================================
# AUTHENTICATION
# ==========================================================

from backend.auth.dependencies import require_authentication
from backend.database.models import User

# ==========================================================
# ROUTER
# ==========================================================

router = APIRouter(
    prefix="/api/donors",
    tags=["Donors"],
)


# ==========================================================
# VALIDATION HELPERS
# ==========================================================

ALLOWED_BLOOD_GROUPS = {
    "A+",
    "A-",
    "B+",
    "B-",
    "AB+",
    "AB-",
    "O+",
    "O-",
}

ALLOWED_HEALTH_VALUES = {
    "Yes",
    "No",
    "Not Recorded",
}


def validate_blood_group(
    blood_group: str,
) -> str:
    """Validate and normalize a donor blood group."""

    normalized = blood_group.strip().upper()

    if normalized not in ALLOWED_BLOOD_GROUPS:

        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid blood group.",
        )

    return normalized


def validate_health_value(
    value: str,
    field_name: str,
) -> str:
    """
    Validate health eligibility values.

    Manual registration will normally send Yes or No.
    Not Recorded remains valid for imported historical data.
    """

    normalized_values = {
        "yes": "Yes",
        "no": "No",
        "not recorded": "Not Recorded",
    }

    normalized = normalized_values.get(
        value.strip().lower()
    )

    if normalized not in ALLOWED_HEALTH_VALUES:

        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                f"{field_name} must be "
                "Yes, No, or Not Recorded."
            ),
        )

    return normalized


# ==========================================================
# CREATE DONOR
# ==========================================================

@router.post(
    "",
    response_model=DonorResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_donor(
    donor_data: DonorCreate,
    database_session: Session = Depends(get_db),
    current_user: User = Depends(require_authentication),
) -> DonorResponse:
    """Register a new donor in BloodLink."""

    # ------------------------------------------------------
    # Normalize and validate blood group
    # ------------------------------------------------------

    donor_data.blood_group = validate_blood_group(
        donor_data.blood_group
    )

    # ------------------------------------------------------
    # Validate health questions
    # ------------------------------------------------------

    donor_data.hb_above_12_5 = validate_health_value(
        donor_data.hb_above_12_5,
        "Hb > 12.5",
    )

    donor_data.regular_medication = validate_health_value(
        donor_data.regular_medication,
        "Regular medication",
    )

    donor_data.bp_normal = validate_health_value(
        donor_data.bp_normal,
        "BP level normal",
    )

    # ------------------------------------------------------
    # Duplicate phone check
    # ------------------------------------------------------

    if donor_data.phone:

        existing_phone = crud.get_donor_by_phone(
            database_session,
            donor_data.phone,
        )

        if existing_phone:

            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    "A donor with this phone number "
                    "already exists."
                ),
            )

    # ------------------------------------------------------
    # Duplicate email check
    # ------------------------------------------------------

    if donor_data.email:

        existing_email = crud.get_donor_by_email(
            database_session,
            donor_data.email,
        )

        if existing_email:

            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    "A donor with this email address "
                    "already exists."
                ),
            )

    return crud.create_donor(
        database_session,
        donor_data,
    )


# ==========================================================
# GET ALL DONORS
# ==========================================================

@router.get(
    "",
    response_model=list[DonorResponse],
)
def list_donors(
    database_session: Session = Depends(get_db),
    current_user: User = Depends(require_authentication),
) -> list[DonorResponse]:
    """Return all donor records."""

    return crud.get_donors(
        database_session
    )


# ==========================================================
# GET ONE DONOR
# ==========================================================

@router.get(
    "/{donor_id}",
    response_model=DonorResponse,
)
def get_donor(
    donor_id: int,
    database_session: Session = Depends(get_db),
    current_user: User = Depends(require_authentication),
) -> DonorResponse:
    """Return one donor by database ID."""

    donor = crud.get_donor_by_id(
        database_session,
        donor_id,
    )

    if donor is None:

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Donor not found.",
        )

    return donor


# ==========================================================
# UPDATE DONOR
# ==========================================================

@router.patch(
    "/{donor_id}",
    response_model=DonorResponse,
)
def update_donor(
    donor_id: int,
    donor_data: DonorUpdate,
    database_session: Session = Depends(get_db),
    current_user: User = Depends(require_authentication),
) -> DonorResponse:
    """Update an existing donor."""

    donor = crud.get_donor_by_id(
        database_session,
        donor_id,
    )

    if donor is None:

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Donor not found.",
        )

    # ------------------------------------------------------
    # Validate blood group when supplied
    # ------------------------------------------------------

    if donor_data.blood_group is not None:

        donor_data.blood_group = validate_blood_group(
            donor_data.blood_group
        )

        # ------------------------------------------------------
    # Validate health values when supplied
    # ------------------------------------------------------

    if donor_data.hb_above_12_5 is not None:

        donor_data.hb_above_12_5 = validate_health_value(
            donor_data.hb_above_12_5,
            "Hb > 12.5",
        )

    if donor_data.regular_medication is not None:

        donor_data.regular_medication = validate_health_value(
            donor_data.regular_medication,
            "Regular medication",
        )

    if donor_data.bp_normal is not None:

        donor_data.bp_normal = validate_health_value(
            donor_data.bp_normal,
            "BP level normal",
        )

    # ------------------------------------------------------
    # Duplicate phone check
    # ------------------------------------------------------

    if donor_data.phone is not None:

        normalized_phone = (
            donor_data.phone.strip()
            if donor_data.phone
            else None
        )

        donor_data.phone = normalized_phone

        if normalized_phone:

            existing_phone = crud.get_donor_by_phone(
                database_session,
                normalized_phone,
            )

            if (
                existing_phone is not None
                and existing_phone.id != donor.id
            ):

                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=(
                        "A donor with this phone number "
                        "already exists."
                    ),
                )

    # ------------------------------------------------------
    # Duplicate email check
    # ------------------------------------------------------

    if donor_data.email is not None:

        normalized_email = (
            donor_data.email.strip()
            if donor_data.email
            else None
        )

        donor_data.email = normalized_email

        if normalized_email:

            existing_email = crud.get_donor_by_email(
                database_session,
                normalized_email,
            )

            if (
                existing_email is not None
                and existing_email.id != donor.id
            ):

                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=(
                        "A donor with this email address "
                        "already exists."
                    ),
                )

    # ------------------------------------------------------
    # SAVE UPDATE
    # ------------------------------------------------------

    return crud.update_donor(
        database_session,
        donor,
        donor_data,
    )