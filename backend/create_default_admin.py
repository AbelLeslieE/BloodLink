"""
Create the default administrator account for BloodLink.
Run this once after creating the database.
"""

from backend.database.database import SessionLocal
from backend.database import crud
from backend.database.schemas import UserCreate
from backend.auth.security import hash_password


def create_admin():

    db = SessionLocal()

    try:

        if crud.volunteer_exists(db):
            print("Default administrator already exists.")
            return

        admin = crud.create_user(
            db,
            UserCreate(
                username="admin",
                password_hash=hash_password("Admin@123"),
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
        print("Password : Admin@123")

    finally:

        db.close()


if __name__ == "__main__":
    create_admin()