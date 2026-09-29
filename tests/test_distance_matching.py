"""Regression coverage for structured locations and donor distance ranking."""

from decimal import Decimal

import pytest

from backend.database.models import Donor
from backend.services.donor_matching_service import calculate_distance_km


def request_payload(**overrides):
    payload = {
        "patient_name": "Distance Test Patient",
        "case_details": "Surgery",
        "blood_group": "A+",
        "units_required": 1,
        "required_date": "2026-10-02",
        "priority": "Urgent",
        "hospital_name": "Distance Test Hospital",
        "hospital_location": "Central campus",
        "hospital_district": "Ernakulam",
        "hospital_city": "Kochi",
        "hospital_latitude": 10.0,
        "hospital_longitude": 76.0,
        "contact_person": "Test Contact",
        "contact_phone": "9999900099",
        "additional_notes": None,
    }
    payload.update(overrides)
    return payload


def test_haversine_distance_is_stable():
    assert calculate_distance_km(10, 76, 10, 76) == 0
    assert calculate_distance_km(10, 76, 11, 76) == pytest.approx(111.20, abs=0.05)
    assert calculate_distance_km(None, 76, 11, 76) is None


def test_matching_ranks_nearest_coordinate_first(system):
    client, sessions, tokens = system
    with sessions.begin() as database_session:
        donors = database_session.query(Donor).order_by(Donor.id).all()
        donors[0].district = donors[1].district = "Ernakulam"
        donors[0].city = donors[1].city = "Kochi"
        donors[0].latitude = Decimal("10.010000")
        donors[0].longitude = Decimal("76.000000")
        donors[1].latitude = Decimal("11.000000")
        donors[1].longitude = Decimal("76.000000")

    created = client.post(
        "/api/blood-requests",
        json=request_payload(),
        headers=tokens["admin"],
    )
    assert created.status_code == 201, created.text
    request_data = created.json()
    assert request_data["hospital_district"] == "Ernakulam"
    assert request_data["hospital_city"] == "Kochi"

    matched = client.post(
        "/api/match/find",
        json={"blood_request_id": request_data["id"]},
        headers=tokens["admin"],
    )
    assert matched.status_code == 200, matched.text
    matches = matched.json()["matches"]
    assert [item["donor"]["name"] for item in matches] == ["Test Donor 1", "Test Donor 2"]
    assert matches[0]["distance_km"] == pytest.approx(1.11, abs=0.02)
    assert matches[1]["distance_km"] == pytest.approx(111.20, abs=0.05)
    assert matches[0]["location_match_type"] == "Coordinate distance"
    assert matches[0]["location_score"] > matches[1]["location_score"]


def test_matching_falls_back_to_structured_city_and_district(system):
    client, sessions, tokens = system
    with sessions.begin() as database_session:
        donors = database_session.query(Donor).order_by(Donor.id).all()
        donors[0].district, donors[0].city = "Thrissur", "Thrissur"
        donors[1].district, donors[1].city = "Ernakulam", "Kochi"
        for donor in donors:
            donor.latitude = None
            donor.longitude = None

    created = client.post(
        "/api/blood-requests",
        json=request_payload(hospital_latitude=None, hospital_longitude=None),
        headers=tokens["admin"],
    )
    assert created.status_code == 201, created.text

    matched = client.post(
        "/api/match/find",
        json={"blood_request_id": created.json()["id"]},
        headers=tokens["admin"],
    )
    matches = matched.json()["matches"]
    assert matches[0]["donor"]["name"] == "Test Donor 2"
    assert matches[0]["distance_km"] is None
    assert matches[0]["location_match_type"] == "Same city and district"
    assert matches[0]["location_score"] == 25


def test_request_coordinates_require_a_valid_pair(system):
    client, _, tokens = system
    missing_longitude = client.post(
        "/api/blood-requests",
        json=request_payload(hospital_longitude=None),
        headers=tokens["admin"],
    )
    assert missing_longitude.status_code == 422

    out_of_range = client.post(
        "/api/blood-requests",
        json=request_payload(hospital_latitude=91),
        headers=tokens["admin"],
    )
    assert out_of_range.status_code == 422
