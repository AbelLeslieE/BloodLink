"""
Create the default administrator account for BloodLink.
Run this once after creating the database.
"""

from backend.database.database import SessionLocal
from backend.database import crud
from backend.database.schemas import UserCreate
from backend.auth.security import hash_password
from backend.config.settings import get_default_volunteer_credentials


def create_admin():

    db = SessionLocal()

    try:

        if crud.volunteer_exists(db):
            print("Default administrator already exists.")
            return

        credentials = get_default_volunteer_credentials()
        admin = crud.create_user(
            db,
            UserCreate(
                username=credentials.username,
                password_hash=hash_password(credentials.password),
                full_name="System Administrator",
                department="Blood Bank",
                role="Administrator",
                email="admin@bloodlink.local",
                phone="9999999999",
                active=True,
            ),
        )

        print("Default administrator created successfully.")
        print(f"Username : {admin.username}")
        print("Password was read from DEFAULT_VOLUNTEER_PASSWORD.")

    finally:

        db.close()


if __name__ == "__main__":
    create_admin()
