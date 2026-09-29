"""Regression coverage for time-bound donor availability."""

from datetime import date, datetime, timedelta, timezone

from sqlalchemy import select

from backend.database.email_token import EmailToken
from backend.database.models import BloodRequest, Donor, Notification
from backend.database.notification_recipient import NotificationRecipient


def request_payload(units: int = 1) -> dict:
    return {
        "patient_name": "Deferral Patient",
        "case_details": "Deferral regression",
        "blood_group": "A+",
        "units_required": units,
        "required_date": str(date.today() + timedelta(days=1)),
        "priority": "Normal",
        "hospital_name": "Deferral Hospital",
        "hospital_location": "Test City",
        "contact_person": "Test Contact",
        "contact_phone": "9999900070",
    }


def test_manual_deferral_blocks_matching_and_donor_responses(system):
    client, _, tokens = system
    eligible_on = date.today() + timedelta(days=14)
    deferred = client.patch(
        "/api/donors/1",
        json={
            "status": "Deferred",
            "deferred_until": eligible_on.isoformat(),
            "deferral_reason": "Temporary medication",
        },
        headers=tokens["admin"],
    )
    assert deferred.status_code == 200, deferred.text
    assert deferred.json()["status"] == "Deferred"
    assert deferred.json()["deferred_until"] == eligible_on.isoformat()

    created = client.post(
        "/api/blood-requests",
        json=request_payload(),
        headers=tokens["admin"],
    )
    request_id = created.json()["id"]
    matches = client.post(
        "/api/match/find",
        json={"blood_request_id": request_id},
        headers=tokens["admin"],
    )
    assert matches.status_code == 200, matches.text
    assert {item["donor"]["id"] for item in matches.json()["matches"]} == {2}

    availability = client.get("/api/match/availability", headers=tokens["admin"])
    a_positive = next(item for item in availability.json() if item["group"] == "A+")
    assert a_positive["available_donors"] == 1

    summary = client.get("/api/donor-dashboard/summary", headers=tokens["donor1"])
    assert summary.status_code == 200
    assert summary.json()["donor"]["status"] == "Deferred"
    assert eligible_on.isoformat() in summary.json()["eligibility_reminder"]
    assert client.get("/api/donor-dashboard/requests", headers=tokens["donor1"]).json() == []
    blocked = client.post(
        f"/api/donor-dashboard/requests/{request_id}/response",
        json={"response": "Yes"},
        headers=tokens["donor1"],
    )
    assert blocked.status_code == 409


def test_deferral_validation_and_manual_restoration(system):
    client, _, tokens = system
    assert client.patch(
        "/api/donors/1",
        json={"status": "Deferred", "deferral_reason": "Missing date"},
        headers=tokens["admin"],
    ).status_code == 422
    assert client.patch(
        "/api/donors/1",
        json={"status": "Deferred", "deferred_until": date.today().isoformat(), "deferral_reason": "Not future"},
        headers=tokens["admin"],
    ).status_code == 422
    assert client.patch(
        "/api/donors/1",
        json={"status": "Paused"},
        headers=tokens["admin"],
    ).status_code == 422

    eligible_on = date.today() + timedelta(days=7)
    assert client.patch(
        "/api/donors/1",
        json={"deferred_until": eligible_on.isoformat(), "deferral_reason": "Short recovery"},
        headers=tokens["admin"],
    ).status_code == 200
    restored = client.patch(
        "/api/donors/1",
        json={"status": "Available"},
        headers=tokens["admin"],
    )
    assert restored.status_code == 200, restored.text
    assert restored.json()["status"] == "Available"
    assert restored.json()["deferred_until"] is None
    assert restored.json()["deferral_reason"] is None


def test_elapsed_deferral_restores_and_confirmed_donation_starts_new_one(system):
    client, sessions, tokens = system
    with sessions.begin() as db:
        donor = db.get(Donor, 1)
        donor.gender = "Male"
        donor.status = "Deferred"
        donor.deferred_until = date.today()
        donor.deferral_reason = "Elapsed recovery"

    donors = client.get("/api/donors", headers=tokens["admin"])
    restored = next(item for item in donors.json() if item["id"] == 1)
    assert restored["status"] == "Available"

    created = client.post(
        "/api/blood-requests",
        json=request_payload(),
        headers=tokens["admin"],
    )
    request_id = created.json()["id"]
    completed = client.post(
        f"/api/blood-requests/{request_id}/complete",
        json={"donor_id": 1, "units": 1},
        headers=tokens["admin"],
    )
    assert completed.status_code == 200, completed.text

    donor = client.get("/api/donors/1", headers=tokens["admin"])
    assert donor.status_code == 200
    assert donor.json()["status"] == "Deferred"
    assert donor.json()["deferred_until"] == (date.today() + timedelta(days=90)).isoformat()
    assert donor.json()["deferral_reason"] == "Post-donation recovery period (90 days)"


def test_deferred_donor_cannot_accept_an_old_email_link(system):
    client, sessions, _ = system
    with sessions.begin() as db:
        donor = db.get(Donor, 1)
        donor.status = "Deferred"
        donor.deferred_until = date.today() + timedelta(days=30)
        donor.deferral_reason = "Temporary clinical deferral"
        request = BloodRequest(
            patient_name="Email Deferral Patient", case_details="Email deferral regression",
            blood_group="A+", units_required=1,
            required_date=date.today() + timedelta(days=1), priority="Normal",
            hospital_name="Email Deferral Hospital", hospital_location="Test City",
            contact_person="Test Contact", contact_phone="9999900071", created_by=1,
        )
        db.add(request)
        db.flush()
        campaign = Notification(blood_request_id=request.id, title="Deferral outreach", status="ACTIVE")
        token = EmailToken(
            token="deferred-donor-token",
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
        )
        db.add_all([campaign, token])
        db.flush()
        db.add(NotificationRecipient(
            notification_id=campaign.id,
            donor_id=donor.id,
            email_token_id=token.id,
            email=donor.email,
        ))

    page = client.get("/email/accept/deferred-donor-token")
    assert page.status_code == 200 and "Link Expired" in page.text
    result = client.post("/email/accept/deferred-donor-token")
    assert result.status_code == 200 and "Link Expired" in result.text
    with sessions() as db:
        token = db.scalar(select(EmailToken).where(EmailToken.token == "deferred-donor-token"))
        assert token.used is False


def test_resend_skips_donor_who_became_deferred(system, monkeypatch):
    from backend.services import email_service

    client, _, tokens = system
    monkeypatch.setattr(email_service, "delivery_configuration_error", lambda: None)
    monkeypatch.setattr(email_service, "send_email", lambda *args, **kwargs: True)
    created = client.post(
        "/api/blood-requests",
        json=request_payload(),
        headers=tokens["admin"],
    )
    request_id = created.json()["id"]
    sent = client.post(
        "/api/match/send",
        json={"blood_request_id": request_id, "donor_ids": [1]},
        headers=tokens["admin"],
    )
    assert sent.status_code == 200, sent.text
    campaign_id = sent.json()["campaign_id"]

    deferred = client.patch(
        "/api/donors/1",
        json={
            "status": "Deferred",
            "deferred_until": (date.today() + timedelta(days=10)).isoformat(),
            "deferral_reason": "Temporary illness",
        },
        headers=tokens["admin"],
    )
    assert deferred.status_code == 200

    resend = client.post(
        f"/api/notifications/{campaign_id}/resend-pending",
        headers=tokens["admin"],
    )
    assert resend.status_code == 409
    details = client.get(f"/api/notifications/{campaign_id}/recipients", headers=tokens["admin"])
    assert details.status_code == 200
    assert details.json()[0]["status"] == "INELIGIBLE"
