"""Environment-backed application configuration."""

from __future__ import annotations

import os
from pathlib import Path
from urllib.parse import urlsplit
from dataclasses import dataclass
from functools import lru_cache

from dotenv import load_dotenv

# Load the .env file from the project root
BASE_DIR = Path(__file__).resolve().parents[2]
if os.getenv("RENDER", "").lower() != "true":
    load_dotenv(BASE_DIR / ".env")


class ConfigurationError(RuntimeError):
    """Raised when a required environment setting is missing or invalid."""


@dataclass(frozen=True)
class Settings:
    """Runtime settings loaded exclusively from environment variables."""

    # ==========================================================
    # Database
    # ==========================================================

    database_url: str
    database_pool_size: int
    database_max_overflow: int

    # ==========================================================
    # Security
    # ==========================================================

    secret_key: str
    jwt_algorithm: str
    access_token_expire_minutes: int

    # ==========================================================
    # Email delivery
    # ==========================================================

    resend_api_key: str
    email_from: str
    smtp_host: str
    smtp_port: int
    smtp_username: str
    smtp_password: str
    smtp_from: str

    # ==========================================================
    # Application URLs
    # ==========================================================

    backend_url: str
    frontend_url: str

    # Web Push. The private VAPID key is deliberately server-only. Leaving
    # these unset disables push delivery without preventing the website from
    # starting (useful for local development).
    vapid_public_key: str
    vapid_private_key: str
    vapid_subject: str
    on_render: bool = False
    production: bool = False
    allowed_hosts: tuple[str, ...] = ("localhost", "127.0.0.1", "testserver")


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
    """Build and cache the application settings."""

    on_render = os.getenv("RENDER", "").lower() == "true"
    environment = os.getenv("APP_ENV", "production" if on_render else "development").strip().lower()
    if environment not in {"development", "production", "test"}:
        raise ConfigurationError("APP_ENV must be development, test, or production.")
    if on_render and environment != "production":
        raise ConfigurationError("Render must run with APP_ENV=production.")
    production = environment == "production"
    if _required_value("JWT_ALGORITHM") != "HS256":
        raise ConfigurationError("JWT_ALGORITHM must be HS256 for this symmetric-key application.")
    if (len(_required_value("SECRET_KEY").encode("utf-8")) < 32
            or _required_value("SECRET_KEY").startswith("REPLACE_")):
        raise ConfigurationError("SECRET_KEY must contain at least 32 bytes; use a random secret.")
    default_url = os.getenv("RENDER_EXTERNAL_URL", "") if on_render else "http://localhost:" + str(_positive_integer("PORT", 8000))
    backend_url = os.getenv("BACKEND_URL", "").strip() or default_url
    frontend_url = os.getenv("FRONTEND_URL", "").strip() or backend_url
    for name, value in (("BACKEND_URL", backend_url), ("FRONTEND_URL", frontend_url)):
        parsed = urlsplit(value)
        if (parsed.scheme not in ({"https"} if production else {"http", "https"})
                or not parsed.hostname or parsed.username or parsed.password
                or parsed.query or parsed.fragment or parsed.path not in {"", "/"}):
            raise ConfigurationError(f"{name} must be an absolute {'HTTPS' if production else 'HTTP(S)'} origin.")
    hosts = tuple(h.strip() for h in os.getenv("ALLOWED_HOSTS", "").split(",") if h.strip())
    if not hosts:
        hosts = tuple(dict.fromkeys(filter(None, [
            urlsplit(backend_url).hostname, urlsplit(frontend_url).hostname,
            os.getenv("RENDER_EXTERNAL_HOSTNAME", "") if on_render else "127.0.0.1",
        ])))
    if production and any("*" in h for h in hosts):
        raise ConfigurationError("Production ALLOWED_HOSTS cannot contain wildcards.")
    from backend.config.database_url import normalize_database_url
    database_url = normalize_database_url(
        _required_value("DATABASE_URL") if production else os.getenv("DATABASE_URL", "") or "sqlite:///./bloodlink.db",
        production=production, on_render=on_render,
    )
    return Settings(
        on_render=on_render,
        production=production,
        allowed_hosts=hosts or ("localhost", "127.0.0.1", "testserver"),

        # Database
        database_url=database_url,
        database_pool_size=_positive_integer("DATABASE_POOL_SIZE", 5),
        database_max_overflow=_positive_integer("DATABASE_MAX_OVERFLOW", 10),

        # Security
        secret_key=_required_value("SECRET_KEY"),
        jwt_algorithm=_required_value("JWT_ALGORITHM"),
        access_token_expire_minutes=_positive_integer(
            "ACCESS_TOKEN_EXPIRE_MINUTES",
            60,
        ),

        # Email (optional during development). SMTP takes precedence when
        # configured. Render free services block SMTP; use Resend there.
        resend_api_key=os.getenv("RESEND_API_KEY", ""),
        email_from=os.getenv("EMAIL_FROM", ""),
        smtp_host=os.getenv("SMTP_HOST", "").strip(),
        smtp_port=_positive_integer("SMTP_PORT", 587),
        smtp_username=os.getenv("SMTP_USERNAME", "").strip(),
        smtp_password=os.getenv("SMTP_PASSWORD", "").strip(),
        smtp_from=os.getenv("SMTP_FROM", "").strip(),

        # Application URLs
        backend_url=backend_url.rstrip("/"),
        frontend_url=frontend_url.rstrip("/"),

        vapid_public_key=os.getenv("VAPID_PUBLIC_KEY", "").strip(),
        vapid_private_key=os.getenv("VAPID_PRIVATE_KEY", "").strip(),
        vapid_subject=os.getenv("VAPID_SUBJECT", "").strip(),
    )
def get_default_volunteer_credentials() -> DefaultVolunteerCredentials:
    """Load initial volunteer credentials."""

    username = os.getenv(
        "DEFAULT_VOLUNTEER_USERNAME",
        "volunteer",
    ).strip()

    if not username:
        raise ConfigurationError(
            "DEFAULT_VOLUNTEER_USERNAME cannot be empty."
        )

    return DefaultVolunteerCredentials(
        username=username,
        password=_required_value("DEFAULT_VOLUNTEER_PASSWORD"),
    )
