"""Regression coverage for clinician-reviewed donor pre-screening."""

from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy import select

from backend.database.models import AuditLog, Donor


def blood_request_payload() -> dict:
    return {
        "patient_name": "Eligibility Patient",
        "case_details": "Eligibility policy regression",
        "blood_group": "A+",
        "units_required": 1,
        "required_date": str(date.today() + timedelta(days=1)),
        "priority": "Normal",
        "hospital_name": "Eligibility Hospital",
        "hospital_location": "Test City",
        "contact_person": "Test Contact",
        "contact_phone": "9999900080",
    }


def reviewed_policy(**overrides) -> dict:
    payload = {
        "enforcement_mode": "ENFORCED",
        "minimum_age_years": 18,
        "maximum_age_years": 65,
        "minimum_weight_kg": "45.00",
        "require_complete_profile": False,
        "reviewer_name": "Dr Test Reviewer",
        "review_notes": "Reviewed against the current blood-centre donor selection SOP.",
        "clinical_review_confirmed": True,
    }
    payload.update(overrides)
    return payload


def test_policy_defaults_to_non_disruptive_advisory_mode(system):
    client, _, tokens = system
    response = client.get(
        "/api/admin/technical/eligibility-policy", headers=tokens["admin"]
    )
    assert response.status_code == 200, response.text
    policy = response.json()
    assert policy["enforcement_mode"] == "ADVISORY"
    assert policy["minimum_age_years"] == 18
    assert policy["maximum_age_years"] == 65
    assert Decimal(str(policy["minimum_weight_kg"])) == Decimal("45.00")
    assert policy["summary"]["matching_allowed"] == 2
    assert policy["summary"]["review_needed"] == 2
    assert policy["source_reference"].startswith("https://clinicalestablishments.mohfw.gov.in/")
    assert client.get(
        "/api/admin/technical/eligibility-policy", headers=tokens["donor1"]
    ).status_code == 403


def test_enforcement_requires_recorded_review_and_cannot_weaken_baseline(system):
    client, _, tokens = system
    missing_review = reviewed_policy(clinical_review_confirmed=False)
    assert client.put(
        "/api/admin/technical/eligibility-policy",
        json=missing_review,
        headers=tokens["admin"],
    ).status_code == 422

    weakened = reviewed_policy(minimum_age_years=17)
    assert client.put(
        "/api/admin/technical/eligibility-policy",
        json=weakened,
        headers=tokens["admin"],
    ).status_code == 422

    short_notes = reviewed_policy(review_notes="Too short")
    assert client.put(
        "/api/admin/technical/eligibility-policy",
        json=short_notes,
        headers=tokens["admin"],
    ).status_code == 422


def test_reviewed_enforcement_excludes_known_failure_everywhere(system):
    client, sessions, tokens = system
    with sessions.begin() as db:
        donor1, donor2 = db.get(Donor, 1), db.get(Donor, 2)
        donor1.date_of_birth = date(date.today().year - 17, 1, 1)
        donor1.weight = Decimal("55")
        donor1.hb_above_12_5 = "Yes"
        donor1.bp_normal = "Yes"
        donor1.regular_medication = "No"
        donor2.date_of_birth = date(date.today().year - 25, 1, 1)
        donor2.weight = Decimal("55")
        donor2.hb_above_12_5 = "Yes"
        donor2.bp_normal = "Yes"
        donor2.regular_medication = "No"

    saved = client.put(
        "/api/admin/technical/eligibility-policy",
        json=reviewed_policy(),
        headers=tokens["admin"],
    )
    assert saved.status_code == 200, saved.text
    assert saved.json()["enforcement_mode"] == "ENFORCED"
    assert saved.json()["reviewed_at"]

    created = client.post(
        "/api/blood-requests", json=blood_request_payload(), headers=tokens["admin"]
    )
    request_id = created.json()["id"]
    matches = client.post(
        "/api/match/find",
        json={"blood_request_id": request_id},
        headers=tokens["admin"],
    )
    assert matches.status_code == 200, matches.text
    assert {item["donor"]["id"] for item in matches.json()["matches"]} == {2}
    assert matches.json()["eligibility_policy"]["excluded_count"] == 1

    availability = client.get("/api/match/availability", headers=tokens["admin"])
    a_positive = next(item for item in availability.json() if item["group"] == "A+")
    assert a_positive["available_donors"] == 1
    assert client.get(
        "/api/donor-dashboard/requests", headers=tokens["donor1"]
    ).json() == []
    review = client.get(
        "/api/admin/technical/eligibility-policy/donors/1",
        headers=tokens["admin"],
    )
    assert review.status_code == 200
    assert review.json()["evaluation"]["match_allowed"] is False
    assert "configured minimum" in review.json()["evaluation"]["reasons"][0]


def test_advisory_mode_surfaces_failures_without_silently_excluding(system):
    client, sessions, tokens = system
    with sessions.begin() as db:
        donor = db.get(Donor, 1)
        donor.hb_above_12_5 = "No"

    created = client.post(
        "/api/blood-requests", json=blood_request_payload(), headers=tokens["admin"]
    )
    matches = client.post(
        "/api/match/find",
        json={"blood_request_id": created.json()["id"]},
        headers=tokens["admin"],
    )
    assert matches.status_code == 200, matches.text
    assert {item["donor"]["id"] for item in matches.json()["matches"]} == {1, 2}
    donor1 = next(item for item in matches.json()["matches"] if item["donor"]["id"] == 1)
    assert donor1["screening"]["passed"] is False
    assert donor1["screening"]["mode"] == "ADVISORY"
    assert any("Haemoglobin" in reason for reason in donor1["screening"]["reasons"])


def test_strict_reviewed_policy_blocks_incomplete_legacy_profiles_and_is_audited(system):
    client, sessions, tokens = system
    saved = client.put(
        "/api/admin/technical/eligibility-policy",
        json=reviewed_policy(require_complete_profile=True),
        headers=tokens["admin"],
    )
    assert saved.status_code == 200, saved.text
    assert saved.json()["summary"]["matching_blocked"] == 2

    with sessions() as db:
        event = db.scalar(
            select(AuditLog)
            .where(AuditLog.action == "ELIGIBILITY_POLICY_UPDATED")
            .order_by(AuditLog.id.desc())
        )
        assert event is not None
        assert event.actor_username == "admin"
        assert event.category == "ELIGIBILITY"

    switched = client.put(
        "/api/admin/technical/eligibility-policy",
        json={
            "enforcement_mode": "ADVISORY",
            "minimum_age_years": 18,
            "maximum_age_years": 65,
            "minimum_weight_kg": "45.00",
            "require_complete_profile": False,
            "clinical_review_confirmed": False,
        },
        headers=tokens["admin"],
    )
    assert switched.status_code == 200, switched.text
    assert switched.json()["reviewed_at"] is None
    assert switched.json()["summary"]["matching_allowed"] == 2
