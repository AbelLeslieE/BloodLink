from datetime import date, datetime, timedelta, timezone

from sqlalchemy import select

from backend.database.models import BloodRequest, Donor, Notification
from backend.database.notification_recipient import NotificationRecipient
from backend.services import notification_service


def _create_outreach_request_and_donors(sessions, *, units_required=2, extra_donors=4):
    with sessions.begin() as db:
        donors = list(db.scalars(select(Donor).order_by(Donor.id)))
        for number in range(3, 3 + extra_donors):
            donor = Donor(
                donor_code=f"STAGE-{number}",
                full_name=f"Stage Donor {number}",
                blood_group="A+",
                phone=f"98888000{number:02d}",
                email=f"stage{number}@example.org",
                status="Available",
            )
            db.add(donor)
            donors.append(donor)
        db.flush()
        request = BloodRequest(
            patient_name="Staged Outreach Patient",
            case_details="Staged outreach regression",
            blood_group="A+",
            units_required=units_required,
            required_date=date.today() + timedelta(days=1),
            priority="Urgent",
            hospital_name="Staged Outreach Hospital",
            hospital_location="Test City",
            contact_person="Test Contact",
            contact_phone="9888899999",
            created_by=1,
        )
        db.add(request)
        db.flush()
        return request.id, [donor.id for donor in donors]


def test_staged_outreach_releases_only_one_ranked_batch_after_cooldown(system, monkeypatch):
    from backend.services import email_service

    client, sessions, tokens = system
    request_id, donor_ids = _create_outreach_request_and_donors(sessions)
    delivered_to = []
    monkeypatch.setattr(email_service, "delivery_configuration_error", lambda: None)
    monkeypatch.setattr(
        email_service,
        "send_email",
        lambda recipient_email, **_: delivered_to.append(recipient_email) or True,
    )

    ranking = client.post(
        "/api/match/find",
        json={"blood_request_id": request_id},
        headers=tokens["admin"],
    ).json()["matches"]
    ranked_emails = [item["donor"]["email"] for item in ranking]
    sent = client.post(
        "/api/match/send",
        json={
            "blood_request_id": request_id,
            "donor_ids": list(reversed(donor_ids)),
            "stage_size": 2,
            "stage_delay_minutes": 30,
        },
        headers=tokens["admin"],
    )
    assert sent.status_code == 200, sent.text
    assert sent.json()["current_stage"] == 1
    assert sent.json()["emails_sent"] == 2
    assert sent.json()["queued_count"] == len(donor_ids) - 2
    assert delivered_to == ranked_emails[:2]
    campaign_id = sent.json()["campaign_id"]

    with sessions() as db:
        recipients = list(db.scalars(
            select(NotificationRecipient)
            .where(NotificationRecipient.notification_id == campaign_id)
            .order_by(NotificationRecipient.outreach_order)
        ))
        assert [item.stage_number for item in recipients] == [1, 1, 2, 2, 3, 3]
        assert [item.status for item in recipients] == ["PENDING", "PENDING", "QUEUED", "QUEUED", "QUEUED", "QUEUED"]
        assert all(item.sent_at is not None and item.email_token_id is not None for item in recipients[:2])
        assert all(item.sent_at is None and item.email_token_id is None for item in recipients[2:])

    too_soon = client.post(
        f"/api/notifications/{campaign_id}/send-next-stage",
        headers=tokens["admin"],
    )
    assert too_soon.status_code == 409
    assert "after" in too_soon.json()["detail"]

    with sessions.begin() as db:
        db.get(Notification, campaign_id).next_stage_at = datetime.now(timezone.utc) - timedelta(minutes=1)
    second = client.post(
        f"/api/notifications/{campaign_id}/send-next-stage",
        headers=tokens["admin"],
    )
    assert second.status_code == 200, second.text
    assert second.json()["current_stage"] == 2
    assert second.json()["emails_sent"] == 2
    assert second.json()["queued_count"] == 2
    assert delivered_to == ranked_emails[:4]


def test_acceptance_target_stops_future_stages(system, monkeypatch):
    from backend.services import email_service

    client, sessions, tokens = system
    request_id, donor_ids = _create_outreach_request_and_donors(
        sessions, units_required=1, extra_donors=1
    )
    monkeypatch.setattr(email_service, "delivery_configuration_error", lambda: None)
    monkeypatch.setattr(email_service, "send_email", lambda *args, **kwargs: True)
    sent = client.post(
        "/api/match/send",
        json={
            "blood_request_id": request_id,
            "donor_ids": donor_ids,
            "stage_size": 1,
            "stage_delay_minutes": 0,
        },
        headers=tokens["admin"],
    )
    assert sent.status_code == 200, sent.text
    campaign_id = sent.json()["campaign_id"]

    with sessions() as db:
        campaign = db.get(Notification, campaign_id)
        first = db.scalar(
            select(NotificationRecipient)
            .where(NotificationRecipient.notification_id == campaign_id)
            .order_by(NotificationRecipient.outreach_order)
        )
        first.status = "ACCEPTED"
        first.responded_at = datetime.now(timezone.utc)
        notification_service.refresh_statistics(db, campaign)
        assert campaign.status == "TARGET_MET"
        assert campaign.queued_count == len(donor_ids) - 1
        assert campaign.next_stage_at is None

    blocked = client.post(
        f"/api/notifications/{campaign_id}/send-next-stage",
        headers=tokens["admin"],
    )
    assert blocked.status_code == 409
    assert "Enough donors" in blocked.json()["detail"]


def test_resend_pending_never_releases_queued_donors(system, monkeypatch):
    from backend.services import email_service

    client, sessions, tokens = system
    request_id, donor_ids = _create_outreach_request_and_donors(
        sessions, units_required=2, extra_donors=1
    )
    delivered_to = []
    monkeypatch.setattr(email_service, "delivery_configuration_error", lambda: None)
    monkeypatch.setattr(
        email_service,
        "send_email",
        lambda recipient_email, **_: delivered_to.append(recipient_email) or True,
    )
    sent = client.post(
        "/api/match/send",
        json={
            "blood_request_id": request_id,
            "donor_ids": donor_ids,
            "stage_size": 1,
            "stage_delay_minutes": 30,
        },
        headers=tokens["admin"],
    )
    campaign_id = sent.json()["campaign_id"]
    first_email = delivered_to[0]
    delivered_to.clear()

    resent = client.post(
        f"/api/notifications/{campaign_id}/resend-pending",
        headers=tokens["admin"],
    )
    assert resent.status_code == 200, resent.text
    assert resent.json()["pending_recipients"] == 1
    assert delivered_to == [first_email]
    with sessions() as db:
        statuses = list(db.scalars(
            select(NotificationRecipient.status)
            .where(NotificationRecipient.notification_id == campaign_id)
            .order_by(NotificationRecipient.outreach_order)
        ))
        assert statuses == ["PENDING", "QUEUED", "QUEUED"]
