"""Deployment contracts; no real credentials, cloud writes, or production DBs."""
import os
import secrets
import socket
import subprocess
import sys
import time
from pathlib import Path
from dataclasses import replace

import httpx
import pytest
from sqlalchemy.engine import make_url
from backend.config.settings import BASE_DIR, ConfigurationError, get_settings
from backend.config.database_url import normalize_database_url
from backend.security.database import create_database_engine
from start import server_options


@pytest.fixture
def config_env(monkeypatch):
    for name in ("RENDER", "APP_ENV", "BACKEND_URL", "FRONTEND_URL",
                 "ALLOWED_HOSTS", "RENDER_EXTERNAL_HOSTNAME", "RENDER_EXTERNAL_URL",
                 "DATABASE_TLS_MODE", "DATABASE_CA_FILE", "PORT", "HOST"):
        monkeypatch.delenv(name, raising=False)
    get_settings.cache_clear()
    yield monkeypatch
    get_settings.cache_clear()


@pytest.mark.parametrize("prefix", ["postgres", "postgresql", "postgresql+psycopg"])
def test_postgres_driver_and_verified_tls(config_env, prefix):
    value = normalize_database_url(prefix + "://user:p%40ss@db.example.org/app", production=True, on_render=False)
    url = make_url(value)
    assert url.drivername == "postgresql+psycopg"
    assert url.password == "p@ss"
    assert url.query["sslmode"] == "verify-full"
    assert Path(url.query["sslrootcert"]).is_file()
    engine = create_database_engine(replace(get_settings(), database_url=value))
    assert engine.dialect.driver == "psycopg"
    engine.dispose()  # No connection is made by this test.


def test_render_internal_tls_explicit(config_env):
    config_env.setenv("DATABASE_TLS_MODE", "render-internal")
    url = make_url(normalize_database_url("postgres://u:p@dpg-example-a/app", production=True, on_render=True))
    assert url.query["sslmode"] == "require"
    for host, on_render in [("db.example.org", True), ("dpg-example-a", False)]:
        with pytest.raises(ConfigurationError):
            normalize_database_url(f"postgres://u:p@{host}/app", production=True, on_render=on_render)


@pytest.mark.parametrize(
    "host",
    [
        "dpg-example-a",
        "dpg-example-a.oregon-postgres.render.com",
    ],
)
def test_render_managed_database_tls_is_detected(config_env, host):
    url = make_url(
        normalize_database_url(
            f"postgres://u:p@{host}/app?sslmode=require",
            production=True,
            on_render=True,
        )
    )
    assert url.query["sslmode"] == "require"


def test_render_managed_mode_rejects_non_render_host(config_env):
    config_env.setenv("DATABASE_TLS_MODE", "render-managed")
    with pytest.raises(ConfigurationError):
        normalize_database_url(
            "postgres://u:p@dpg-example-a.attacker.example/app?sslmode=require",
            production=True,
            on_render=True,
        )


@pytest.mark.parametrize("mode", ["disable", "prefer", "require"])
def test_public_tls_cannot_downgrade(config_env, mode):
    with pytest.raises(ConfigurationError):
        normalize_database_url("postgres://u:p@db.example.org/app?sslmode=" + mode, production=True, on_render=True)


def test_render_defaults_and_port(config_env):
    config_env.setenv("RENDER", "true")
    config_env.setenv("RENDER_EXTERNAL_URL", "https://bloodlink.onrender.com")
    config_env.setenv("RENDER_EXTERNAL_HOSTNAME", "bloodlink.onrender.com")
    config_env.setenv("DATABASE_URL", "postgres://u:p@db.example.org/app")
    config_env.setenv("PORT", "10001")
    settings = get_settings()
    assert settings.production and settings.on_render
    assert settings.frontend_url == settings.backend_url == "https://bloodlink.onrender.com"
    assert settings.allowed_hosts == ("bloodlink.onrender.com",)
    assert server_options(settings)["host"] == "0.0.0.0"
    assert server_options(settings)["port"] == 10001


def test_local_paths_and_origins(config_env, tmp_path):
    config_env.chdir(tmp_path)
    config_env.setenv("DATABASE_URL", "sqlite:///./bloodlink.db")
    settings = get_settings()
    assert Path(make_url(settings.database_url).database) == BASE_DIR / "bloodlink.db"
    assert settings.backend_url == "http://localhost:8000"
    assert server_options(settings)["host"] == "127.0.0.1"


@pytest.mark.parametrize("env", ["developmnt", "development"])
def test_render_refuses_insecure_environment(config_env, env):
    config_env.setenv("RENDER", "true")
    config_env.setenv("APP_ENV", env)
    with pytest.raises(ConfigurationError):
        get_settings()


def test_render_refuses_ephemeral_database(config_env):
    with pytest.raises(ConfigurationError):
        normalize_database_url("sqlite:///./bloodlink.db", production=True, on_render=True)


def test_health_does_not_disclose_errors(monkeypatch):
    import backend.main as main
    from fastapi.testclient import TestClient
    client = TestClient(main.app)
    monkeypatch.setattr(main, "verify_database_connection", lambda: None)
    assert client.get("/healthz").json() == {"status": "ok"}
    def unavailable():
        raise RuntimeError("private database credentials")
    monkeypatch.setattr(main, "verify_database_connection", unavailable)
    response = client.get("/healthz")
    assert response.status_code == 503
    assert response.json() == {"status": "unavailable"}
    assert response.headers["cache-control"] == "no-store"
    client.close()


@pytest.mark.parametrize("encrypted", [False, True])
def test_real_launcher_from_another_directory(tmp_path, encrypted):
    # Real socket, migrations, lifespan, administrator bootstrap, and cookies.
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        port = listener.getsockname()[1]
    password = secrets.token_urlsafe(32)
    env = dict(os.environ, RENDER="", APP_ENV="development",
               DATABASE_URL="sqlite:///" + str(tmp_path / "launch.db"),
               DATABASE_ENCRYPTION_KEY=secrets.token_hex(32) if encrypted else "",
               DATABASE_ENCRYPTION_KEY_FILE="", PORT=str(port), HOST="127.0.0.1",
               BACKEND_URL=f"http://127.0.0.1:{port}", FRONTEND_URL=f"http://127.0.0.1:{port}",
               DEFAULT_VOLUNTEER_USERNAME="launch-admin", DEFAULT_VOLUNTEER_PASSWORD=password,
               DATABASE_TLS_MODE="verify-full")
    process = subprocess.Popen([sys.executable, str(BASE_DIR / "start.py")], cwd=tmp_path,
                               env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        with httpx.Client(base_url=f"http://127.0.0.1:{port}", timeout=2) as client:
            deadline = time.monotonic() + 30
            while time.monotonic() < deadline:
                if process.poll() is not None:
                    pytest.fail("Launcher exited before readiness")
                try:
                    if client.get("/healthz").status_code == 200:
                        break
                except httpx.TransportError:
                    pass
                time.sleep(0.2)
            else:
                pytest.fail("Launcher did not become ready")
            assert client.get("/").status_code == 200
            response = client.post("/api/auth/login", data={"username": "launch-admin", "password": password},
                                   headers={"X-Session-Mode": "cookie"})
            assert response.status_code == 200
            assert "HttpOnly" in response.headers["set-cookie"]
    finally:
        process.terminate()
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)


def test_render_edge_http_has_no_redirect_loop(config_env):
    env = dict(os.environ, RENDER="true", APP_ENV="production",
               RENDER_EXTERNAL_URL="https://bloodlink.onrender.com",
               RENDER_EXTERNAL_HOSTNAME="bloodlink.onrender.com",
               BACKEND_URL="", FRONTEND_URL="", ALLOWED_HOSTS="",
               DATABASE_URL="postgres://u:p@dpg-example-a/app",
               DATABASE_TLS_MODE="render-internal")
    code = """
from fastapi.testclient import TestClient
import backend.main as main
main.verify_database_connection = lambda: None
client = TestClient(main.app, base_url="http://bloodlink.onrender.com")
assert client.get("/", follow_redirects=False).status_code == 200
response = client.get("/healthz", follow_redirects=False)
assert response.status_code == 200
assert response.headers["strict-transport-security"] == "max-age=31536000"
assert client.get("/docs").status_code == 404
assert client.get("/", headers={"host": "evil.example.org"}).status_code == 400
client.close()
"""
    result = subprocess.run([sys.executable, "-c", code], cwd=BASE_DIR, env=env,
                            capture_output=True, text=True, timeout=20)
    assert result.returncode == 0, result.stderr


def test_secure_origin_behind_http_proxy(system, monkeypatch):
    from backend.auth import dependencies
    from starlette.requests import Request
    client, sessions, tokens = system
    settings = replace(get_settings(), production=True, on_render=True)
    monkeypatch.setattr(dependencies, "get_settings", lambda: settings)
    token = tokens["admin"]["Authorization"].removeprefix("Bearer ")
    request = Request({"type": "http", "method": "POST", "scheme": "http",
                       "path": "/", "root_path": "", "query_string": b"",
                       "server": ("custom.example.org", 80),
                       "headers": [(b"host", b"custom.example.org"),
                                   (b"origin", b"https://custom.example.org"),
                                   (b"cookie", ("bloodlink_session=" + token).encode())]})
    with sessions() as db:
        assert dependencies.get_current_user(request, None, db).username == "admin"
