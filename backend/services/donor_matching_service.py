"""
BloodLink Donor Matching Service.

This module contains all donor matching
business logic.
"""

from __future__ import annotations

from typing import Dict, List
from datetime import date
from math import asin, cos, radians, sin, sqrt

# ==========================================================
# BLOOD COMPATIBILITY MATRIX
# ==========================================================

# Compatible red blood cell donors.
# Keys = Patient blood group
# Values = Compatible donor blood groups.

COMPATIBILITY_MATRIX: Dict[str, List[str]] = {

    "A+": [
        "A+",
        "A-",
        "O+",
        "O-",
    ],

    "A-": [
        "A-",
        "O-",
    ],

    "B+": [
        "B+",
        "B-",
        "O+",
        "O-",
    ],

    "B-": [
        "B-",
        "O-",
    ],

    "AB+": [
        "A+",
        "A-",
        "B+",
        "B-",
        "AB+",
        "AB-",
        "O+",
        "O-",
    ],

    "AB-": [
        "A-",
        "B-",
        "AB-",
        "O-",
    ],

    "O+": [
        "O+",
        "O-",
    ],

    "O-": [
        "O-",
    ],

}


# ==========================================================
# GET COMPATIBLE GROUPS
# ==========================================================

def get_compatible_blood_groups(
    patient_blood_group: str,
) -> list[str]:
    """
    Return all compatible donor blood groups
    for a patient.
    """

    normalized = (
        patient_blood_group
        .strip()
        .upper()
    )

    return COMPATIBILITY_MATRIX.get(
        normalized,
        [],
    )


def is_compatible_donor(
    patient_blood_group: str,
    donor_blood_group: str,
) -> bool:
    """Return whether donor red cells are compatible with the patient.

    Blood requests in BloodLink represent red-cell/whole-blood requirements,
    so compatibility is directional: an O- donor can support an A+ patient,
    while an A+ donor cannot support an O- patient.
    """
    donor_group = donor_blood_group.strip().upper()
    return donor_group in get_compatible_blood_groups(patient_blood_group)
# ==========================================================
# MATCH SCORING
# ==========================================================

EXACT_BLOOD_MATCH_SCORE = 100

COMPATIBLE_BLOOD_MATCH_SCORE = 80

AVAILABLE_SCORE = 40

HEALTHY_SCORE = 25

LAST_DONATION_OVER_120_DAYS = 20

LAST_DONATION_OVER_90_DAYS = 10

NEVER_DONATED_SCORE = 15

SAME_DISTRICT_SCORE = 15

SAME_CITY_SCORE = 10

WITHIN_5_KM_SCORE = 30

WITHIN_15_KM_SCORE = 25

WITHIN_30_KM_SCORE = 18

WITHIN_60_KM_SCORE = 10

AGE_BONUS = 5
# ==========================================================
# BLOOD GROUP SCORE
# ==========================================================

def calculate_blood_group_score(
    patient_group: str,
    donor_group: str,
) -> int:
    """
    Score based on blood compatibility.
    """

    patient_group = patient_group.upper().strip()
    donor_group = donor_group.upper().strip()

    if patient_group == donor_group:
        return EXACT_BLOOD_MATCH_SCORE

    compatible = get_compatible_blood_groups(
        patient_group
    )

    if donor_group in compatible:
        return COMPATIBLE_BLOOD_MATCH_SCORE

    return 0
# ==========================================================
# AVAILABILITY SCORE
# ==========================================================

def calculate_availability_score(
    donor_status: str,
) -> int:

    if donor_status.lower() == "available":
        return AVAILABLE_SCORE

    return 0
# ==========================================================
# HEALTH SCORE
# ==========================================================

def calculate_health_score(
    donor,
) -> int:

    score = 0

    if donor.hb_above_12_5 == "Yes":
        score += 10

    if donor.bp_normal == "Yes":
        score += 10

    if donor.regular_medication == "No":
        score += 5

    return score
# ==========================================================
# DONATION INTERVAL SCORE
# ==========================================================

def calculate_last_donation_score(
    last_donation_date,
) -> int:

    if last_donation_date is None:
        return NEVER_DONATED_SCORE

    days = (
        date.today() -
        last_donation_date
    ).days

    if days >= 120:
        return LAST_DONATION_OVER_120_DAYS

    if days >= 90:
        return LAST_DONATION_OVER_90_DAYS

    return 0
# ==========================================================
# LOCATION SCORE
# ==========================================================

def calculate_location_score(
    request_district,
    donor_district,
    request_city=None,
    donor_city=None,
) -> int:

    score = 0

    if (
        request_district
        and donor_district
        and request_district.strip().casefold()
        == donor_district.strip().casefold()
    ):
        score += SAME_DISTRICT_SCORE

    if (
        request_city
        and donor_city
        and request_city.strip().casefold()
        == donor_city.strip().casefold()
    ):
        score += SAME_CITY_SCORE

    return score


def calculate_distance_km(
    request_latitude,
    request_longitude,
    donor_latitude,
    donor_longitude,
) -> float | None:
    """Return great-circle distance in kilometres when both points exist."""

    coordinates = (
        request_latitude,
        request_longitude,
        donor_latitude,
        donor_longitude,
    )
    if any(value is None for value in coordinates):
        return None

    request_lat, request_lon, donor_lat, donor_lon = map(float, coordinates)
    latitude_delta = radians(donor_lat - request_lat)
    longitude_delta = radians(donor_lon - request_lon)
    request_latitude_radians = radians(request_lat)
    donor_latitude_radians = radians(donor_lat)

    haversine = (
        sin(latitude_delta / 2) ** 2
        + cos(request_latitude_radians)
        * cos(donor_latitude_radians)
        * sin(longitude_delta / 2) ** 2
    )
    angular_distance = 2 * asin(sqrt(min(1.0, haversine)))
    return round(6371.0088 * angular_distance, 2)


def calculate_distance_score(distance_km: float) -> int:
    """Reward nearby donors using transparent distance bands."""

    if distance_km <= 5:
        return WITHIN_5_KM_SCORE
    if distance_km <= 15:
        return WITHIN_15_KM_SCORE
    if distance_km <= 30:
        return WITHIN_30_KM_SCORE
    if distance_km <= 60:
        return WITHIN_60_KM_SCORE
    return 0


def describe_location_match(
    distance_km: float | None,
    request_district: str | None,
    donor_district: str | None,
    request_city: str | None,
    donor_city: str | None,
) -> str:
    if distance_km is not None:
        return "Coordinate distance"

    same_district = bool(
        request_district
        and donor_district
        and request_district.strip().casefold() == donor_district.strip().casefold()
    )
    same_city = bool(
        request_city
        and donor_city
        and request_city.strip().casefold() == donor_city.strip().casefold()
    )
    if same_district and same_city:
        return "Same city and district"
    if same_district:
        return "Same district"
    if same_city:
        return "Same city"
    return "Location unavailable"
# ==========================================================
# MATCH SCORE RESULT
# ==========================================================

from dataclasses import dataclass


@dataclass
class MatchScore:

    total_score: int

    blood_group_score: int

    availability_score: int

    health_score: int

    donation_score: int

    location_score: int

    distance_km: float | None

    location_match_type: str
# ==========================================================
# FINAL MATCH SCORE
# ==========================================================

def calculate_match_score(
    patient_blood_group: str,
    patient_district: str | None,
    patient_city: str | None,
    donor,
    request_latitude=None,
    request_longitude=None,
) -> MatchScore:
    """
    Calculate the complete donor match score.
    """

    blood_score = calculate_blood_group_score(
        patient_blood_group,
        donor.blood_group,
    )

    availability_score = calculate_availability_score(
        donor.status,
    )

    health_score = calculate_health_score(
        donor,
    )

    donation_score = calculate_last_donation_score(
        donor.last_donation_date,
    )

    distance_km = calculate_distance_km(
        request_latitude,
        request_longitude,
        donor.latitude,
        donor.longitude,
    )

    location_score = (
        calculate_distance_score(distance_km)
        if distance_km is not None
        else calculate_location_score(
            patient_district,
            donor.district,
            patient_city,
            donor.city,
        )
    )
    location_match_type = describe_location_match(
        distance_km,
        patient_district,
        donor.district,
        patient_city,
        donor.city,
    )

    total = (
        blood_score
        + availability_score
        + health_score
        + donation_score
        + location_score
    )

    return MatchScore(

        total_score=total,

        blood_group_score=blood_score,

        availability_score=availability_score,

        health_score=health_score,

        donation_score=donation_score,

        location_score=location_score,

        distance_km=distance_km,

        location_match_type=location_match_type,

    )
# ==========================================================
# RANKED DONOR
# ==========================================================

@dataclass
class RankedDonor:

    donor: object

    score: MatchScore

    rank: int = 0
# ==========================================================
# RANK DONORS
# ==========================================================

def rank_matching_donors(
    patient_blood_group: str,
    patient_district: str | None,
    patient_city: str | None,
    donors: list,
    request_latitude=None,
    request_longitude=None,
) -> list[RankedDonor]:
    """
    Rank compatible donors from best to worst.
    """

    ranked: list[RankedDonor] = []

    for donor in donors:

        if not is_compatible_donor(patient_blood_group, donor.blood_group):
            continue

        score = calculate_match_score(

            patient_blood_group,

            patient_district,

            patient_city,

            donor,

            request_latitude,

            request_longitude,

        )

        ranked.append(

            RankedDonor(

                donor=donor,

                score=score,

            )

        )

    ranked.sort(
        key=lambda item: (
            -item.score.total_score,
            item.score.distance_km is None,
            item.score.distance_km if item.score.distance_km is not None else float("inf"),
            getattr(item.donor, "id", 0) or 0,
        )
    )

    for index, donor in enumerate(
        ranked,
        start=1,
    ):

        donor.rank = index

    return ranked
