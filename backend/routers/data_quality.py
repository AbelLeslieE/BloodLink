"""Administrator-only donor data-quality dashboard APIs."""

from __future__ import annotations

import csv
import io
from datetime import datetime, timezone
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from backend.auth.dependencies import require_administrator
from backend.database.database import get_db
from backend.database.models import User
from backend.services.audit_service import record_audit_event
from backend.services.data_quality_service import DonorQualityResult, analyze_donors, quality_summary


router = APIRouter(
    prefix="/api/admin/technical/data-quality",
    tags=["data quality"],
)


def _item_payload(item: DonorQualityResult) -> dict:
    donor = item.donor
    return {
        "donor_id": donor.id,
        "donor_code": donor.donor_code,
        "full_name": donor.full_name,
        "blood_group": donor.blood_group,
        "email": donor.email,
        "phone": donor.phone,
        "status": donor.status,
        "updated_at": donor.updated_at,
        "completeness_percent": item.completeness_percent,
        "highest_severity": item.highest_severity,
        "issues": [
            {
                "code": issue.code,
                "category": issue.category,
                "severity": issue.severity,
                "message": issue.message,
            }
            for issue in item.issues
        ],
    }


def _filtered_results(
    database_session: Session,
    *,
    stale_after_days: int,
    category: str | None,
    severity: str | None,
    search: str | None,
) -> tuple[list[DonorQualityResult], list[DonorQualityResult]]:
    all_results = analyze_donors(
        database_session, stale_after_days=stale_after_days
    )
    filtered = all_results
    if category:
        filtered = [
            item for item in filtered
            if any(issue.category == category for issue in item.issues)
        ]
    if severity:
        filtered = [
            item for item in filtered
            if any(issue.severity == severity for issue in item.issues)
        ]
    if search:
        query = search.strip().lower()
        filtered = [
            item for item in filtered
            if query in " ".join(filter(None, (
                item.donor.full_name,
                item.donor.donor_code,
                item.donor.email,
                item.donor.phone,
                item.donor.blood_group,
            ))).lower()
        ]
    return all_results, filtered


@router.get("")
def data_quality_queue(
    _: Annotated[User, Depends(require_administrator)],
    database_session: Annotated[Session, Depends(get_db)],
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=200),
    stale_after_days: int = Query(default=365, ge=30, le=3650),
    category: Literal["ELIGIBILITY", "CONTACT", "DUPLICATE", "LOCATION", "STALE"] | None = None,
    severity: Literal["HIGH", "REVIEW", "INFO"] | None = None,
    search: str | None = Query(default=None, max_length=120),
) -> dict:
    all_results, filtered = _filtered_results(
        database_session,
        stale_after_days=stale_after_days,
        category=category,
        severity=severity,
        search=search,
    )
    start = (page - 1) * page_size
    return {
        "items": [_item_payload(item) for item in filtered[start:start + page_size]],
        "total": len(filtered),
        "page": page,
        "page_size": page_size,
        "stale_after_days": stale_after_days,
        "summary": quality_summary(all_results),
    }


def _csv_safe(value: object) -> str:
    text = "" if value is None else str(value)
    if text.startswith(("=", "+", "-", "@")):
        return "'" + text
    return text


@router.get("/export")
def export_data_quality_queue(
    request: Request,
    administrator: Annotated[User, Depends(require_administrator)],
    database_session: Annotated[Session, Depends(get_db)],
    stale_after_days: int = Query(default=365, ge=30, le=3650),
    category: Literal["ELIGIBILITY", "CONTACT", "DUPLICATE", "LOCATION", "STALE"] | None = None,
    severity: Literal["HIGH", "REVIEW", "INFO"] | None = None,
    search: str | None = Query(default=None, max_length=120),
) -> StreamingResponse:
    _, results = _filtered_results(
        database_session,
        stale_after_days=stale_after_days,
        category=category,
        severity=severity,
        search=search,
    )
    output = io.StringIO(newline="")
    writer = csv.writer(output)
    writer.writerow([
        "donor_id", "donor_code", "full_name", "blood_group", "email", "phone",
        "status", "completeness_percent", "highest_severity", "issue_codes",
        "issue_details", "updated_at",
    ])
    for item in results:
        donor = item.donor
        writer.writerow([_csv_safe(value) for value in (
            donor.id,
            donor.donor_code,
            donor.full_name,
            donor.blood_group,
            donor.email,
            donor.phone,
            donor.status,
            item.completeness_percent,
            item.highest_severity,
            "; ".join(issue.code for issue in item.issues),
            "; ".join(issue.message for issue in item.issues),
            donor.updated_at.isoformat() if donor.updated_at else "",
        )])
    record_audit_event(
        database_session,
        category="DATA_QUALITY",
        action="DATA_QUALITY_EXPORTED",
        actor=administrator,
        target_type="donor_data_quality",
        request=request,
        details={
            "rows": len(results),
            "category": category,
            "severity": severity,
            "stale_after_days": stale_after_days,
        },
    )
    database_session.commit()
    filename = f"bloodlink-data-quality-{datetime.now(timezone.utc):%Y%m%d-%H%M%S}.csv"
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
