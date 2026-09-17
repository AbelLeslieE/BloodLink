from datetime import date, timedelta
from io import BytesIO
import os
import secrets
from alembic import command
from alembic.config import Config
from openpyxl import Workbook, load_workbook
from sqlalchemy import select, text
from backend.config.settings import get_settings
from backend.database.models import User, DonationHistory
from backend.security.database import create_database_engine
from backend.auth.security import create_password_reset_token


def blood_request():
    return {"patient_name": "Regression Patient", "case_details": "Regression only", "blood_group": "A+",
        "units_required": 1, "required_date": str(date.today()+timedelta(days=1)), "priority": "Normal",
        "hospital_name": "Regression Hospital", "hospital_location": "Test City",
        "contact_person": "Test Contact", "contact_phone": "9999900020"}


def test_request_match_response_confirmation_rewards_and_certificate(system):
    client, sessions, tokens = system
    created = client.post("/api/blood-requests", json=blood_request(), headers=tokens["admin"])
    assert created.status_code == 201, created.text
    request_id = created.json()["id"]
    matched = client.post("/api/match/find", json={"blood_request_id": request_id}, headers=tokens["admin"])
    assert matched.status_code == 200 and matched.json()["total_matches"] == 2
    response = client.post(f"/api/donor-dashboard/requests/{request_id}/response", json={"response": "Yes"}, headers=tokens["donor1"])
    assert response.status_code == 200 and response.json()["points_awarded"] == 0
    confirmation = f"/api/admin/donations/requests/{request_id}/donors/1/confirm"
    assert client.post(confirmation, headers=tokens["donor1"]).status_code == 403
    confirmed = client.post(confirmation, headers=tokens["admin"])
    assert confirmed.status_code == 200 and confirmed.json()["points_awarded"] == 100
    repeated = client.post(confirmation, headers=tokens["admin"])
    assert repeated.status_code == 200 and repeated.json()["already_confirmed"]
    with sessions() as db:
        assert len(db.scalars(select(DonationHistory)).all()) == 1
    certificates = client.get("/api/donor-dashboard/certificates", headers=tokens["donor1"])
    assert certificates.status_code == 200 and len(certificates.json()) == 1
    download_url = certificates.json()[0]["download_url"]
    pdf = client.get(download_url, headers=tokens["donor1"])
    assert pdf.status_code == 200 and pdf.content.startswith(b"%PDF")
    assert client.get(download_url, headers=tokens["donor2"]).status_code in {403, 404}
    assert client.get("/api/donation-history", headers=tokens["admin"]).status_code == 200
    for kind in ("excel", "pdf"):
        assert client.get(f"/api/donation-history/export/{kind}", headers=tokens["admin"]).status_code == 200


def test_excel_import_export(system):
    client, _, tokens = system
    workbook = Workbook()
    workbook.active.append(["Full Name", "Phone", "Blood Group", "Email"])
    workbook.active.append(["Import Test", "9999900040", "O+", "import@example.org"])
    data = BytesIO(); workbook.save(data)
    response = client.post("/api/donors/import", files={"file": ("donors.xlsx", data.getvalue())}, headers=tokens["admin"])
    assert response.status_code == 200 and response.json()["imported"] == 1, response.text
    output = client.get("/api/donors/export", headers=tokens["admin"])
    assert output.status_code == 200
    assert load_workbook(BytesIO(output.content)).active.max_row == 4


def test_password_reset_single_use_and_old_sessions_revoked(system):
    client, sessions, tokens = system
    token = create_password_reset_token("donor1", 0)
    data = {"token": token, "new_password": "ChangedPassword123"}
    assert client.post("/api/auth/password-reset/confirm", json=data).status_code == 200
    assert client.post("/api/auth/password-reset/confirm", json=data).status_code == 400
    assert client.get("/api/auth/me", headers=tokens["donor1"]).status_code == 401
    assert client.post("/api/auth/login", data={"username": "donor1", "password": "ChangedPassword123"}).status_code == 200


def test_alembic_on_encrypted_database(tmp_path, monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "sqlite:///" + str(tmp_path / "migration-encrypted.db"))
    monkeypatch.setenv("DATABASE_ENCRYPTION_KEY", secrets.token_hex(32))
    get_settings.cache_clear()
    try:
        command.upgrade(Config("alembic.ini"), "head")
        engine = create_database_engine(get_settings())
        with engine.connect() as connection:
            assert connection.execute(text("SELECT version_num FROM alembic_version")).scalar() == "02a_security_rate_limits"
            assert connection.execute(text("SELECT COUNT(*) FROM security_rate_limits")).scalar() == 0
        engine.dispose()
    finally:
        get_settings.cache_clear()
