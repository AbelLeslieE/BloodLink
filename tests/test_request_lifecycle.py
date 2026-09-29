"""Request expiry, escalation, and closure-reason regression coverage."""

from datetime import datetime, timedelta, timezone

from sqlalchemy import select

from backend.database.models import AuditLog, BloodRequest
from backend.services import request_lifecycle_service
from backend.services.audit_service import verify_audit_event


def request_payload(**overrides) -> dict:
    payload = {
        "patient_name": "Lifecycle Patient",
        "case_details": "Scheduled procedure",
        "blood_group": "A+",
        "units_required": 1,
        "required_date": str(request_lifecycle_service.local_today() + timedelta(days=5)),
        "priority": "Normal",
        "hospital_name": "Lifecycle Hospital",
        "hospital_location": "Central campus",
        "contact_person": "Lifecycle Contact",
        "contact_phone": "9999900088",
        "additional_notes": None,
    }
    payload.update(overrides)
    return payload


def create_request(client, headers, **overrides) -> dict:
    response = client.post(
        "/api/blood-requests",
        json=request_payload(**overrides),
        headers=headers,
    )
    assert response.status_code == 201, response.text
    return response.json()


def test_creation_sets_deadline_escalation_and_rejects_past_date(system):
    client, _, tokens = system
    emergency = create_request(client, tokens["admin"], priority="Emergency")
    assert emergency["expires_at"] is not None
    assert emergency["escalation_level"] == 3
    assert emergency["escalation_reason"] == "Emergency-priority request"

    past = client.post(
        "/api/blood-requests",
        json=request_payload(
            required_date=str(request_lifecycle_service.local_today() - timedelta(days=1))
        ),
        headers=tokens["admin"],
    )
    assert past.status_code == 422


def test_due_request_escalates_once_and_records_signed_audit(system):
    client, sessions, tokens = system
    now = datetime.now(timezone.utc)
    with sessions.begin() as database_session:
        request = BloodRequest(
            patient_name="Escalation Patient",
            case_details="Urgent procedure",
            blood_group="A+",
            units_required=1,
            required_date=request_lifecycle_service.local_today(),
            priority="Normal",
            status="Pending",
            expires_at=now + timedelta(hours=5),
            hospital_name="Escalation Hospital",
            hospital_location="Test City",
            contact_person="Test Contact",
            contact_phone="9999900077",
            created_by=1,
        )
        database_session.add(request)
        database_session.flush()
        request_id = request.id

    first = client.get("/api/blood-requests", headers=tokens["admin"])
    assert first.status_code == 200
    escalated = next(item for item in first.json() if item["id"] == request_id)
    assert escalated["escalation_level"] == 3
    assert escalated["escalation_reason"] == "Required within 6 hours"
    assert escalated["escalated_at"] is not None

    assert client.get("/api/blood-requests", headers=tokens["admin"]).status_code == 200
    with sessions() as database_session:
        events = list(database_session.scalars(select(AuditLog).where(
            AuditLog.action == "REQUEST_AUTO_ESCALATED",
            AuditLog.target_id == str(request_id),
        )).all())
        assert len(events) == 1
        assert verify_audit_event(events[0])


def test_overdue_request_expires_and_is_removed_from_matching(system):
    client, sessions, tokens = system
    now = datetime.now(timezone.utc)
    with sessions.begin() as database_session:
        request = BloodRequest(
            patient_name="Expired Patient",
            case_details="Past requirement",
            blood_group="A+",
            units_required=2,
            units_fulfilled=1,
            required_date=request_lifecycle_service.local_today() - timedelta(days=1),
            priority="Urgent",
            status="Partially Fulfilled",
            expires_at=now - timedelta(minutes=1),
            hospital_name="Expired Hospital",
            hospital_location="Test City",
            contact_person="Test Contact",
            contact_phone="9999900066",
            created_by=1,
        )
        database_session.add(request)
        database_session.flush()
        request_id = request.id

    match = client.post(
        "/api/match/find",
        json={"blood_request_id": request_id},
        headers=tokens["admin"],
    )
    assert match.status_code == 409

    with sessions() as database_session:
        expired = database_session.get(BloodRequest, request_id)
        assert expired.status == "Expired"
        assert expired.closed_at is not None
        assert "1 unit(s) still outstanding" in expired.closure_reason
        event = database_session.scalar(select(AuditLog).where(
            AuditLog.action == "REQUEST_AUTO_EXPIRED",
            AuditLog.target_id == str(request_id),
        ))
        assert event is not None and verify_audit_event(event)


def test_manual_closure_requires_reason_and_reopen_clears_it(system):
    client, _, tokens = system
    request = create_request(client, tokens["admin"])
    endpoint = f"/api/blood-requests/{request['id']}/status"

    missing_reason = client.patch(
        endpoint,
        json={"status": "Cancelled"},
        headers=tokens["admin"],
    )
    assert missing_reason.status_code == 422

    cancelled = client.patch(
        endpoint,
        json={"status": "Cancelled", "closure_reason": "Procedure rescheduled"},
        headers=tokens["admin"],
    )
    assert cancelled.status_code == 200, cancelled.text
    assert cancelled.json()["closure_reason"] == "Procedure rescheduled"
    assert cancelled.json()["closed_at"] is not None

    reopened = client.patch(
        endpoint,
        json={"status": "Pending"},
        headers=tokens["admin"],
    )
    assert reopened.status_code == 200, reopened.text
    assert reopened.json()["closure_reason"] is None
    assert reopened.json()["closed_at"] is None


def test_fulfilment_records_automatic_closure_reason(system):
    client, _, tokens = system
    request = create_request(client, tokens["admin"])
    completed = client.post(
        f"/api/blood-requests/{request['id']}/complete",
        json={
            "external_donor_name": "External Lifecycle Donor",
            "units": 1,
            "donation_type": "Voluntary",
        },
        headers=tokens["admin"],
    )
    assert completed.status_code == 200, completed.text
    assert completed.json()["status"] == "Fulfilled"
    assert completed.json()["closure_reason"] == "Fulfilled by confirmed donation units."
    assert completed.json()["closed_at"] is not None
