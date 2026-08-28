"""Public, token-protected donor responses to notification emails."""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from backend.database import crud
from backend.database.database import get_db
from backend.database.donor_response import DonorResponse
from backend.database.notification_recipient import NotificationRecipient


router = APIRouter(prefix="/email", tags=["Email"])
templates = Jinja2Templates(directory="backend/templates")


def _token_page(request: Request, token: str, decision: str, db: Session):
    email_token = crud.get_email_token(db, token)
    if email_token is None:
        raise HTTPException(status_code=404, detail="Invalid email token.")
    if email_token.used:
        return templates.TemplateResponse(request=request, name="already_used.html", context={})
    if crud.email_token_expired(email_token):
        return templates.TemplateResponse(request=request, name="expired.html", context={})
    return templates.TemplateResponse(
        request=request,
        name="response_confirmation.html",
        context={"action_url": f"/email/{decision.lower()}/{token}", "response": decision.title()},
    )


def _record_decision(db: Session, token: str, response: str) -> str:
    """Atomically persist a donor decision and refresh campaign statistics."""
    email_token = crud.get_email_token(db, token)
    if email_token is None:
        return "invalid"
    if email_token.used:
        return "used"
    if crud.email_token_expired(email_token):
        return "expired"
    recipient = db.scalar(select(NotificationRecipient).where(
        NotificationRecipient.email_token_id == email_token.id
    ))
    if recipient is None:
        return "invalid"

    existing = db.scalar(select(DonorResponse).where(
        DonorResponse.donor_id == recipient.donor_id,
        DonorResponse.blood_request_id == recipient.notification.blood_request_id,
    ))
    if existing is None:
        db.add(DonorResponse(
            email_token_id=email_token.id,
            donor_id=recipient.donor_id,
            blood_request_id=recipient.notification.blood_request_id,
            response=response,
        ))
    else:
        # Portal and email actions represent one decision for the same request.
        existing.email_token_id = email_token.id
        existing.response = response
        existing.responded_at = datetime.now(timezone.utc)

    recipient.status = response
    recipient.responded_at = datetime.now(timezone.utc)
    email_token.used = True
    notification = recipient.notification
    # Flush the decision before calculating aggregates; otherwise a session
    # configured without autoflush can report stale campaign counts.
    db.flush()
    recipients = crud.get_notification_recipients(db, notification.id)
    notification.total_sent = sum(item.status != "DELIVERY_FAILED" for item in recipients)
    notification.accepted_count = sum(item.status == "ACCEPTED" for item in recipients)
    notification.declined_count = sum(item.status == "DECLINED" for item in recipients)
    notification.pending_count = sum(item.status == "PENDING" for item in recipients)
    if response == "ACCEPTED" and notification.blood_request.status == "Pending":
        notification.blood_request.status = "In Progress"
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        return "used"
    except SQLAlchemyError:
        db.rollback()
        raise
    return "ok"


def _result_page(request: Request, outcome: str, accepted: bool):
    if outcome == "used":
        return templates.TemplateResponse(request=request, name="already_used.html", context={})
    if outcome == "expired":
        return templates.TemplateResponse(request=request, name="expired.html", context={})
    if outcome == "invalid":
        raise HTTPException(status_code=404, detail="Invalid email token.")
    return templates.TemplateResponse(
        request=request,
        name="accepted.html" if accepted else "declined.html",
        context={"message": "Thank you for accepting the donation request." if accepted else "Your response has been recorded."},
    )


@router.get("/accept/{token}")
def accept_donation_page(request: Request, token: str, db: Session = Depends(get_db)):
    return _token_page(request, token, "accept", db)


@router.post("/accept/{token}")
def accept_donation(request: Request, token: str, db: Session = Depends(get_db)):
    return _result_page(request, _record_decision(db, token, "ACCEPTED"), accepted=True)


@router.get("/decline/{token}")
def decline_donation_page(request: Request, token: str, db: Session = Depends(get_db)):
    return _token_page(request, token, "decline", db)


@router.post("/decline/{token}")
def decline_donation(request: Request, token: str, db: Session = Depends(get_db)):
    return _result_page(request, _record_decision(db, token, "DECLINED"), accepted=False)
