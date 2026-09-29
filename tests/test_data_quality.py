"""Regression coverage for the non-destructive donor data-quality queue."""

from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy import func, select

from backend.database.models import AuditLog, Donor


def test_data_quality_queue_reports_incomplete_profiles_to_admin_only(system):
    client, _, tokens = system
    response = client.get(
        "/api/admin/technical/data-quality", headers=tokens["admin"]
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["total"] == 2
    assert data["summary"]["total_donors"] == 2
    assert data["summary"]["incomplete_eligibility"] == 2
    assert data["summary"]["donors_with_issues"] == 2
    assert all(
        any(issue["code"] == "INCOMPLETE_ELIGIBILITY" for issue in item["issues"])
        for item in data["items"]
    )
    assert client.get(
        "/api/admin/technical/data-quality", headers=tokens["donor1"]
    ).status_code == 403


def test_exact_duplicate_signals_are_suggestions_and_do_not_merge_records(system):
    client, sessions, tokens = system
    with sessions.begin() as db:
        db.add(Donor(
            donor_code="TEST-DUPLICATE",
            full_name="Possible Duplicate",
            blood_group="A+",
            phone="+91 99999 00001",
            email="unique-duplicate@example.org",
        ))

    response = client.get(
        "/api/admin/technical/data-quality?category=DUPLICATE",
        headers=tokens["admin"],
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["total"] == 2
    assert data["summary"]["possible_duplicates"] == 2
    assert all(
        any(issue["code"] == "POSSIBLE_DUPLICATE" for issue in item["issues"])
        for item in data["items"]
    )
    with sessions() as db:
        assert db.scalar(select(func.count(Donor.id))) == 3


def test_invalid_contacts_and_stale_profiles_can_be_filtered(system):
    client, sessions, tokens = system
    with sessions.begin() as db:
        donor = db.get(Donor, 1)
        donor.email = "not-an-email"
        donor.phone = "12"
        donor.updated_at = datetime.now(timezone.utc) - timedelta(days=500)

    high = client.get(
        "/api/admin/technical/data-quality?severity=HIGH",
        headers=tokens["admin"],
    )
    assert high.status_code == 200
    assert high.json()["total"] == 1
    assert any(
        issue["code"] == "INVALID_CONTACT"
        for issue in high.json()["items"][0]["issues"]
    )

    stale = client.get(
        "/api/admin/technical/data-quality?category=STALE&stale_after_days=365",
        headers=tokens["admin"],
    )
    assert stale.status_code == 200
    assert stale.json()["total"] == 1
    assert stale.json()["items"][0]["donor_id"] == 1


def test_complete_profile_leaves_the_cleanup_queue(system):
    client, sessions, tokens = system
    with sessions.begin() as db:
        donor = db.get(Donor, 1)
        donor.date_of_birth = date(1995, 1, 1)
        donor.gender = "Male"
        donor.weight = Decimal("70")
        donor.hb_above_12_5 = "Yes"
        donor.bp_normal = "Yes"
        donor.regular_medication = "No"
        donor.district = "Test District"
        donor.updated_at = datetime.now(timezone.utc)

    response = client.get(
        "/api/admin/technical/data-quality?search=TEST-1",
        headers=tokens["admin"],
    )
    assert response.status_code == 200
    assert response.json()["total"] == 1
    item = response.json()["items"][0]
    assert item["completeness_percent"] == 100
    assert item["highest_severity"] == "COMPLETE"
    assert item["issues"] == []


def test_data_quality_export_is_formula_safe_and_audited(system):
    client, sessions, tokens = system
    with sessions.begin() as db:
        db.get(Donor, 1).full_name = "=HYPERLINK(\"unsafe\")"

    exported = client.get(
        "/api/admin/technical/data-quality/export", headers=tokens["admin"]
    )
    assert exported.status_code == 200
    assert exported.headers["content-type"].startswith("text/csv")
    assert "'=HYPERLINK" in exported.text
    assert client.get(
        "/api/admin/technical/data-quality/export", headers=tokens["donor1"]
    ).status_code == 403
    with sessions() as db:
        event = db.scalar(
            select(AuditLog)
            .where(AuditLog.action == "DATA_QUALITY_EXPORTED")
            .order_by(AuditLog.id.desc())
        )
        assert event is not None
        assert event.actor_username == "admin"
