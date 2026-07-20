"""FastAPI application initialization for BloodLink."""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from backend.database.database import (
    Base,
    engine,
    verify_database_connection,
)
from backend.routers.auth import router as auth_router
from backend.routers.blood_requests import router as blood_requests_router
from backend.routers.donors import router as donors_router
logger = logging.getLogger(__name__)
from backend.routers.donor_matching import (
    router as donor_matching_router,
)
from backend.routers.email_router import router as email_router
from backend.routers.notifications import (
    router as notifications_router,
)
from backend.create_default_admin import create_admin
from backend.routers import dashboard_router
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

    # ------------------------------------------------------
    # Create all database tables
    # ------------------------------------------------------

    Base.metadata.create_all(bind=engine)

    # ------------------------------------------------------
    # Create the default administrator
    # (Only if it doesn't already exist)
    # ------------------------------------------------------

    create_admin()

    # ------------------------------------------------------
    # Verify database connection
    # ------------------------------------------------------

    verify_database_connection()

    logger.info("Database initialized successfully.")

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
)

# ==========================================================
# Routers
# ==========================================================

app.include_router(auth_router)

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

@app.get("/dashboard", include_in_schema=False)
async def dashboard():
    return FileResponse(
        FRONTEND_DIR / "dashboard_v2" / "pages" / "dashboard.html"
    )
