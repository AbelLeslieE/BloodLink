"""Portable database URLs and explicit transport policy. Never log these URLs."""
import os
import re
from pathlib import Path
from sqlalchemy.engine import make_url
from backend.config.settings import BASE_DIR, ConfigurationError


def normalize_database_url(value: str, *, production: bool, on_render: bool) -> str:
    try:
        url = make_url(value)
    except Exception:
        raise ConfigurationError("DATABASE_URL is not a valid SQLAlchemy URL.") from None
    if url.drivername in {"postgres", "postgresql", "postgresql+psycopg"}:
        url = url.set(drivername="postgresql+psycopg")
        mode = os.getenv("DATABASE_TLS_MODE", "verify-full").strip()
        if mode not in {"verify-full", "render-internal"}:
            raise ConfigurationError("DATABASE_TLS_MODE must be verify-full or render-internal.")
        query = dict(url.query)
        if mode == "render-internal":
            # Explicit exception only for Render's private, single-label DB host.
            if not on_render or not re.fullmatch(r"dpg-[a-z0-9-]+", url.host or ""):
                raise ConfigurationError("render-internal TLS requires Render and an internal dpg-* hostname.")
            if query.get("sslmode", "require") != "require":
                raise ConfigurationError("Internal Render database requires sslmode=require.")
            query["sslmode"] = "require"
        elif production:
            if query.get("sslmode", "verify-full") != "verify-full":
                raise ConfigurationError("Public production PostgreSQL requires sslmode=verify-full.")
            import certifi
            query["sslmode"] = "verify-full"
            query.setdefault("sslrootcert", os.getenv("DATABASE_CA_FILE", "").strip() or certifi.where())
        query.setdefault("connect_timeout", "5")
        return url.set(query=query).render_as_string(hide_password=False)
    if url.drivername not in {"sqlite", "sqlite+pysqlite"}:
        raise ConfigurationError("Supported databases are SQLite and PostgreSQL (psycopg).")
    if on_render:
        raise ConfigurationError("Render requires PostgreSQL; ephemeral SQLite would lose data.")
    if url.query:
        raise ConfigurationError("SQLite URL query options are unsupported; use a filesystem path.")
    if url.database and url.database != ":memory:":
        path = Path(url.database)
        if not path.is_absolute():
            path = BASE_DIR / path
        url = url.set(database=str(path.resolve()))
    return url.render_as_string(hide_password=False)
