"""API routes for BloodLink donor management."""

from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.database import crud
from backend.database.database import get_db
from backend.database.schemas import (
    DonorCreate,
    DonorResponse,
    DonorUpdate,
)
from io import BytesIO
from backend.services.donor_import_service import (
    import_donors_from_excel,
)

from fastapi.responses import StreamingResponse
from openpyxl import Workbook
from openpyxl.styles import Font
from fastapi import UploadFile, File
from zipfile import BadZipFile

from openpyxl import load_workbook  
# ==========================================================
# AUTHENTICATION
# ==========================================================

from backend.auth.dependencies import require_administrator
from backend.database.models import User
from backend.database.donor_profile import DonorProfile
from backend.services import donor_eligibility_service

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


def validate_deferral_update(donor, donor_data: DonorUpdate) -> None:
    """Normalize a donor availability update and enforce complete deferrals."""
    supplied = donor_data.model_fields_set
    if "status" in supplied and donor_data.status is not None:
        normalized_status = donor_data.status.strip().title()
        if normalized_status not in donor_eligibility_service.ALLOWED_AVAILABILITY_STATUSES:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="Donor status must be Available, Unavailable, or Deferred.",
            )
        donor_data.status = normalized_status

    if "deferral_reason" in supplied and donor_data.deferral_reason is not None:
        donor_data.deferral_reason = " ".join(donor_data.deferral_reason.split()) or None

    target_status = donor_data.status if "status" in supplied else donor.status
    target_date = donor_data.deferred_until if "deferred_until" in supplied else donor.deferred_until
    target_reason = donor_data.deferral_reason if "deferral_reason" in supplied else donor.deferral_reason

    if "deferred_until" in supplied and donor_data.deferred_until is not None:
        donor_data.status = donor_eligibility_service.DEFERRED
        target_status = donor_eligibility_service.DEFERRED

    if target_status == donor_eligibility_service.DEFERRED:
        if target_date is None or target_date <= date.today():
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="A deferred donor requires a future next-eligible date.",
            )
        if not target_reason:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="A deferred donor requires a deferral reason.",
            )
        donor_data.status = donor_eligibility_service.DEFERRED
        return

    if "status" in supplied:
        # An explicit manual restoration or indefinite unavailability ends any
        # active time-bound deferral while leaving donation history untouched.
        donor_data.deferred_until = None
        donor_data.deferral_reason = None
    elif "deferred_until" in supplied or "deferral_reason" in supplied:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Set status to Deferred when recording deferral details.",
        )


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
    current_user: User = Depends(require_administrator),
) -> DonorResponse:
    """Register a new donor in BloodLink."""

    # ------------------------------------------------------
    # Normalize and validate blood group
    # ------------------------------------------------------

    donor_data.blood_group = validate_blood_group(
        donor_data.blood_group
    )

    donor_data.status = donor_data.status.strip().title()
    if donor_data.status not in {
        donor_eligibility_service.AVAILABLE,
        donor_eligibility_service.UNAVAILABLE,
    }:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="New donors must start as Available or Unavailable. Add a dated deferral after registration.",
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
    current_user: User = Depends(require_administrator),
) -> list[DonorResponse]:
    """Return all donor records."""

    donor_eligibility_service.restore_expired_deferrals(database_session)

    return crud.get_donors(
        database_session
    )


# ==========================================================
# EXPORT DONORS TO EXCEL
# ==========================================================

@router.get("/export")
def export_donors(
    database_session: Session = Depends(get_db),
    current_user: User = Depends(require_administrator),
):
    """
    Export all donor records as an Excel workbook.
    """

    donor_eligibility_service.restore_expired_deferrals(database_session)
    donors = crud.get_donors(database_session)

    workbook = Workbook()
    worksheet = workbook.active
    worksheet.title = "Donors"

    headers = [
        "Donor Code",
        "Full Name",
        "Blood Group",
        "Gender",
        "Date of Birth",
        "Phone",
        "Email",
        "Department",
        "District",
        "City",
        "Weight",
        "Status",
        "Next Eligible Date",
        "Deferral Reason",
        "Donor Pause Until",
        "Travel Radius (km)",
        "Contact Window Start",
        "Contact Window End",
        "Last Donation",
        "Total Donations",
    ]

    worksheet.append(headers)

    for cell in worksheet[1]:
        cell.font = Font(bold=True)

    for donor in donors:

        worksheet.append([
            donor.donor_code,
            donor.full_name,
            donor.blood_group,
            donor.gender,
            donor.date_of_birth,
            donor.phone,
            donor.email,
            donor.class_department,
            donor.district,
            donor.city,
            donor.weight,
            donor.status,
            donor.deferred_until,
            donor.deferral_reason,
            donor.availability_paused_until,
            donor.travel_radius_km,
            donor.contact_window_start,
            donor.contact_window_end,
            donor.last_donation_date,
            donor.total_donations,
        ])

    for column in worksheet.columns:

        length = max(
            len(str(cell.value or ""))
            for cell in column
        )

        worksheet.column_dimensions[
            column[0].column_letter
        ].width = length + 3

    stream = BytesIO()

    from backend.security.exports import protect_workbook
    protect_workbook(workbook)
    workbook.save(stream)

    stream.seek(0)

    return StreamingResponse(
        stream,
        media_type=(
            "application/vnd.openxmlformats-officedocument."
            "spreadsheetml.sheet"
        ),
        headers={
            "Content-Disposition":
                'attachment; filename="bloodlink_donors.xlsx"'
        },
    )

# ==========================================================
# IMPORT DONORS
# ==========================================================

@router.post("/import")
async def import_donors(
    file: UploadFile = File(...),
    database_session: Session = Depends(get_db),
    current_user: User = Depends(require_administrator),
):
    """
    Import donors from an Excel workbook.
    """

    if not (file.filename or "").lower().endswith(".xlsx"):
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Upload an .xlsx workbook.",
        )
    contents = await file.read(10 * 1024 * 1024 + 1)
    if not contents or len(contents) > 10 * 1024 * 1024:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="Workbook must be between 1 byte and 10 MB.")

    try:
        summary = import_donors_from_excel(database_session, contents)
    except BadZipFile as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid Excel workbook.",
        ) from error
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(error),
        ) from error

    return {
        "message": "Import completed successfully.",
        "total_rows": summary.total_rows,
        "imported": summary.imported,
        "duplicates": summary.duplicates,
        "skipped": summary.skipped,
        "errors": summary.errors,
    }
# ==========================================================
# GET ONE DONOR
# ==========================================================

@router.get("/{donor_id}/profile")
def get_donor_profile(
    donor_id: int,
    database_session: Session = Depends(get_db),
    _: User = Depends(require_administrator),
) -> dict:
    """Return the structured status profile without changing legacy donor APIs."""
    donor = crud.get_donor_by_id(database_session, donor_id)
    if donor is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Donor not found.")
    profile = donor.profile
    if profile is None:
        return {"donor_id": donor_id, "profile": None}
    fields = [column.name for column in DonorProfile.__table__.columns if column.name not in {"id", "donor_id"}]
    return {"donor_id": donor_id, "profile": {name: getattr(profile, name) for name in fields}}

@router.get(
    "/{donor_id}",
    response_model=DonorResponse,
)
def get_donor(
    donor_id: int,
    database_session: Session = Depends(get_db),
    current_user: User = Depends(require_administrator),
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

    donor_eligibility_service.restore_donor_if_due(database_session, donor)
    return donor


# ==========================================================
# DELETE DONOR
# ==========================================================

@router.delete(
    "/{donor_id}",
    status_code=status.HTTP_200_OK,
)
def delete_donor(
    donor_id: int,
    database_session: Session = Depends(get_db),
    current_user: User = Depends(require_administrator),
) -> dict:
    """Delete an existing donor."""

    donor = crud.get_donor_by_id(
        database_session,
        donor_id,
    )

    if donor is None:

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Donor not found.",
        )

    donor_eligibility_service.restore_donor_if_due(database_session, donor)

    deletion = crud.delete_donor(
        database_session,
        donor,
    )

    return {
        "message": "Donor deleted successfully.",
        **deletion,
    }
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
    current_user: User = Depends(require_administrator),
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

    donor_eligibility_service.restore_donor_if_due(database_session, donor)

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

    validate_deferral_update(donor, donor_data)

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
