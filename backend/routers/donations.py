from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.database.database import get_db
from backend.database import crud
from backend.database.schemas import DonationRecordCreate

router = APIRouter()


# ==========================================================
# GET ALL DONATIONS
# ==========================================================

@router.get("/")
def get_donations(
    database_session: Session = Depends(get_db),
):
    """
    Return all donation history records.
    """

    donations = crud.get_donation_history(
        database_session,
    )

    response = []

    for donation in donations:

        donor = donation.donor

        response.append(

            {

                "id": donation.id,

                "donation_id": f"DON-{donation.id:06d}",

                "donor_id": donor.id,

                "donor_code": donor.donor_code,

                "donor_name": donor.full_name,

                "phone": donor.phone,

                "district": donor.district,

                "blood_group": donor.blood_group,

                "hospital_name": donation.blood_request.hospital_name,

                "donation_date": donation.donation_date,

                "units": donation.units,

                "donation_type": donation.donation_type,

                "remarks": donation.remarks,

            }

        )

    return response

# ==========================================================
# DONATION SUMMARY
# ==========================================================

@router.get("/summary")
def donation_summary(
    database_session: Session = Depends(get_db),
):
    """
    Return dashboard statistics for the
    Donation History page.
    """

    return crud.get_donation_dashboard_summary(
        database_session
    )

# ==========================================================
# RECENT DONATIONS
# ==========================================================

@router.get("/recent")
def recent_donations(
    database_session: Session = Depends(get_db),
):

    donations = crud.get_recent_donations(
        database_session,
        5,
    )

    response = []

    for donation in donations:

        response.append(
            {
                "name": donation.donor.full_name,
                "blood_group": donation.donor.blood_group,
                "date": donation.donation_date,
            }
        )

    return response
@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
)
def create_donation(
    donation: DonationRecordCreate,
    database_session: Session = Depends(get_db),
):
    """
    Record a completed blood donation.
    """

    donor = crud.get_donor_by_id(
        database_session,
        donation.donor_id,
    )

    if donor is None:
        raise HTTPException(
            status_code=404,
            detail="Donor not found.",
        )

    blood_request = crud.get_blood_request_by_id(
        database_session,
        donation.blood_request_id,
    )

    if blood_request is None:
        raise HTTPException(
            status_code=404,
            detail="Blood request not found.",
        )

    donation_record = crud.create_donation_history(
        database_session=database_session,
        donor_id=donation.donor_id,
        blood_request_id=donation.blood_request_id,
        donation_date=donation.donation_date,
        units=donation.units,
        donation_type=donation.donation_type,
        remarks=donation.remarks,
    )

    crud.update_blood_request_status(
        database_session,
        blood_request,
        "Completed",
    )

    return {
        "message": "Donation recorded successfully.",
        "donation_id": donation_record.id,
    }