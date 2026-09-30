from datetime import date, datetime, time, timedelta, timezone
from io import BytesIO
from zoneinfo import ZoneInfo

from openpyxl import load_workbook
from sqlalchemy import select

from backend.config.settings import get_settings
from backend.database.models import BloodRequest, Donor
from backend.database.notification_recipient import NotificationRecipient
from backend.services import donor_eligibility_service


def _request(db, *, latitude=None, longitude=None):
    request = BloodRequest(
        patient_name="Preference Test Patient",
        case_details="Donor preference regression",
        blood_group="A+",
        units_required=1,
        required_date=date.today() + timedelta(days=1),
        priority="Urgent",
        hospital_name="Preference Hospital",
        hospital_location="Test City",
        hospital_latitude=latitude,
        hospital_longitude=longitude,
        contact_person="Test Contact",
        contact_phone="9777700000",
        created_by=1,
    )
    db.add(request)
    db.flush()
    return request.id


def _closed_contact_window() -> tuple[str, str]:
    local_now = datetime.now(ZoneInfo(get_settings().request_timezone))
    start = (local_now + timedelta(hours=2)).time().replace(second=0, microsecond=0)
    end = (local_now + timedelta(hours=3)).time().replace(second=0, microsecond=0)
    return start.isoformat(timespec="minutes"), end.isoformat(timespec="minutes")


def test_donor_controls_pause_radius_and_contact_hours(system):
    client, sessions, tokens = system
    with sessions.begin() as db:
        request_id = _request(db)

    paused_until = datetime.now(timezone.utc) + timedelta(days=2)
    saved = client.put(
        "/api/donor-dashboard/preferences",
        json={
            "availability_paused_until": paused_until.isoformat(),
            "travel_radius_km": 25,
            "contact_window_start": "09:00",
            "contact_window_end": "18:00",
        },
        headers=tokens["donor1"],
    )
    assert saved.status_code == 200, saved.text
    assert saved.json()["pause_active"] is True
    assert saved.json()["travel_radius_km"] == 25
    assert saved.json()["contact_window_start"] == "09:00:00"

    summary = client.get("/api/donor-dashboard/summary", headers=tokens["donor1"])
    assert summary.status_code == 200
    assert summary.json()["preferences"]["pause_active"] is True
    assert summary.json()["preferences"]["timezone"] == get_settings().request_timezone
    assert client.get("/api/donor-dashboard/requests", headers=tokens["donor1"]).json() == []
    blocked = client.post(
        f"/api/donor-dashboard/requests/{request_id}/response",
        json={"response": "Yes"},
        headers=tokens["donor1"],
    )
    assert blocked.status_code == 409
    assert "paused" in blocked.json()["detail"].lower()

    resumed = client.put(
        "/api/donor-dashboard/preferences",
        json={
            "availability_paused_until": None,
            "travel_radius_km": 25,
            "contact_window_start": "09:00",
            "contact_window_end": "18:00",
        },
        headers=tokens["donor1"],
    )
    assert resumed.status_code == 200
    assert resumed.json()["pause_active"] is False
    assert request_id in {
        item["id"]
        for item in client.get("/api/donor-dashboard/requests", headers=tokens["donor1"]).json()
    }

    assert client.put(
        "/api/donor-dashboard/preferences",
        json={"availability_paused_until": None},
        headers=tokens["admin"],
    ).status_code == 403
    assert client.put(
        "/api/donor-dashboard/preferences",
        json={"contact_window_start": "09:00", "contact_window_end": None},
        headers=tokens["donor1"],
    ).status_code == 422
    assert client.put(
        "/api/donor-dashboard/preferences",
        json={"availability_paused_until": (datetime.now(timezone.utc) - timedelta(minutes=1)).isoformat()},
        headers=tokens["donor1"],
    ).status_code == 422


def test_travel_radius_and_contact_hours_filter_matching(system):
    client, sessions, tokens = system
    with sessions.begin() as db:
        donor = db.get(Donor, 1)
        donor.latitude = 0
        donor.longitude = 0
        request_id = _request(db, latitude=1, longitude=1)

    limited = client.put(
        "/api/donor-dashboard/preferences",
        json={"travel_radius_km": 25},
        headers=tokens["donor1"],
    )
    assert limited.status_code == 200
    matches = client.post(
        "/api/match/find",
        json={"blood_request_id": request_id},
        headers=tokens["admin"],
    ).json()
    assert 1 not in {item["donor"]["id"] for item in matches["matches"]}
    assert matches["eligibility_policy"]["excluded_reasons"][
        "Request is outside the donor's preferred travel radius."
    ] == 1

    expanded = client.put(
        "/api/donor-dashboard/preferences",
        json={"travel_radius_km": 500},
        headers=tokens["donor1"],
    )
    assert expanded.status_code == 200
    matches = client.post(
        "/api/match/find",
        json={"blood_request_id": request_id},
        headers=tokens["admin"],
    ).json()
    assert 1 in {item["donor"]["id"] for item in matches["matches"]}

    start, end = _closed_contact_window()
    closed = client.put(
        "/api/donor-dashboard/preferences",
        json={
            "travel_radius_km": 500,
            "contact_window_start": start,
            "contact_window_end": end,
        },
        headers=tokens["donor1"],
    )
    assert closed.status_code == 200
    assert closed.json()["contact_window_open_now"] is False
    matches = client.post(
        "/api/match/find",
        json={"blood_request_id": request_id},
        headers=tokens["admin"],
    ).json()
    assert 1 not in {item["donor"]["id"] for item in matches["matches"]}
    assert matches["eligibility_policy"]["excluded_reasons"][
        "Current time is outside the donor's preferred contact hours."
    ] == 1


def test_resend_respects_changed_contact_hours(system, monkeypatch):
    from backend.services import email_service

    client, sessions, tokens = system
    with sessions.begin() as db:
        request_id = _request(db)
    deliveries = []
    monkeypatch.setattr(email_service, "delivery_configuration_error", lambda: None)
    monkeypatch.setattr(
        email_service,
        "send_email",
        lambda recipient_email, **_: deliveries.append(recipient_email) or True,
    )
    sent = client.post(
        "/api/match/send",
        json={"blood_request_id": request_id, "donor_ids": [1]},
        headers=tokens["admin"],
    )
    assert sent.status_code == 200, sent.text
    campaign_id = sent.json()["campaign_id"]
    assert len(deliveries) == 1

    start, end = _closed_contact_window()
    assert client.put(
        "/api/donor-dashboard/preferences",
        json={"contact_window_start": start, "contact_window_end": end},
        headers=tokens["donor1"],
    ).status_code == 200
    resend = client.post(
        f"/api/notifications/{campaign_id}/resend-pending",
        headers=tokens["admin"],
    )
    assert resend.status_code == 409
    assert "contact hours" in resend.json()["detail"]
    assert len(deliveries) == 1
    with sessions() as db:
        recipient = db.scalar(select(NotificationRecipient).where(
            NotificationRecipient.notification_id == campaign_id
        ))
        assert recipient.status == "PENDING"


def test_admin_export_includes_donor_outreach_preferences(system):
    client, _, tokens = system
    export = client.get("/api/donors/export", headers=tokens["admin"])
    assert export.status_code == 200
    headers = [cell.value for cell in load_workbook(BytesIO(export.content)).active[1]]
    assert "Donor Pause Until" in headers
    assert "Travel Radius (km)" in headers
    assert "Contact Window Start" in headers
    assert "Contact Window End" in headers


def test_overnight_contact_window_and_pause_are_deterministic():
    donor = Donor(
        donor_code="PREF-UNIT",
        full_name="Preference Unit",
        blood_group="A+",
        contact_window_start=time(22, 0),
        contact_window_end=time(6, 0),
    )
    zone = ZoneInfo(get_settings().request_timezone)
    inside = datetime(2026, 9, 30, 23, 0, tzinfo=zone).astimezone(timezone.utc)
    outside = datetime(2026, 9, 30, 12, 0, tzinfo=zone).astimezone(timezone.utc)
    assert donor_eligibility_service.is_contact_window_open(donor, now=inside)
    assert not donor_eligibility_service.is_contact_window_open(donor, now=outside)

    donor.availability_paused_until = inside + timedelta(hours=1)
    assert donor_eligibility_service.is_availability_pause_active(donor, now=inside)
    assert not donor_eligibility_service.is_availability_pause_active(
        donor, now=inside + timedelta(hours=2)
    )
