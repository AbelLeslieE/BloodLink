"""Blood Request API endpoints for BloodLink."""

from __future__ import annotations

from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)

from sqlalchemy import delete, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from backend.auth.dependencies import require_administrator
from backend.database import crud
from backend.database.database import get_db
from backend.database.models import DonationHistory, SavedMatch, User
from backend.database.schemas import (
    BloodRequestCompleteRequest,
    BloodRequestCreate,
    BloodRequestResponse,
    BloodRequestStatusUpdate,
)


# ==========================================================
# ROUTER
# ==========================================================

router = APIRouter(
    prefix="/api/blood-requests",
    tags=["blood requests"],
)

# Keep these values in one place so invalid requests do not silently become
# impossible to match or disappear from the donor portal.
ALLOWED_BLOOD_GROUPS = {"A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"}
ALLOWED_PRIORITIES = {"Normal", "Urgent", "Emergency"}
ALLOWED_STATUSES = {
    "Pending",
    "Open",
    "Sent",
    "In Progress",
    "Donor Responded",
    "Awaiting Donation",
    "Donation Completed",
    "Points Awarded",
    "Fulfilled",
    "Closed",
    "Cancelled",
}


def _normalise_blood_group(value: str) -> str:
    return value.strip().upper().replace(" ", "")


def _validate_request_values(blood_group: str, priority: str) -> tuple[str, str]:
    normalised_group = _normalise_blood_group(blood_group)
    normalised_priority = priority.strip().title()
    if normalised_group not in ALLOWED_BLOOD_GROUPS:
        raise HTTPException(status_code=422, detail="Blood group must be one of A+, A-, B+, B-, AB+, AB-, O+, or O-.")
    if normalised_priority not in ALLOWED_PRIORITIES:
        raise HTTPException(status_code=422, detail="Priority must be Normal, Urgent, or Emergency.")
    return normalised_group, normalised_priority


# ==========================================================
# CREATE BLOOD REQUEST
# ==========================================================

@router.post(
    "",
    response_model=BloodRequestResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_blood_request(
    request_data: BloodRequestCreate,

    database_session: Annotated[
        Session,
        Depends(get_db),
    ],

    current_user: Annotated[
        User,
        Depends(require_administrator),
    ],

) -> BloodRequestResponse:
    """Create a blood request for the authenticated user."""

    request_data.blood_group, request_data.priority = _validate_request_values(
        request_data.blood_group,
        request_data.priority,
    )

    return crud.create_blood_request(
        database_session=database_session,
        request_data=request_data,
        created_by=current_user.id,
    )


# ==========================================================
# LIST BLOOD REQUESTS
# ==========================================================

@router.get(
    "",
    response_model=list[BloodRequestResponse],
)
def list_blood_requests(

    database_session: Annotated[
        Session,
        Depends(get_db),
    ],

    _: Annotated[
        User,
        Depends(require_administrator),
    ],

) -> list[BloodRequestResponse]:
    """Return all blood requests ordered newest first."""

    return crud.get_blood_requests(
        database_session
    )
# ==========================================================
# UPDATE BLOOD REQUEST STATUS
# ==========================================================

@router.patch(
    "/{request_id}/status",
    response_model=BloodRequestResponse,
)
def update_blood_request_status(
    request_id: int,

    status_data: BloodRequestStatusUpdate,

    database_session: Annotated[
        Session,
        Depends(get_db),
    ],

    _: Annotated[
        User,
        Depends(require_administrator),
    ],

) -> BloodRequestResponse:
    """
    Update the status of an existing blood request.

    The lifecycle supports pending, contact, donation, completion, and closure
    states while preventing arbitrary status values from entering the system.
    """

    # ======================================================
    # 1. FIND BLOOD REQUEST
    # ======================================================

    blood_request = crud.get_blood_request_by_id(
        database_session,
        request_id,
    )


    if blood_request is None:

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Blood request not found.",
        )


    # ======================================================
    # 2. VALIDATE STATUS
    # ======================================================

    requested_status = status_data.status.strip().title()

    if requested_status not in ALLOWED_STATUSES:

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Invalid blood request status."
            ),
        )


    # ======================================================
    # 3. UPDATE DATABASE
    # ======================================================

    return crud.update_blood_request_status(
        database_session=database_session,
        blood_request=blood_request,
        new_status=requested_status,
    )


# ==========================================================
# DELETE BLOOD REQUEST
# ==========================================================

@router.delete(
    "/{request_id}",
)
def delete_blood_request(
    request_id: int,

    database_session: Annotated[
        Session,
        Depends(get_db),
    ],

    _: Annotated[
        User,
        Depends(require_administrator),
    ],

) -> dict:
    """Delete a mistaken request that has no confirmed donations."""

    blood_request = crud.get_blood_request_by_id(
        database_session,
        request_id,
    )

    if blood_request is None:

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Blood request not found.",
        )

    has_confirmed_donations = database_session.scalar(
        select(DonationHistory.id).where(
            DonationHistory.blood_request_id == request_id
        )
    )

    if has_confirmed_donations is not None:

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "A request with confirmed donations cannot be deleted. "
                "Mark it completed instead."
            ),
        )

    try:

        # Saved matches have no database-level relationship to a request, so
        # remove them explicitly before deleting its related campaign data.
        database_session.execute(
            delete(SavedMatch).where(
                SavedMatch.blood_request_id == request_id
            )
        )

        database_session.delete(blood_request)
        database_session.commit()

    except SQLAlchemyError as error:

        database_session.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "Unable to delete this blood request because it is still "
                "referenced by related records."
            ),
        ) from error

    return {
        "success": True,
        "deleted_request_id": request_id,
    }


# ==========================================================
# COMPLETE BLOOD REQUEST
# ==========================================================

@router.post(
    "/{request_id}/complete",
    response_model=BloodRequestResponse,
)
def complete_blood_request(
    request_id: int,

    request_data: BloodRequestCompleteRequest,

    database_session: Annotated[
        Session,
        Depends(get_db),
    ],

    administrator: Annotated[
        User,
        Depends(require_administrator),
    ],

) -> BloodRequestResponse:
    """
    Complete a blood request by recording a donation
    and marking the request as fulfilled.
    """

    # ------------------------------------------------------
    # Find blood request
    # ------------------------------------------------------

    blood_request = crud.get_blood_request_by_id(
        database_session,
        request_id,
    )

    if blood_request is None:

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Blood request not found.",
        )

    # ------------------------------------------------------
    # Complete the request using either a registered donor or the supplied
    # external donor name. The request schema ensures exactly one source.
    # ------------------------------------------------------

    if request_data.external_donor_name:
        try:
            return crud.complete_blood_request_with_external_donor(
                database_session=database_session,
                blood_request=blood_request,
                external_donor_name=request_data.external_donor_name,
                recorded_by=administrator.id,
                donation_type=request_data.donation_type,
                remarks=request_data.remarks,
            )
        except ValueError as error:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(error),
            ) from error

    donor = crud.get_donor_by_id(
        database_session,
        request_data.donor_id,
    )
    if donor is None:

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Donor not found.",
        )

    # ------------------------------------------------------
    # Complete donation
    # ------------------------------------------------------

    try:

        return crud.complete_blood_request(
            database_session=database_session,
            blood_request=blood_request,
            donor=donor,
            recorded_by=administrator.id,
            donation_type=request_data.donation_type,
            remarks=request_data.remarks,
        )

    except ValueError as error:

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        )
