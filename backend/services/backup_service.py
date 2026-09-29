"""Encrypted, checksummed logical backups that work with SQLite and PostgreSQL."""

from __future__ import annotations

import base64
import gzip
import hashlib
import json
import os
from datetime import date, datetime, timezone
from decimal import Decimal
from pathlib import Path
from uuid import uuid4

from cryptography.fernet import Fernet, InvalidToken
from sqlalchemy import MetaData, select
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from backend.config.settings import BASE_DIR, get_settings
from backend.database.models import BackupRecord, User


class BackupError(RuntimeError):
    pass


def backup_directory() -> Path:
    configured = os.getenv("BACKUP_DIRECTORY", "").strip()
    if get_settings().production and not configured:
        raise BackupError("BACKUP_DIRECTORY must point to persistent storage before production backups can be created.")
    path = Path(configured) if configured else BASE_DIR / "local_artifacts" / "backups"
    path = path.expanduser().resolve()
    path.mkdir(parents=True, exist_ok=True)
    return path


def _fernet() -> Fernet:
    configured = os.getenv("BACKUP_ENCRYPTION_KEY", "").strip()
    if configured:
        try:
            decoded = base64.urlsafe_b64decode(configured.encode())
        except Exception as error:
            raise BackupError("BACKUP_ENCRYPTION_KEY must be a URL-safe base64 key.") from error
        if len(decoded) != 32:
            raise BackupError("BACKUP_ENCRYPTION_KEY must decode to exactly 32 bytes.")
        return Fernet(configured.encode())
    if get_settings().production:
        raise BackupError("BACKUP_ENCRYPTION_KEY is required before production backups can be created.")
    digest = hashlib.sha256((get_settings().secret_key + ":backup:v1").encode()).digest()
    return Fernet(base64.urlsafe_b64encode(digest))


def _json_value(value):
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, (datetime, date)):
        return {"$type": "datetime" if isinstance(value, datetime) else "date", "value": value.isoformat()}
    if isinstance(value, Decimal):
        return {"$type": "decimal", "value": str(value)}
    if isinstance(value, bytes):
        return {"$type": "bytes", "value": base64.b64encode(value).decode()}
    return {"$type": "string", "value": str(value)}


def _snapshot(engine: Engine) -> tuple[dict, int, int]:
    metadata = MetaData()
    metadata.reflect(bind=engine)
    tables = []
    total_rows = 0
    with engine.connect() as connection:
        with connection.begin():
            for table in sorted(metadata.tables.values(), key=lambda item: item.name):
                rows = [
                    {column: _json_value(value) for column, value in row._mapping.items()}
                    for row in connection.execute(select(table)).all()
                ]
                total_rows += len(rows)
                tables.append({
                    "name": table.name,
                    "columns": [column.name for column in table.columns],
                    "rows": rows,
                })
    payload = {
        "format": "bloodlink-logical-backup",
        "version": 1,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "database_dialect": engine.dialect.name,
        "tables": tables,
    }
    return payload, len(tables), total_rows


def create_backup(database_session: Session, engine: Engine, administrator: User) -> BackupRecord:
    backup_id = str(uuid4())
    filename = f"bloodlink-{datetime.now(timezone.utc):%Y%m%d-%H%M%S}-{backup_id[:8]}.blbackup"
    record = BackupRecord(
        id=backup_id,
        created_by=administrator.id,
        created_by_username=administrator.username,
        status="CREATING",
        filename=filename,
    )
    database_session.add(record)
    database_session.commit()
    database_session.refresh(record)
    try:
        payload, table_count, row_count = _snapshot(engine)
        raw = json.dumps(payload, separators=(",", ":"), ensure_ascii=True).encode()
        encrypted = _fernet().encrypt(gzip.compress(raw, compresslevel=9))
        target = backup_directory() / filename
        temporary = target.with_suffix(target.suffix + ".tmp")
        temporary.write_bytes(encrypted)
        temporary.replace(target)
        record.status = "READY"
        record.completed_at = datetime.now(timezone.utc)
        record.storage_path = str(target)
        record.size_bytes = len(encrypted)
        record.checksum_sha256 = hashlib.sha256(encrypted).hexdigest()
        record.table_count = table_count
        record.row_count = row_count
        database_session.commit()
        database_session.refresh(record)
        return record
    except Exception as error:
        database_session.rollback()
        record = database_session.get(BackupRecord, backup_id)
        if record:
            record.status = "FAILED"
            record.error_message = str(error)[:500]
            record.completed_at = datetime.now(timezone.utc)
            database_session.commit()
        if isinstance(error, BackupError):
            raise
        raise BackupError("The encrypted backup could not be created.") from error


def resolved_backup_file(record: BackupRecord) -> Path:
    if record.status != "READY" or not record.storage_path or record.deleted_at:
        raise BackupError("This backup file is not available.")
    base = backup_directory()
    path = Path(record.storage_path).resolve()
    if path.parent != base or path.name != record.filename:
        raise BackupError("The backup path failed validation.")
    if not path.is_file():
        raise BackupError("The backup file is missing from storage.")
    return path


def verify_backup(record: BackupRecord) -> dict:
    path = resolved_backup_file(record)
    encrypted = path.read_bytes()
    checksum = hashlib.sha256(encrypted).hexdigest()
    if not record.checksum_sha256 or checksum != record.checksum_sha256:
        raise BackupError("The backup checksum does not match its recorded value.")
    try:
        payload = json.loads(gzip.decompress(_fernet().decrypt(encrypted)))
    except (InvalidToken, OSError, ValueError, json.JSONDecodeError) as error:
        raise BackupError("The backup cannot be decrypted or its contents are invalid.") from error
    if payload.get("format") != "bloodlink-logical-backup" or payload.get("version") != 1:
        raise BackupError("The backup format is not supported.")
    return {
        "valid": True,
        "checksum_sha256": checksum,
        "created_at": payload.get("created_at"),
        "table_count": len(payload.get("tables", [])),
        "row_count": sum(len(table.get("rows", [])) for table in payload.get("tables", [])),
    }


def delete_backup_file(database_session: Session, record: BackupRecord) -> None:
    path = resolved_backup_file(record)
    path.unlink()
    record.status = "DELETED"
    record.deleted_at = datetime.now(timezone.utc)
    record.storage_path = None
    database_session.commit()
