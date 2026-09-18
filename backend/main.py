"""FastAPI application initialization for BloodLink."""

from __future__ import annotations

import logging
import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import DataError, OperationalError
from starlette.middleware.trustedhost import TrustedHostMiddleware
from starlette.middleware.httpsredirect import HTTPSRedirectMiddleware
from backend.config.settings import forwarded_allow_ips, get_settings
from backend.security.middleware import SecurityMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from backend.database.database import (
    engine,
    verify_database_connection,
)
from backend.routers.auth import router as auth_router
from backend.routers.password_reset import router as password_reset_router
from backend.routers.blood_requests import router as blood_requests_router
from backend.routers.donors import router as donors_router
logger = logging.getLogger(__name__)
from backend.security.logging import RedactAccessLog
logging.getLogger("uvicorn.access").addFilter(RedactAccessLog())
from backend.routers.donor_matching import (
    router as donor_matching_router,
)
from backend.routers.email_router import router as email_router
from backend.routers.notifications import (
    router as notifications_router,
)
from backend.routers.donations import (
    router as donations_router,
)
from backend.create_default_admin import create_admin
from backend.routers import dashboard_router
from backend.routers.user_routes import router as users_router
from backend.routers.donor_portal import admin_router as donation_admin_router
from backend.routers.donor_portal import donor_router
from backend.routers.donor_registration import router as donor_registration_router
from backend.routers.donation_history import router as donation_history_router
from backend.routers.push_notifications import router as push_notifications_router
from backend.routers.diagnostics import router as diagnostics_router
# ==========================================================
# Paths
# ==========================================================

BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"

# ==========================================================
# Lifespan
# ==========================================================

@asynccontextmanager
async def lifespan(_: FastAPI):
    """
    Initialize the database, create the default administrator
    if needed, verify connectivity, and clean up resources
    on shutdown.
    """

    # Schema changes are applied exclusively through Alembic.  create_all()
    # silently leaves existing databases with missing columns.

    create_admin()

    # ------------------------------------------------------
    # Verify database connection
    # ------------------------------------------------------

    verify_database_connection()

    logger.info("Database initialized successfully.")
    settings = get_settings()
    logger.info(
        "Security posture: production=%s docs_disabled=%s on_render=%s forwarded_allow_ips=%s "
        "database_tls_mode=%s bootstrap_password_configured=%s",
        settings.production, settings.production, settings.on_render, forwarded_allow_ips(settings),
        os.getenv("DATABASE_TLS_MODE", "").strip() or "automatic", bool(os.getenv("DEFAULT_VOLUNTEER_PASSWORD")),
    )

    try:
        yield

    finally:

        engine.dispose()

        logger.info("Database engine disposed.")
# ==========================================================
# FastAPI App
# ==========================================================

app = FastAPI(
    title="BloodLink",
    description="Blood donor management system for NSS volunteers.",
    version="0.1.0",
    lifespan=lifespan,
    docs_url=None if get_settings().production else "/docs",
    redoc_url=None if get_settings().production else "/redoc",
    openapi_url=None if get_settings().production else "/openapi.json",
)
app.add_middleware(SecurityMiddleware, production=get_settings().production)
if get_settings().production:
    # Render redirects at its TLS edge and forwards HTTP internally.
    # Redirecting again here would loop unless arbitrary proxy headers were trusted.
    if not get_settings().on_render:
        app.add_middleware(HTTPSRedirectMiddleware)
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=list(get_settings().allowed_hosts))


_NOT_FOUND = JSONResponse(status_code=404, content={"detail": "Resource not found."}, headers={"Cache-Control": "no-store"})


@app.exception_handler(OverflowError)
async def oversized_identifier(request, error):
    # SQLite binds an id wider than 64 bits by raising OverflowError directly;
    # such an id cannot match any row, so report a clean 404, never a 500.
    return _NOT_FOUND


@app.exception_handler(OperationalError)
@app.exception_handler(DataError)
async def out_of_range_identifier(request, error):
    # PostgreSQL surfaces an out-of-range integer id as a wrapped driver error.
    original = getattr(error, "orig", None)
    text = str(original).lower()
    if isinstance(original, OverflowError) or "out of range" in text or "too large" in text:
        return _NOT_FOUND
    logger.exception("Unhandled database error")
    return JSONResponse(status_code=500, content={"detail": "A database error occurred."}, headers={"Cache-Control": "no-store"})


@app.exception_handler(RequestValidationError)
async def safe_validation_error(request, error):
    # Pydantic errors normally echo submitted passwords and medical data.
    details = [{"loc": e["loc"], "msg": e["msg"], "type": e["type"]} for e in error.errors()]
    return JSONResponse(status_code=422, content={"detail": details}, headers={"Cache-Control": "no-store"})


# ==========================================================
# Routers
# ==========================================================

@app.get("/healthz", include_in_schema=False)
def health():
    try:
        verify_database_connection()
    except Exception:
        # Never disclose connection URLs, SQL, or credentials in health output.
        return JSONResponse({"status": "unavailable"}, status_code=503)
    return {"status": "ok"}


app.include_router(auth_router)
app.include_router(password_reset_router)
app.include_router(users_router)
app.include_router(donor_registration_router)
app.include_router(donor_router)
app.include_router(donation_admin_router)
app.include_router(donation_history_router)
app.include_router(
    blood_requests_router
)
app.include_router(
    donors_router
)
app.include_router(
    donor_matching_router
)
app.include_router(email_router)
app.include_router(
    notifications_router
)
app.include_router(push_notifications_router)
app.include_router(diagnostics_router)

app.include_router(
    donations_router,
    prefix="/api/donations",
    tags=["Donations"],
)

app.include_router(
    dashboard_router.router,
)

# ==========================================================
# Static Files
# ==========================================================

app.mount(
    "/static",
    StaticFiles(directory=str(FRONTEND_DIR)),
    name="static",
)


# These files must be served at the origin root: a root-scoped service worker
# may control both the normal site and the installed PWA. Revalidation headers
# ensure Render deployments are discovered rather than held by an HTTP cache.
@app.get("/manifest.webmanifest", include_in_schema=False)
async def manifest() -> FileResponse:
    return FileResponse(FRONTEND_DIR / "pwa" / "manifest.webmanifest", media_type="application/manifest+json", headers={"Cache-Control": "no-cache"})


@app.get("/sw.js", include_in_schema=False)
async def service_worker() -> FileResponse:
    return FileResponse(FRONTEND_DIR / "pwa" / "sw.js", media_type="application/javascript", headers={"Cache-Control": "no-cache", "Service-Worker-Allowed": "/"})

# ==========================================================
# Frontend Routes
# ==========================================================

from fastapi.responses import FileResponse

@app.get("/", include_in_schema=False)
async def root():
    return FileResponse(
        FRONTEND_DIR / "dashboard_v2" / "pages" / "login.html"
    )


@app.get("/login", include_in_schema=False)
async def login_page():
    return FileResponse(
        FRONTEND_DIR / "dashboard_v2" / "pages" / "login.html"
    )


@app.get("/reset-password", include_in_schema=False)
async def reset_password_page():
    return FileResponse(
        FRONTEND_DIR / "dashboard_v2" / "pages" / "reset_password.html"
    )


@app.get("/setup-password", include_in_schema=False)
async def setup_password_page():
    """Reuse the existing password page for first-time email setup."""
    return FileResponse(FRONTEND_DIR / "dashboard_v2" / "pages" / "reset_password.html")

@app.get("/dashboard", include_in_schema=False)
async def dashboard():
    return FileResponse(
        FRONTEND_DIR / "dashboard_v2" / "pages" / "dashboard.html"
    )


@app.get("/donor-dashboard", include_in_schema=False)
async def donor_dashboard():
    return FileResponse(FRONTEND_DIR / "dashboard_v2" / "pages" / "donor_dashboard.html")


@app.get("/donor-register", include_in_schema=False)
async def donor_registration_page():
    return FileResponse(FRONTEND_DIR / "dashboard_v2" / "pages" / "donor_registration.html")
