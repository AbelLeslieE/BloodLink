"""MFA, session control, audit log, and encrypted-backup APIs."""

from __future__ import annotations

import csv
import io
import json
import os
from datetime import datetime, timedelta, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from backend.auth.dependencies import require_administrator, require_authentication
from backend.auth.security import verify_password
from backend.database.database import get_db
from backend.database.models import AuditLog, BackupRecord, User, UserSession
from backend.services.audit_service import record_audit_event, verify_audit_event
from backend.services.backup_service import (
    BackupError,
    create_backup,
    delete_backup_file,
    resolved_backup_file,
    verify_backup,
)
from backend.services.mfa_service import (
    decrypt_secret,
    encrypt_secret,
    generate_recovery_codes,
    generate_secret,
    provisioning_uri,
    qr_data_uri,
    recovery_codes_remaining,
    verify_totp,
    verify_user_code,
)
from backend.services.session_service import (
    as_utc,
    describe_user_agent,
    revoke_all_sessions,
    revoke_session,
    utcnow,
)
from backend.services import donor_eligibility_service


security_router = APIRouter(prefix="/api/security", tags=["account security"])
admin_router = APIRouter(prefix="/api/admin/technical", tags=["technical portal"])


class PasswordProof(BaseModel):
    current_password: str = Field(min_length=1, max_length=1024)


class MFACode(BaseModel):
    code: str = Field(min_length=6, max_length=64)


class MFADisable(PasswordProof):
    code: str = Field(min_length=6, max_length=64)


class MFARecoveryRegenerate(MFADisable):
    pass


class MFAAdministrativeReset(PasswordProof):
    reason: str = Field(min_length=5, max_length=300)


def _session_payload(session: UserSession, current_session_id: str | None = None) -> dict:
    return {
        "id": session.id,
        "user_id": session.user_id,
        "username": session.user.username if session.user else None,
        "display_name": session.user.full_name if session.user else None,
        "created_at": session.created_at,
        "last_seen_at": session.last_seen_at,
        "expires_at": session.expires_at,
        "revoked_at": session.revoked_at,
        "active": session.revoked_at is None and as_utc(session.expires_at) > utcnow(),
        "current": session.id == current_session_id,
        "ip_address": session.ip_address,
        "device": describe_user_agent(session.user_agent),
        "user_agent": session.user_agent,
        "mfa_verified": session.mfa_verified,
    }


def _backup_payload(record: BackupRecord) -> dict:
    return {
        "id": record.id,
        "created_by": record.created_by_username,
        "created_at": record.created_at,
        "completed_at": record.completed_at,
        "deleted_at": record.deleted_at,
        "status": record.status,
        "filename": record.filename,
        "size_bytes": record.size_bytes,
        "checksum_sha256": record.checksum_sha256,
        "table_count": record.table_count,
        "row_count": record.row_count,
        "error_message": record.error_message,
    }


def _audit_payload(event: AuditLog) -> dict:
    try:
        details = json.loads(event.details_json)
    except (TypeError, json.JSONDecodeError):
        details = {}
    return {
        "id": event.id,
        "created_at": event.created_at,
        "actor_user_id": event.actor_user_id,
        "actor_username": event.actor_username or "System",
        "category": event.category,
        "action": event.action,
        "result": event.result,
        "target_type": event.target_type,
        "target_id": event.target_id,
        "ip_address": event.ip_address,
        "user_agent": event.user_agent,
        "request_method": event.request_method,
        "request_path": event.request_path,
        "details": details,
        "integrity_valid": verify_audit_event(event),
    }


@security_router.get("/mfa/status")
def mfa_status(current_user: Annotated[User, Depends(require_authentication)]) -> dict:
    return {
        "enabled": current_user.mfa_enabled,
        "setup_pending": bool(current_user.mfa_secret_encrypted and not current_user.mfa_enabled),
        "recovery_codes_remaining": recovery_codes_remaining(current_user),
    }


@security_router.post("/mfa/setup")
def mfa_setup(
    data: PasswordProof,
    request: Request,
    current_user: Annotated[User, Depends(require_authentication)],
    database_session: Annotated[Session, Depends(get_db)],
) -> dict:
    if current_user.mfa_enabled:
        raise HTTPException(status_code=409, detail="MFA is already enabled for this account.")
    if not verify_password(data.current_password, current_user.password_hash):
        raise HTTPException(status_code=400, detail="The current password is incorrect.")
    secret = generate_secret()
    uri = provisioning_uri(current_user.username, secret)
    current_user.mfa_secret_encrypted = encrypt_secret(secret)
    current_user.mfa_recovery_codes = None
    current_user.mfa_last_counter = None
    record_audit_event(
        database_session,
        category="MFA",
        action="MFA_SETUP_STARTED",
        actor=current_user,
        target_type="user",
        target_id=current_user.id,
        request=request,
    )
    database_session.commit()
    return {"secret": secret, "provisioning_uri": uri, "qr_data_uri": qr_data_uri(uri)}


@security_router.post("/mfa/confirm")
def mfa_confirm(
    data: MFACode,
    request: Request,
    current_user: Annotated[User, Depends(require_authentication)],
    database_session: Annotated[Session, Depends(get_db)],
) -> dict:
    if current_user.mfa_enabled:
        raise HTTPException(status_code=409, detail="MFA is already enabled.")
    if not current_user.mfa_secret_encrypted:
        raise HTTPException(status_code=409, detail="Start MFA setup before confirming a code.")
    counter = verify_totp(decrypt_secret(current_user.mfa_secret_encrypted), data.code)
    if counter is None:
        raise HTTPException(status_code=400, detail="The verification code is invalid.")
    codes, hashes = generate_recovery_codes()
    current_user.mfa_enabled = True
    current_user.mfa_last_counter = counter
    current_user.mfa_recovery_codes = hashes
    revoked_count = revoke_all_sessions(
        database_session,
        current_user.id,
        except_session_id=getattr(request.state, "session_id", None),
    )
    record_audit_event(
        database_session,
        category="MFA",
        action="MFA_ENABLED",
        actor=current_user,
        target_type="user",
        target_id=current_user.id,
        request=request,
        details={"other_sessions_revoked": revoked_count},
    )
    database_session.commit()
    return {"enabled": True, "recovery_codes": codes}


@security_router.post("/mfa/disable")
def mfa_disable(
    data: MFADisable,
    request: Request,
    current_user: Annotated[User, Depends(require_authentication)],
    database_session: Annotated[Session, Depends(get_db)],
) -> dict:
    if not current_user.mfa_enabled:
        raise HTTPException(status_code=409, detail="MFA is not enabled.")
    if not verify_password(data.current_password, current_user.password_hash):
        raise HTTPException(status_code=400, detail="The current password is incorrect.")
    if not verify_user_code(current_user, data.code):
        raise HTTPException(status_code=400, detail="The verification code is invalid.")
    current_user.mfa_enabled = False
    current_user.mfa_secret_encrypted = None
    current_user.mfa_recovery_codes = None
    current_user.mfa_last_counter = None
    revoked_count = revoke_all_sessions(
        database_session, current_user.id, except_session_id=getattr(request.state, "session_id", None)
    )
    record_audit_event(
        database_session,
        category="MFA",
        action="MFA_DISABLED",
        actor=current_user,
        target_type="user",
        target_id=current_user.id,
        request=request,
        details={"other_sessions_revoked": revoked_count},
    )
    database_session.commit()
    return {"enabled": False}


@security_router.post("/mfa/recovery-codes")
def regenerate_recovery_codes(
    data: MFARecoveryRegenerate,
    request: Request,
    current_user: Annotated[User, Depends(require_authentication)],
    database_session: Annotated[Session, Depends(get_db)],
) -> dict:
    if not current_user.mfa_enabled:
        raise HTTPException(status_code=409, detail="Enable MFA before generating recovery codes.")
    if not verify_password(data.current_password, current_user.password_hash) or not verify_user_code(current_user, data.code, allow_recovery=False):
        raise HTTPException(status_code=400, detail="The password or authenticator code is invalid.")
    codes, hashes = generate_recovery_codes()
    current_user.mfa_recovery_codes = hashes
    record_audit_event(
        database_session,
        category="MFA",
        action="MFA_RECOVERY_CODES_REGENERATED",
        actor=current_user,
        target_type="user",
        target_id=current_user.id,
        request=request,
    )
    database_session.commit()
    return {"recovery_codes": codes}


@security_router.get("/sessions")
def my_sessions(
    request: Request,
    current_user: Annotated[User, Depends(require_authentication)],
    database_session: Annotated[Session, Depends(get_db)],
) -> list[dict]:
    sessions = database_session.scalars(
        select(UserSession)
        .where(UserSession.user_id == current_user.id)
        .order_by(UserSession.created_at.desc())
    ).all()
    return [_session_payload(item, getattr(request.state, "session_id", None)) for item in sessions]


@security_router.delete("/sessions/{session_id}")
def revoke_my_session(
    session_id: str,
    request: Request,
    response: Response,
    current_user: Annotated[User, Depends(require_authentication)],
    database_session: Annotated[Session, Depends(get_db)],
) -> dict:
    session = database_session.scalar(
        select(UserSession).where(UserSession.id == session_id, UserSession.user_id == current_user.id)
    )
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found.")
    revoke_session(database_session, session)
    record_audit_event(
        database_session,
        category="SESSION",
        action="SESSION_REVOKED",
        actor=current_user,
        target_type="session",
        target_id=session.id,
        request=request,
        details={"current_session": session.id == getattr(request.state, "session_id", None)},
    )
    database_session.commit()
    if session.id == getattr(request.state, "session_id", None):
        response.delete_cookie("bloodlink_session", path="/", samesite="strict")
    return {"revoked": True, "current_session": session.id == getattr(request.state, "session_id", None)}


@security_router.post("/sessions/revoke-others")
def revoke_other_sessions(
    request: Request,
    current_user: Annotated[User, Depends(require_authentication)],
    database_session: Annotated[Session, Depends(get_db)],
) -> dict:
    count = revoke_all_sessions(
        database_session, current_user.id, except_session_id=getattr(request.state, "session_id", None)
    )
    record_audit_event(
        database_session,
        category="SESSION",
        action="OTHER_SESSIONS_REVOKED",
        actor=current_user,
        target_type="user",
        target_id=current_user.id,
        request=request,
        details={"revoked_count": count},
    )
    database_session.commit()
    return {"revoked_count": count}


@admin_router.get("/summary")
def technical_summary(
    _: Annotated[User, Depends(require_administrator)],
    database_session: Annotated[Session, Depends(get_db)],
) -> dict:
    now = utcnow()
    eligibility_policy = donor_eligibility_service.current_policy(database_session)
    return {
        "audit_events_24h": database_session.scalar(
            select(func.count(AuditLog.id)).where(AuditLog.created_at >= now - timedelta(hours=24))
        ) or 0,
        "failed_events_24h": database_session.scalar(
            select(func.count(AuditLog.id)).where(
                AuditLog.created_at >= now - timedelta(hours=24), AuditLog.result == "FAILED"
            )
        ) or 0,
        "active_sessions": database_session.scalar(
            select(func.count(UserSession.id)).where(
                UserSession.revoked_at.is_(None), UserSession.expires_at > now
            )
        ) or 0,
        "mfa_enabled_users": database_session.scalar(
            select(func.count(User.id)).where(User.active.is_(True), User.mfa_enabled.is_(True))
        ) or 0,
        "active_users": database_session.scalar(
            select(func.count(User.id)).where(User.active.is_(True))
        ) or 0,
        "ready_backups": database_session.scalar(
            select(func.count(BackupRecord.id)).where(BackupRecord.status == "READY")
        ) or 0,
        "backup_key_configured": bool(os.getenv("BACKUP_ENCRYPTION_KEY", "").strip()) or not os.getenv("APP_ENV", "development").lower() == "production",
        "backup_storage_configured": bool(os.getenv("BACKUP_DIRECTORY", "").strip()) or not os.getenv("APP_ENV", "development").lower() == "production",
        "restore_available": False,
        "eligibility_policy_mode": eligibility_policy.enforcement_mode,
        "eligibility_policy_version": eligibility_policy.version,
    }


@admin_router.get("/audit-logs")
def audit_logs(
    _: Annotated[User, Depends(require_administrator)],
    database_session: Annotated[Session, Depends(get_db)],
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=200),
    category: str | None = Query(default=None, max_length=50),
    result: str | None = Query(default=None, max_length=30),
    search: str | None = Query(default=None, max_length=120),
) -> dict:
    filters = []
    if category:
        filters.append(AuditLog.category == category.strip().upper())
    if result:
        filters.append(AuditLog.result == result.strip().upper())
    if search:
        pattern = f"%{search.strip()}%"
        filters.append(or_(
            AuditLog.actor_username.ilike(pattern), AuditLog.action.ilike(pattern),
            AuditLog.target_id.ilike(pattern), AuditLog.request_path.ilike(pattern),
        ))
    total = database_session.scalar(select(func.count(AuditLog.id)).where(*filters)) or 0
    events = database_session.scalars(
        select(AuditLog).where(*filters).order_by(AuditLog.created_at.desc(), AuditLog.id.desc())
        .offset((page - 1) * page_size).limit(page_size)
    ).all()
    return {"items": [_audit_payload(event) for event in events], "total": total, "page": page, "page_size": page_size}


@admin_router.get("/audit-logs/export")
def export_audit_logs(
    request: Request,
    administrator: Annotated[User, Depends(require_administrator)],
    database_session: Annotated[Session, Depends(get_db)],
) -> StreamingResponse:
    events = database_session.scalars(select(AuditLog).order_by(AuditLog.created_at.desc())).all()
    output = io.StringIO(newline="")
    writer = csv.writer(output)
    writer.writerow(["id", "created_at", "actor", "category", "action", "result", "target_type", "target_id", "ip_address", "request_method", "request_path", "integrity_valid"])
    for event in events:
        writer.writerow([event.id, event.created_at.isoformat(), event.actor_username or "System", event.category, event.action, event.result, event.target_type, event.target_id, event.ip_address, event.request_method, event.request_path, verify_audit_event(event)])
    record_audit_event(
        database_session, category="AUDIT", action="AUDIT_LOG_EXPORTED", actor=administrator,
        target_type="audit_log", request=request, details={"rows": len(events)},
    )
    database_session.commit()
    filename = f"bloodlink-audit-{datetime.now(timezone.utc):%Y%m%d-%H%M%S}.csv"
    return StreamingResponse(iter([output.getvalue()]), media_type="text/csv", headers={"Content-Disposition": f'attachment; filename="{filename}"'})


@admin_router.get("/sessions")
def all_sessions(
    request: Request,
    _: Annotated[User, Depends(require_administrator)],
    database_session: Annotated[Session, Depends(get_db)],
    active_only: bool = Query(default=True),
) -> list[dict]:
    statement = select(UserSession).order_by(UserSession.last_seen_at.desc())
    if active_only:
        statement = statement.where(UserSession.revoked_at.is_(None), UserSession.expires_at > utcnow())
    sessions = database_session.scalars(statement).all()
    return [_session_payload(item, getattr(request.state, "session_id", None)) for item in sessions]


@admin_router.delete("/sessions/{session_id}")
def revoke_any_session(
    session_id: str,
    request: Request,
    response: Response,
    administrator: Annotated[User, Depends(require_administrator)],
    database_session: Annotated[Session, Depends(get_db)],
) -> dict:
    session = database_session.get(UserSession, session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found.")
    revoke_session(database_session, session)
    record_audit_event(
        database_session, category="SESSION", action="SESSION_ADMIN_REVOKED", actor=administrator,
        target_type="session", target_id=session.id, request=request,
        details={"session_user_id": session.user_id},
    )
    database_session.commit()
    current = session.id == getattr(request.state, "session_id", None)
    if current:
        response.delete_cookie("bloodlink_session", path="/", samesite="strict")
    return {"revoked": True, "current_session": current}


@admin_router.get("/mfa/users")
def mfa_users(
    _: Annotated[User, Depends(require_administrator)],
    database_session: Annotated[Session, Depends(get_db)],
) -> list[dict]:
    users = database_session.scalars(select(User).order_by(User.full_name)).all()
    return [{
        "id": user.id, "username": user.username, "full_name": user.full_name,
        "role": user.role, "active": user.active, "mfa_enabled": user.mfa_enabled,
        "recovery_codes_remaining": recovery_codes_remaining(user),
    } for user in users]


@admin_router.post("/mfa/users/{user_id}/reset")
def reset_user_mfa(
    user_id: int,
    data: MFAAdministrativeReset,
    request: Request,
    administrator: Annotated[User, Depends(require_administrator)],
    database_session: Annotated[Session, Depends(get_db)],
) -> dict:
    if user_id == administrator.id:
        raise HTTPException(status_code=400, detail="Use your own MFA security controls to disable MFA.")
    if not verify_password(data.current_password, administrator.password_hash):
        raise HTTPException(status_code=400, detail="The administrator password is incorrect.")
    user = database_session.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found.")
    user.mfa_enabled = False
    user.mfa_secret_encrypted = None
    user.mfa_recovery_codes = None
    user.mfa_last_counter = None
    revoked_count = revoke_all_sessions(database_session, user.id)
    record_audit_event(
        database_session, category="MFA", action="MFA_ADMIN_RESET", actor=administrator,
        target_type="user", target_id=user.id, request=request,
        details={"reason": data.reason, "sessions_revoked": revoked_count, "target_username": user.username},
    )
    database_session.commit()
    return {"reset": True, "sessions_revoked": revoked_count}


@admin_router.get("/backups")
def backups(
    _: Annotated[User, Depends(require_administrator)],
    database_session: Annotated[Session, Depends(get_db)],
) -> list[dict]:
    records = database_session.scalars(select(BackupRecord).order_by(BackupRecord.created_at.desc())).all()
    return [_backup_payload(record) for record in records]


@admin_router.post("/backups", status_code=201)
def create_encrypted_backup(
    request: Request,
    administrator: Annotated[User, Depends(require_administrator)],
    database_session: Annotated[Session, Depends(get_db)],
) -> dict:
    try:
        record = create_backup(database_session, database_session.get_bind(), administrator)
    except BackupError as error:
        record_audit_event(
            database_session, category="BACKUP", action="BACKUP_CREATE", result="FAILED",
            actor=administrator, request=request, details={"reason": str(error)},
        )
        database_session.commit()
        raise HTTPException(status_code=503, detail=str(error)) from error
    record_audit_event(
        database_session, category="BACKUP", action="BACKUP_CREATED", actor=administrator,
        target_type="backup", target_id=record.id, request=request,
        details={"size_bytes": record.size_bytes, "rows": record.row_count, "tables": record.table_count},
    )
    database_session.commit()
    return _backup_payload(record)


@admin_router.get("/backups/{backup_id}/download")
def download_backup(
    backup_id: str,
    request: Request,
    administrator: Annotated[User, Depends(require_administrator)],
    database_session: Annotated[Session, Depends(get_db)],
) -> FileResponse:
    record = database_session.get(BackupRecord, backup_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Backup not found.")
    try:
        path = resolved_backup_file(record)
    except BackupError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
    record_audit_event(
        database_session, category="BACKUP", action="BACKUP_DOWNLOADED", actor=administrator,
        target_type="backup", target_id=record.id, request=request,
    )
    database_session.commit()
    return FileResponse(path, media_type="application/octet-stream", filename=record.filename, headers={"Cache-Control": "no-store"})


@admin_router.post("/backups/{backup_id}/verify")
def verify_encrypted_backup(
    backup_id: str,
    request: Request,
    administrator: Annotated[User, Depends(require_administrator)],
    database_session: Annotated[Session, Depends(get_db)],
) -> dict:
    record = database_session.get(BackupRecord, backup_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Backup not found.")
    try:
        result = verify_backup(record)
    except BackupError as error:
        record_audit_event(
            database_session, category="BACKUP", action="BACKUP_VERIFIED", result="FAILED",
            actor=administrator, target_type="backup", target_id=record.id,
            request=request, details={"reason": str(error)},
        )
        database_session.commit()
        raise HTTPException(status_code=409, detail=str(error)) from error
    record_audit_event(
        database_session, category="BACKUP", action="BACKUP_VERIFIED", actor=administrator,
        target_type="backup", target_id=record.id, request=request,
    )
    database_session.commit()
    return result


@admin_router.delete("/backups/{backup_id}")
def delete_encrypted_backup(
    backup_id: str,
    request: Request,
    administrator: Annotated[User, Depends(require_administrator)],
    database_session: Annotated[Session, Depends(get_db)],
) -> dict:
    record = database_session.get(BackupRecord, backup_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Backup not found.")
    try:
        delete_backup_file(database_session, record)
    except BackupError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
    record_audit_event(
        database_session, category="BACKUP", action="BACKUP_DELETED", actor=administrator,
        target_type="backup", target_id=record.id, request=request,
    )
    database_session.commit()
    return {"deleted": True}
