"""
==========================================================
Dashboard API
==========================================================

Provides all dashboard statistics in one request.
"""

from __future__ import annotations

from fastapi import APIRouter
from fastapi import Depends
from sqlalchemy.orm import Session

from backend.auth.dependencies import require_authentication
from backend.database.database import get_db
from backend.database.models import User
from backend.database import crud

router = APIRouter(
    prefix="/api/dashboard",
    tags=["Dashboard"],
)


# ==========================================================
# DASHBOARD SUMMARY
# ==========================================================

@router.get("")
def dashboard_summary(
    database_session: Session = Depends(get_db),
    _: User = Depends(require_authentication),
):
    """
    Return dashboard statistics.
    """

    donors = crud.get_donors(
        database_session,
    )

    blood_requests = crud.get_blood_requests(
        database_session,
    )

    notifications = crud.get_notifications(
        database_session,
    )

    total_donors = len(
        donors,
    )

    active_requests = sum(
        1
        for request in blood_requests
        if request.status in (
            "Pending",
            "In Progress",
        )
    )

    emergency_cases = sum(
        1
        for request in blood_requests
        if request.priority == "Emergency"
    )

    fulfilled_requests = sum(
        1
        for request in blood_requests
        if request.status == "Fulfilled"
    )

    success_rate = 0

    if blood_requests:

        success_rate = round(
            (
                fulfilled_requests
                / len(blood_requests)
            ) * 100,
            1,
        )

    emails_sent = sum(
        campaign.total_sent
        for campaign in notifications
    )

    responses = sum(
        campaign.accepted_count
        + campaign.declined_count
        for campaign in notifications
    )


        # ------------------------------------------------------
    # Monthly Blood Requests
    # ------------------------------------------------------

    monthly_donations = {

        "Jan": 0,
        "Feb": 0,
        "Mar": 0,
        "Apr": 0,
        "May": 0,
        "Jun": 0,
        "Jul": 0,
        "Aug": 0,
        "Sep": 0,
        "Oct": 0,
        "Nov": 0,
        "Dec": 0,

    }

    for request in blood_requests:

        if request.required_date:

            month = request.required_date.strftime("%b")

            if month in monthly_donations:

                monthly_donations[month] += 1
    blood_group_distribution = {

        "A+": 0,
        "A-": 0,
        "B+": 0,
        "B-": 0,
        "AB+": 0,
        "AB-": 0,
        "O+": 0,
        "O-": 0,

    }

    for donor in donors:

        if donor.blood_group in blood_group_distribution:

            blood_group_distribution[
                donor.blood_group
            ] += 1


    return {

        "statistics": {

            "total_donors": total_donors,

            "active_requests": active_requests,

            "emergency_cases": emergency_cases,

            "success_rate": success_rate,

            "emails_sent": emails_sent,

            "responses": responses,

        },

                "monthly_donations": monthly_donations,

            "blood_group_distribution": blood_group_distribution,

    }