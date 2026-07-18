"""Environment-backed application configuration."""

from __future__ import annotations

import os
from pathlib import Path
from dataclasses import dataclass
from functools import lru_cache

from dotenv import load_dotenv

# Load the .env file from the project root
BASE_DIR = Path(__file__).resolve().parents[2]
load_dotenv(BASE_DIR / ".env")


class ConfigurationError(RuntimeError):
    """Raised when a required environment setting is missing or invalid."""


@dataclass(frozen=True)
class Settings:
    """Runtime settings loaded exclusively from environment variables."""

    database_url: str
    database_pool_size: int
    database_max_overflow: int
    secret_key: str
    jwt_algorithm: str
    access_token_expire_minutes: int


@dataclass(frozen=True)
class DefaultVolunteerCredentials:
    """Bootstrap credentials used only by the default-user setup script."""

    username: str
    password: str


def _required_value(name: str) -> str:
    """Return a required non-empty environment variable."""
    value = os.getenv(name)
    if not value or not value.strip():
        raise ConfigurationError(f"{name} environment variable is required.")
    return value.strip()


def _positive_integer(name: str, default: int) -> int:
    """Read a positive integer setting from the environment."""
    raw_value = os.getenv(name, str(default))
    try:
        value = int(raw_value)
    except ValueError as error:
        raise ConfigurationError(
            f"{name} environment variable must be an integer."
        ) from error

    if value <= 0:
        raise ConfigurationError(
            f"{name} environment variable must be greater than zero."
        )
    return value


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Build and cache the application settings for the current process."""
    return Settings(
        database_url=_required_value("DATABASE_URL"),
        database_pool_size=_positive_integer("DATABASE_POOL_SIZE", default=5),
        database_max_overflow=_positive_integer(
            "DATABASE_MAX_OVERFLOW",
            default=10,
        ),
        secret_key=_required_value("SECRET_KEY"),
        jwt_algorithm=_required_value("JWT_ALGORITHM"),
        access_token_expire_minutes=_positive_integer(
            "ACCESS_TOKEN_EXPIRE_MINUTES",
            default=60,
        ),
    )


def get_default_volunteer_credentials() -> DefaultVolunteerCredentials:
    """Load initial volunteer credentials without embedding them in source code."""
    username = os.getenv("DEFAULT_VOLUNTEER_USERNAME", "volunteer").strip()
    if not username:
        raise ConfigurationError(
            "DEFAULT_VOLUNTEER_USERNAME environment variable cannot be empty."
        )

    return DefaultVolunteerCredentials(
        username=username,
        password=_required_value("DEFAULT_VOLUNTEER_PASSWORD"),
    )
