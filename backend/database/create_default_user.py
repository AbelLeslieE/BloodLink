"""Create the initial NSS volunteer account when no user exists."""

from __future__ import annotations

from backend.auth.security import hash_password
from backend.config.settings import get_default_volunteer_credentials
from backend.database import crud
from backend.database.database import SessionLocal
from backend.database.schemas import UserCreate


def create_default_user() -> None:
    """Create the configured initial volunteer account exactly once."""
    database_session = SessionLocal()
    try:
        if crud.volunteer_exists(database_session):
            print("A volunteer account already exists. Default user was not created.")
            return

        credentials = get_default_volunteer_credentials()
        user = crud.create_user(
            database_session,
            UserCreate(
                username=credentials.username,
                password_hash=hash_password(credentials.password),
                full_name="NSS Volunteer",
                active=True,
            ),
        )
        print(f"Default volunteer account created for username '{user.username}'.")
    finally:
        database_session.close()


if __name__ == "__main__":
    create_default_user()
