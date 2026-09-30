import sqlite3

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect, text

from backend.config.settings import get_settings


def _create_legacy_schema(path, *, duplicate_responses: bool = False) -> None:
    connection = sqlite3.connect(path)
    connection.executescript(
        """
        CREATE TABLE alembic_version (
            version_num VARCHAR(32) NOT NULL PRIMARY KEY
        );
        INSERT INTO alembic_version (version_num) VALUES ('f1a2b3c4d5e6');

        CREATE TABLE donor_responses (
            id INTEGER NOT NULL PRIMARY KEY,
            email_token_id INTEGER NOT NULL,
            donor_id INTEGER NOT NULL,
            blood_request_id INTEGER NOT NULL,
            response VARCHAR(20) NOT NULL,
            remarks TEXT,
            responded_at DATETIME NOT NULL
        );

        CREATE TABLE users (
            id INTEGER NOT NULL PRIMARY KEY,
            donor_id INTEGER,
            password_setup_token_hash VARCHAR(128),
            CONSTRAINT uq_users_donor_id UNIQUE (donor_id),
            UNIQUE (password_setup_token_hash)
        );

        CREATE TABLE donors (
            id INTEGER NOT NULL PRIMARY KEY
        );
        """
    )
    connection.execute(
        "INSERT INTO donor_responses "
        "(id, email_token_id, donor_id, blood_request_id, response, responded_at) "
        "VALUES (1, 10, 20, 30, 'YES', CURRENT_TIMESTAMP)"
    )
    if duplicate_responses:
        connection.execute(
            "INSERT INTO donor_responses "
            "(id, email_token_id, donor_id, blood_request_id, response, responded_at) "
            "VALUES (2, 11, 20, 30, 'NO', CURRENT_TIMESTAMP)"
        )
    connection.commit()
    connection.close()


def test_reconciliation_upgrades_a_legacy_prototype_schema(tmp_path, monkeypatch):
    database_path = tmp_path / "legacy-reconciliation.db"
    _create_legacy_schema(database_path)
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{database_path}")
    monkeypatch.setenv("DATABASE_ENCRYPTION_KEY", "")
    get_settings.cache_clear()
    try:
        command.upgrade(Config("alembic.ini"), "head")
        engine = create_engine(f"sqlite:///{database_path}")
        inspector = inspect(engine)
        response_columns = {
            column["name"]: column
            for column in inspector.get_columns("donor_responses")
        }
        response_unique_columns = {
            tuple(item["column_names"])
            for item in inspector.get_unique_constraints("donor_responses")
        }
        response_indexes = {item["name"] for item in inspector.get_indexes("donor_responses")}
        donor_columns = {
            column["name"]
            for column in inspector.get_columns("donors")
        }
        user_unique_columns = {
            tuple(item["column_names"])
            for item in inspector.get_unique_constraints("users")
        } | {
            tuple(item["column_names"])
            for item in inspector.get_indexes("users")
            if item["unique"]
        }
        with engine.connect() as connection:
            assert connection.execute(text("SELECT version_num FROM alembic_version")).scalar() == "1b2c3d4e5f6a"
        engine.dispose()

        assert response_columns["email_token_id"]["nullable"] is True
        assert ("donor_id", "blood_request_id") in response_unique_columns
        assert "ix_donor_responses_id" in response_indexes
        assert {
            "availability_paused_until",
            "travel_radius_km",
            "contact_window_start",
            "contact_window_end",
            "preferences_updated_at",
        } <= donor_columns
        assert ("donor_id",) in user_unique_columns
        assert ("password_setup_token_hash",) in user_unique_columns
    finally:
        get_settings.cache_clear()


def test_reconciliation_refuses_to_discard_duplicate_response_history(tmp_path, monkeypatch):
    database_path = tmp_path / "duplicate-responses.db"
    _create_legacy_schema(database_path, duplicate_responses=True)
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{database_path}")
    monkeypatch.setenv("DATABASE_ENCRYPTION_KEY", "")
    get_settings.cache_clear()
    try:
        with pytest.raises(RuntimeError, match="duplicate rows exist"):
            command.upgrade(Config("alembic.ini"), "head")
        connection = sqlite3.connect(database_path)
        try:
            assert connection.execute("SELECT COUNT(*) FROM donor_responses").fetchone()[0] == 2
            assert connection.execute("SELECT version_num FROM alembic_version").fetchone()[0] == "f1a2b3c4d5e6"
        finally:
            connection.close()
    finally:
        get_settings.cache_clear()
