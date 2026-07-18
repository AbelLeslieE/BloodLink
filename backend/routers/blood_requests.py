"""Blood Request API endpoints for BloodLink."""

from __future__ import annotations

from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)

from sqlalchemy.orm import Session

from backend.auth.dependencies import require_authentication
from backend.database import crud
from backend.database.database import get_db
from backend.database.models import User
from backend.database.schemas import (
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
        Depends(require_authentication),
    ],

) -> BloodRequestResponse:
    """Create a blood request for the authenticated user."""

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
        Depends(require_authentication),
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
        Depends(require_authentication),
    ],

) -> BloodRequestResponse:
    """
    Update the status of an existing blood request.

    Allowed statuses:
    - Pending
    - In Progress
    - Fulfilled
    - Cancelled
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

    allowed_statuses = {
        "Pending",
        "In Progress",
        "Fulfilled",
        "Cancelled",
    }


    if status_data.status not in allowed_statuses:

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Invalid blood request status. "
                "Allowed statuses are Pending, "
                "In Progress, Fulfilled, and Cancelled."
            ),
        )


    # ======================================================
    # 3. UPDATE DATABASE
    # ======================================================

    return crud.update_blood_request_status(
        database_session=database_session,
        blood_request=blood_request,
        new_status=status_data.status,
    )