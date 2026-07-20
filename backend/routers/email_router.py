"""
==========================================================
Email Router
==========================================================

Handles donor responses received through email links.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.database.database import get_db
from backend.database import crud
from fastapi import Request
from fastapi.templating import Jinja2Templates



router = APIRouter(
    prefix="/email",
    tags=["Email"],
)
templates = Jinja2Templates(
    directory="backend/templates",
)
# ==========================================================
# ACCEPT DONATION
# ==========================================================

@router.get("/accept/{token}")
def accept_donation(
    request: Request,
    token: str,
    database_session: Session = Depends(get_db),

):
    """
    Accept a blood donation request.
    """

    email_token = crud.get_email_token(
        database_session,
        token,
    )

    if email_token is None:
        raise HTTPException(
            status_code=404,
            detail="Invalid email token.",
        )

    if email_token.used:

        return templates.TemplateResponse(
            request=request,
            name="already_used.html",
            context={},
            status_code=200,
        )

    if crud.email_token_expired(email_token):

        return templates.TemplateResponse(
            request=request,
            name="expired.html",
            context={},
            status_code=200,
        )
    recipient = crud.get_notification_recipient_by_token(
        database_session,
        email_token.id,
    )

    if recipient is None:
        raise HTTPException(
            status_code=404,
            detail="Recipient not found.",
        )

    crud.update_notification_recipient_status(
        database_session,
        recipient,
        "ACCEPTED",
    )
    crud.create_donor_response(
        database_session=database_session,
        email_token=email_token,
        response="ACCEPTED",
    )

    crud.mark_email_token_used(
        database_session,
        email_token,
    )

    crud.refresh_notification_statistics(
        database_session,
        recipient.notification,
    )
    # ---------------------------------------------------------
    # Automatically move the Blood Request to In Progress
    # ---------------------------------------------------------

    blood_request = recipient.notification.blood_request

    if blood_request.status == "Pending":

        crud.update_blood_request_status(
            database_session=database_session,
            blood_request=blood_request,
            new_status="In Progress",
        )
    return templates.TemplateResponse(
        request=request,
        name="accepted.html",
        context={
            "message": "Thank you for accepting the donation request.",
        },
    )
# ==========================================================
# DECLINE DONATION
# ==========================================================

@router.get("/decline/{token}")
def decline_donation(
    request: Request,
    token: str,
    database_session: Session = Depends(
        get_db,
    ),
):
    """
    Decline a blood donation request.
    """

    email_token = crud.get_email_token(
        database_session,
        token,
    )

    if email_token is None:
        raise HTTPException(
            status_code=404,
            detail="Invalid email token.",
        )

    if email_token.used:
        raise HTTPException(
            status_code=400,
            detail="This link has already been used.",
        )

    if crud.email_token_expired(email_token):
        raise HTTPException(
            status_code=400,
            detail="Email token has expired.",
        )

    recipient = crud.get_notification_recipient_by_token(
        database_session,
        email_token.id,
    )

    if recipient is None:
        raise HTTPException(
            status_code=404,
            detail="Recipient not found.",
        )

    crud.update_notification_recipient_status(
        database_session,
        recipient,
        "DECLINED",
    )

    crud.create_donor_response(
        database_session=database_session,
        email_token=email_token,
        response="DECLINED",
    )

    crud.mark_email_token_used(
        database_session,
        email_token,
    )

    crud.refresh_notification_statistics(
        database_session,
        recipient.notification,
    )

    return templates.TemplateResponse(
        request=request,
        name="declined.html",
        context={
            "message": "Your response has been recorded.",
        },
    )