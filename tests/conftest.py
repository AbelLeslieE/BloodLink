"""All regression tests use disposable databases and disabled external delivery."""
import os
import secrets
import tempfile
from pathlib import Path

_isolation = tempfile.TemporaryDirectory(prefix="bloodlink-security-tests-")
os.environ.update({
    "DATABASE_URL": "sqlite:///" + str(Path(_isolation.name) / "bootstrap.db"),
    "SECRET_KEY": secrets.token_hex(32), "JWT_ALGORITHM": "HS256",
    "BACKEND_URL": "http://testserver", "FRONTEND_URL": "http://testserver",
    "APP_ENV": "development", "DEFAULT_VOLUNTEER_PASSWORD": secrets.token_urlsafe(32),
    "SMTP_HOST": "", "SMTP_USERNAME": "", "SMTP_PASSWORD": "", "RESEND_API_KEY": "",
    "VAPID_PRIVATE_KEY": "", "VAPID_PUBLIC_KEY": "", "DATABASE_ENCRYPTION_KEY": "",
    "DATABASE_ENCRYPTION_KEY_FILE": "",
})

import pytest
from dataclasses import replace
from backend.config.settings import get_settings
from backend.security.database import create_database_engine
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from backend.main import app
from backend.database.database import Base, get_db
from backend.database.models import Donor, User
from backend.auth.security import hash_password, create_access_token
from backend.security import rate_limit


@pytest.fixture(params=["plain", "encrypted"])
def system(tmp_path, monkeypatch, request):
    if request.param == "encrypted":
        monkeypatch.setenv("DATABASE_ENCRYPTION_KEY", secrets.token_hex(32))
    engine = create_database_engine(replace(get_settings(), database_url="sqlite:///" + str(tmp_path / "test.db")))
    @event.listens_for(engine, "connect")
    def foreign_keys(connection, _):
        connection.execute("PRAGMA foreign_keys=ON")
    Base.metadata.create_all(engine)
    sessions = sessionmaker(bind=engine, expire_on_commit=False)
    monkeypatch.setattr(rate_limit, "SessionLocal", sessions)
    def override_db():
        with sessions() as db:
            yield db
    app.dependency_overrides[get_db] = override_db
    with sessions.begin() as db:
        donors = [Donor(donor_code=f"TEST-{i}", full_name=f"Test Donor {i}", blood_group="A+",
                        phone=f"999990000{i}", email=f"donor{i}@example.org") for i in (1, 2)]
        db.add_all(donors)
        db.flush()
        users = [User(username="admin", full_name="Test Admin", department="NSS", role="Administrator",
                      email="admin@example.org", phone="9999900000", password_hash=hash_password("AdminPassword123"))]
        users += [User(username=f"donor{i}", full_name=f"Test Donor {i}", department="NSS", role="Donor",
                       email=f"donor{i}@example.org", phone=f"999990000{i}", donor_id=donors[i-1].id,
                       password_hash=hash_password("DonorPassword123")) for i in (1, 2)]
        db.add_all(users)
    client = TestClient(app)
    tokens = {name: {"Authorization": "Bearer " + create_access_token(name, 0)} for name in ("admin", "donor1", "donor2")}
    yield client, sessions, tokens
    client.close()
    app.dependency_overrides.clear()
    engine.dispose()
