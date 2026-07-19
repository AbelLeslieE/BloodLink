"""
BloodLink Donor Matching Service.

This module contains all donor matching
business logic.
"""

from __future__ import annotations

from typing import Dict, List
from datetime import date

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
        and request_district.lower()
        == donor_district.lower()
    ):
        score += SAME_DISTRICT_SCORE

    if (
        request_city
        and donor_city
        and request_city.lower()
        == donor_city.lower()
    ):
        score += SAME_CITY_SCORE

    return score
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
# ==========================================================
# FINAL MATCH SCORE
# ==========================================================

def calculate_match_score(
    patient_blood_group: str,
    patient_district: str | None,
    patient_city: str | None,
    donor,
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

    location_score = calculate_location_score(
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
) -> list[RankedDonor]:
    """
    Rank compatible donors from best to worst.
    """

    ranked: list[RankedDonor] = []

    compatible_groups = get_compatible_blood_groups(
        patient_blood_group
    )

    for donor in donors:

        if donor.blood_group not in compatible_groups:
            continue

        score = calculate_match_score(

            patient_blood_group,

            patient_district,

            patient_city,

            donor,

        )

        ranked.append(

            RankedDonor(

                donor=donor,

                score=score,

            )

        )

    ranked.sort(

        key=lambda x: x.score.total_score,

        reverse=True,

    )

    for index, donor in enumerate(
        ranked,
        start=1,
    ):

        donor.rank = index

    return ranked
        
        