"""
Create the default administrator account for BloodLink.
Run this once after creating the database.
"""

from backend.database.database import SessionLocal
from backend.database.models import User
from backend.auth.security import hash_password

def create_admin():

    db = SessionLocal()

    try:

        existing = db.query(User).filter(
            User.username == "admin"
        ).first()

        if existing:
            print("Default administrator already exists.")
            return

        admin = User(
            username="admin",
            password_hash=hash_password("Admin@123"),
            full_name="System Administrator",
            active=True,
        )

        db.add(admin)
        db.commit()

        print("Default administrator created successfully.")

        print("Username : admin")
        print("Password : Admin@123")

    finally:

        db.close()


if __name__ == "__main__":
    create_admin()