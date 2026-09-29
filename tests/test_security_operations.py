"""Regression coverage for the administrator Technical Portal controls."""

from backend.services.mfa_service import totp_code


SAME_ORIGIN = {"Origin": "http://testserver"}


def cookie_login(client, username="admin", password="AdminPassword123", mfa_code=None):
    data = {"username": username, "password": password}
    if mfa_code:
        data["mfa_code"] = mfa_code
    return client.post(
        "/api/auth/login",
        data=data,
        headers={"X-Session-Mode": "cookie"},
    )


def test_login_creates_independently_visible_session(system):
    client, _, _ = system
    assert cookie_login(client).status_code == 200
    response = client.get("/api/security/sessions")
    assert response.status_code == 200
    active = [item for item in response.json() if item["active"]]
    assert len(active) == 1
    assert active[0]["current"] is True
    assert active[0]["username"] == "admin"


def test_mfa_enrollment_recovery_login_and_audit(system):
    client, _, _ = system
    assert cookie_login(client).status_code == 200
    setup = client.post(
        "/api/security/mfa/setup",
        json={"current_password": "AdminPassword123"},
        headers=SAME_ORIGIN,
    )
    assert setup.status_code == 200
    payload = setup.json()
    assert payload["qr_data_uri"].startswith("data:image/png;base64,")
    code, _ = totp_code(payload["secret"])
    confirmed = client.post(
        "/api/security/mfa/confirm", json={"code": code}, headers=SAME_ORIGIN
    )
    assert confirmed.status_code == 200
    recovery_code = confirmed.json()["recovery_codes"][0]

    assert client.post("/api/auth/logout", headers=SAME_ORIGIN).status_code == 200
    challenge = cookie_login(client)
    assert challenge.status_code == 428
    assert challenge.json()["detail"]["code"] == "MFA_REQUIRED"
    assert cookie_login(client, mfa_code=recovery_code).status_code == 200

    audit = client.get("/api/admin/technical/audit-logs?category=MFA")
    assert audit.status_code == 200
    actions = {item["action"] for item in audit.json()["items"]}
    assert {"MFA_SETUP_STARTED", "MFA_ENABLED"}.issubset(actions)
    assert all(item["integrity_valid"] for item in audit.json()["items"])


def test_encrypted_backup_create_verify_download_delete(system, monkeypatch, tmp_path):
    client, _, tokens = system
    monkeypatch.setenv("BACKUP_DIRECTORY", str(tmp_path / "backups"))
    created = client.post("/api/admin/technical/backups", headers=tokens["admin"])
    assert created.status_code == 201, created.text
    backup = created.json()
    assert backup["status"] == "READY"
    assert backup["checksum_sha256"]
    assert backup["row_count"] > 0

    verified = client.post(
        f"/api/admin/technical/backups/{backup['id']}/verify",
        headers=tokens["admin"],
    )
    assert verified.status_code == 200
    assert verified.json()["valid"] is True
    downloaded = client.get(
        f"/api/admin/technical/backups/{backup['id']}/download",
        headers=tokens["admin"],
    )
    assert downloaded.status_code == 200
    assert downloaded.content
    assert b"admin@example.org" not in downloaded.content

    deleted = client.delete(
        f"/api/admin/technical/backups/{backup['id']}",
        headers=tokens["admin"],
    )
    assert deleted.status_code == 200
    assert not list((tmp_path / "backups").glob("*.blbackup"))


def test_technical_portal_is_admin_only(system):
    client, _, tokens = system
    assert client.get("/api/admin/technical/summary", headers=tokens["admin"]).status_code == 200
    assert client.get("/api/admin/technical/summary", headers=tokens["donor1"]).status_code == 403
