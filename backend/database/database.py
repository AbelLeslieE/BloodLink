"""SQLAlchemy engine, session, and FastAPI database dependency setup."""

from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import MetaData, create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from backend.config.settings import get_settings
from backend.security.database import create_database_engine


# Stable names keep Alembic-generated constraints consistent across environments.
NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    """Base class inherited by every SQLAlchemy ORM model."""

    metadata = MetaData(naming_convention=NAMING_CONVENTION)


settings = get_settings()

engine: Engine = create_database_engine(settings)

# Each request receives its own session from this factory through get_db().
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    class_=Session,
)


def get_db() -> Generator[Session, None, None]:
    """Yield a database session and close it after the request completes."""
    database_session = SessionLocal()
    try:
        yield database_session
    finally:
        database_session.close()


def verify_database_connection() -> None:
    """Confirm that the configured database is reachable."""
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))
