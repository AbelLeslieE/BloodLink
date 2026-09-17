"""SQLCipher connections: full SQLite encryption without changing query semantics."""
import os
import re
from pathlib import Path
from sqlalchemy import create_engine, event
from backend.config.settings import BASE_DIR, ConfigurationError


def encryption_key() -> str | None:
    key = os.getenv("DATABASE_ENCRYPTION_KEY", "").strip()
    key_file = os.getenv("DATABASE_ENCRYPTION_KEY_FILE", "").strip()
    if key and key_file:
        raise ConfigurationError("Configure one database key source, not both.")
    if key_file:
        path = Path(key_file)
        if not path.is_absolute():
            path = BASE_DIR / path
        key = path.read_text(encoding="ascii").strip()
    if key and not re.fullmatch(r"[0-9a-fA-F]{64}", key):
        raise ConfigurationError("Database encryption key must be 32 random bytes encoded as 64 hex characters.")
    return key or None


def configure_sqlcipher(connection, key: str) -> None:
    # PRAGMA cannot bind parameters. Only the strictly validated hex key is
    # interpolated; never log this statement or put the key in a database URL.
    if not re.fullmatch(r"[0-9a-fA-F]{64}", key):
        raise ConfigurationError("Invalid database encryption key.")
    connection.execute(f'''PRAGMA key = "x'{key}'"''')
    if not connection.execute("PRAGMA cipher_version").fetchone():
        raise ConfigurationError("SQLCipher is unavailable; refusing plaintext fallback.")
    # The Windows community wheel crashes with cipher_memory_security=ON.
    # SQLCipher page encryption/authentication is independent of this optional
    # heap-wiping feature; leave its supported default unchanged.
    connection.execute("PRAGMA temp_store = MEMORY")
    connection.execute("SELECT count(*) FROM sqlite_master").fetchone()


def create_database_engine(settings):
    key = encryption_key()
    if settings.database_url.startswith("sqlite"):
        if settings.production and not key:
            raise ConfigurationError("Production SQLite requires DATABASE_ENCRYPTION_KEY or its key file.")
        options = {"connect_args": {"check_same_thread": False}, "hide_parameters": True}
        if key:
            try:
                from sqlcipher3 import dbapi2
            except ImportError as error:
                raise ConfigurationError("Install requirements-security.txt for SQLCipher; no plaintext fallback.") from error
            options["module"] = dbapi2
        engine = create_engine(settings.database_url, **options)

        @event.listens_for(engine, "connect")
        def secure_connection(connection, _):
            if key:
                configure_sqlcipher(connection, key)
            connection.execute("PRAGMA foreign_keys = ON")
        return engine
    if key:
        raise ConfigurationError("SQLCipher keys apply only to SQLite. Configure PostgreSQL volume/backup encryption with your host.")
    return create_engine(settings.database_url, pool_pre_ping=True,
                         pool_size=settings.database_pool_size,
                         max_overflow=settings.database_max_overflow,
                         hide_parameters=True)
