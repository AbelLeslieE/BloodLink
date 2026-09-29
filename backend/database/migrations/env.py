"""Alembic environment configuration for BloodLink."""

from __future__ import annotations

from logging.config import fileConfig

from alembic import context
from sqlalchemy import inspect

from backend.config.settings import get_settings
from backend.database.database import Base
from backend.security.database import create_database_engine
from backend.security.rate_limit import RateLimitBucket  # noqa: F401
from backend.database import models  # noqa: F401


config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Use the environment-provided URL instead of storing credentials in alembic.ini.
config.set_main_option("sqlalchemy.url", get_settings().database_url.replace("%", "%%"))
target_metadata = Base.metadata
_actual_user_unique_columns: set[tuple[str, ...]] = set()


def include_object(object_, name: str | None, type_: str, reflected: bool, compare_to) -> bool:
    """Ignore archives and equivalent SQLite uniqueness representations."""
    if reflected and name == "legacy_notifications" and type_ == "table":
        return False
    table = getattr(object_, "table", None)
    if reflected and table is not None and table.name == "legacy_notifications":
        return False
    if (
        table is not None
        and table.name == "users"
        and type_ in {"index", "unique_constraint"}
    ):
        columns = tuple(column.name for column in object_.columns)
        if reflected and type_ == "unique_constraint" and columns == ("donor_id",):
            # The ORM expresses this as a unique index; older migrations used
            # an equivalent named UNIQUE constraint.
            return False
        if (
            not reflected
            and compare_to is None
            and type_ in {"index", "unique_constraint"}
            and columns in _actual_user_unique_columns
        ):
            return False
    return True


def run_migrations_offline() -> None:
    """Run migrations without creating a database connection."""
    context.configure(
        url=config.get_main_option("sqlalchemy.url"),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        include_object=include_object,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations with a database connection from Alembic's engine."""
    connectable = create_database_engine(get_settings())

    # Own the SQLAlchemy transaction explicitly. The schema-equivalence
    # inspection below triggers SQLAlchemy 2.x autobegin; using begin() here
    # ensures Alembic's version stamp and any DDL are committed together rather
    # than rolled back when the connection closes.
    with connectable.begin() as connection:
        global _actual_user_unique_columns
        inspector = inspect(connection)
        if "users" in inspector.get_table_names():
            constraints = inspector.get_unique_constraints("users")
            indexes = inspector.get_indexes("users")
            _actual_user_unique_columns = {
                tuple(item.get("column_names") or ())
                for item in constraints
            } | {
                tuple(item.get("column_names") or ())
                for item in indexes
                if item.get("unique")
            }
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            include_object=include_object,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
