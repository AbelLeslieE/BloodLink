"""Authenticated opt-in and opt-out endpoints for browser Web Push."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.auth.dependencies import require_authentication
from backend.config.settings import get_settings
from backend.database.database import get_db
from backend.database.models import User
from backend.database.push_subscription import PushSubscription
from backend.services.push_notification_service import is_configured


router = APIRouter(prefix="/api/push", tags=["web push"])


class PushSubscriptionPayload(BaseModel):
    endpoint: str = Field(min_length=1, max_length=4096)
    keys: dict[str, str]


@router.get("/vapid-public-key")
def vapid_public_key() -> dict:
    """The VAPID public key is intentionally safe to expose to browsers."""
    return {"configured": is_configured(), "public_key": get_settings().vapid_public_key if is_configured() else None}


@router.get("/subscription")
def subscription_status(
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(require_authentication)],
) -> dict:
    enabled = db.scalar(select(PushSubscription.id).where(
        PushSubscription.user_id == user.id, PushSubscription.enabled.is_(True)
    )) is not None
    return {"configured": is_configured(), "enabled": enabled}


@router.post("/subscriptions", status_code=status.HTTP_204_NO_CONTENT)
def save_subscription(
    payload: PushSubscriptionPayload,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(require_authentication)],
) -> None:
    p256dh = payload.keys.get("p256dh", "").strip()
    auth = payload.keys.get("auth", "").strip()
    if not p256dh or not auth:
        raise HTTPException(status_code=422, detail="A valid browser push subscription is required.")
    subscription = db.scalar(select(PushSubscription).where(PushSubscription.endpoint == payload.endpoint))
    if subscription is None:
        subscription = PushSubscription(user_id=user.id, endpoint=payload.endpoint, p256dh=p256dh, auth=auth)
        db.add(subscription)
    else:
        # Endpoints are unique: reassignment lets a user safely move a browser
        # subscription after account recovery without duplicating delivery.
        subscription.user_id = user.id
        subscription.p256dh = p256dh
        subscription.auth = auth
        subscription.enabled = True
    db.commit()


@router.delete("/subscriptions", status_code=status.HTTP_204_NO_CONTENT)
def disable_subscription(
    payload: PushSubscriptionPayload,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(require_authentication)],
) -> None:
    subscription = db.scalar(select(PushSubscription).where(
        PushSubscription.endpoint == payload.endpoint,
        PushSubscription.user_id == user.id,
    ))
    if subscription is not None:
        subscription.enabled = False
        db.commit()
