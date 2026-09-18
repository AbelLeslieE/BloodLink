"""
Create the default administrator account for BloodLink.
Run this once after creating the database.
"""

import logging
import os

from backend.database.database import SessionLocal
from backend.database import crud
from backend.database.schemas import UserCreate
from backend.auth.security import hash_password
from backend.config.settings import get_default_volunteer_credentials, get_settings


logger = logging.getLogger(__name__)


def create_admin():

    db = SessionLocal()

    try:

        if crud.volunteer_exists(db):
            if get_settings().production and os.getenv("DEFAULT_VOLUNTEER_PASSWORD"):
                # A wiped database would silently recreate an administrator
                # with this known value; it is only needed for the first boot.
                logger.warning(
                    "DEFAULT_VOLUNTEER_PASSWORD is still configured although accounts exist; remove it from the environment."
                )
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
                email=credentials.email,
                phone="9999999999",
                active=True,
            ),
        )

        logger.info("Default administrator account created (id %s). Change its password after first sign-in.", admin.id)

    finally:

        db.close()


if __name__ == "__main__":
    create_admin()
