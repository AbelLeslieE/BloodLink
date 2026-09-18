"""Administrator-only view of the deployment's effective security posture."""

from __future__ import annotations

import os
from typing import Annotated

from fastapi import APIRouter, Depends, Request

from backend.auth.dependencies import require_administrator
from backend.config.settings import forwarded_allow_ips, get_settings
from backend.database.models import User
from backend.security.rate_limit import client_address


router = APIRouter(prefix="/api/admin/diagnostics", tags=["diagnostics"])


@router.get("/request")
def request_diagnostics(
    request: Request,
    _: Annotated[User, Depends(require_administrator)],
) -> dict:
    """Show how this request was resolved so proxy trust can be verified live.

    Call it with and without a spoofed X-Forwarded-For header: the resolved
    client address must be the caller's real public address both times.
    """
    settings = get_settings()
    forwarded = request.headers.get("x-forwarded-for", "")
    return {
        "resolved_client_ip": client_address(request),
        "forwarded_chain_length": len([hop for hop in forwarded.split(",") if hop.strip()]),
        "secure_scheme": request.url.scheme == "https",
        "production": settings.production,
        "docs_disabled": settings.production,
        "forwarded_allow_ips": forwarded_allow_ips(settings),
        "database_tls_mode": os.getenv("DATABASE_TLS_MODE", "").strip() or "automatic",
        "bootstrap_password_configured": bool(os.getenv("DEFAULT_VOLUNTEER_PASSWORD")),
    }
