"""Secure Web Push delivery for real BloodLink blood requests."""

from __future__ import annotations

import json
import logging

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from backend.config.settings import get_settings
from backend.database.models import BloodRequest, Donor, User
from backend.database.push_subscription import PushSubscription

try:  # Keep local development usable until the Render dependency is installed.
    from pywebpush import WebPushException, webpush
except ImportError:  # pragma: no cover - exercised only without dependencies
    WebPushException = Exception
    webpush = None


logger = logging.getLogger(__name__)
_PRIORITY_RANK = {"Normal": 1, "Urgent": 2, "Emergency": 3}


def is_configured() -> bool:
    settings = get_settings()
    return bool(webpush and settings.vapid_public_key and settings.vapid_private_key and settings.vapid_subject)


def _priority_allows(subscription: PushSubscription, blood_request: BloodRequest) -> bool:
    return _PRIORITY_RANK.get(blood_request.priority, 1) >= _PRIORITY_RANK.get(subscription.minimum_priority, 1)


def _donor_for_subscription(session: Session, subscription: PushSubscription) -> Donor | None:
    """Resolve a donor dynamically, including older accounts linked by email."""
    if subscription.user.donor is not None:
        return subscription.user.donor
    return session.scalar(
        select(Donor).where(Donor.email == subscription.user.email)
    )


def _matches_request(session: Session, subscription: PushSubscription, blood_request: BloodRequest) -> bool:
    donor = _donor_for_subscription(session, subscription)
    if donor is None or donor.status != "Available":
        return False
    if donor.blood_group.strip().upper() != blood_request.blood_group.strip().upper():
        return False
    # The current request schema has free-form hospital_location, not a
    # structured district. Keep this policy point isolated so structured
    # district/city matching can be added without rewriting delivery.
    return _priority_allows(subscription, blood_request)


def _remove_invalid_subscription(session: Session, subscription: PushSubscription) -> None:
    session.delete(subscription)
    session.commit()


def notify_matching_donors(session: Session, blood_request: BloodRequest) -> dict[str, int]:
    """Send a server-originated notification after a persisted request exists.

    Delivery failures never roll back the medical request itself. Browser push
    providers report permanently invalid subscriptions as 404/410; those rows
    are immediately removed so future campaigns do not keep retrying them.
    """
    if not is_configured():
        logger.info("Web Push is not configured; skipped request %s.", blood_request.id)
        return {"sent": 0, "invalid": 0, "skipped": 0}

    settings = get_settings()
    subscriptions = list(session.scalars(
        select(PushSubscription)
        .options(joinedload(PushSubscription.user).joinedload(User.donor))
        .where(PushSubscription.enabled.is_(True))
    ).unique())
    payload = json.dumps({
        "title": "URGENT BLOOD REQUEST" if blood_request.priority in {"Urgent", "Emergency"} else "BLOOD REQUEST",
        "body": f"{blood_request.blood_group} blood required\nLocation: {blood_request.hospital_name}, {blood_request.hospital_location}\nTap to view request.",
        "tag": f"blood-request-{blood_request.id}",
        "url": f"/donor-dashboard?requestId={blood_request.id}",
        "requestId": blood_request.id,
    })
    sent = invalid = skipped = 0
    for subscription in subscriptions:
        if not _matches_request(session, subscription, blood_request):
            skipped += 1
            continue
        try:
            webpush(
                subscription_info={"endpoint": subscription.endpoint, "keys": {"p256dh": subscription.p256dh, "auth": subscription.auth}},
                data=payload,
                vapid_private_key=settings.vapid_private_key,
                vapid_claims={"sub": settings.vapid_subject},
                ttl=300,
            )
            sent += 1
        except WebPushException as error:
            status_code = getattr(getattr(error, "response", None), "status_code", None)
            if status_code in {404, 410}:
                _remove_invalid_subscription(session, subscription)
                invalid += 1
            else:
                logger.warning("Push delivery failed for request %s: %s", blood_request.id, error)
        except Exception:  # Delivery must not affect a saved blood request.
            logger.exception("Unexpected Web Push failure for request %s", blood_request.id)
    return {"sent": sent, "invalid": invalid, "skipped": skipped}
