"""Atomic, database-backed request limits shared by application workers."""
import hashlib
import hmac
import time
from sqlalchemy import Integer, String, case, delete, or_
from sqlalchemy.orm import Mapped, mapped_column
from starlette.requests import Request
from backend.config.settings import get_settings
from backend.database.database import Base, SessionLocal


class RateLimitBucket(Base):
    __tablename__ = "security_rate_limits"
    key: Mapped[str] = mapped_column(String(64), primary_key=True)
    count: Mapped[int] = mapped_column(Integer, nullable=False)
    expires_at: Mapped[int] = mapped_column(Integer, nullable=False, index=True)


def _bucket_key(identity: str, bucket: str) -> str:
    return hmac.new(get_settings().secret_key.encode(), f"{bucket}:{identity}".encode(), hashlib.sha256).hexdigest()


def client_address(request: Request) -> str:
    """The peer address Uvicorn resolved after applying trusted proxy headers."""
    return request.client.host if request.client else "unknown"


def consume_limit(identity: str, bucket: str, limit: int, window: int) -> bool:
    now = int(time.time())
    key = _bucket_key(identity, bucket)
    with SessionLocal.begin() as db:
        if db.bind.dialect.name == "sqlite":
            from sqlalchemy.dialects.sqlite import insert
        elif db.bind.dialect.name == "postgresql":
            from sqlalchemy.dialects.postgresql import insert
        else:
            raise RuntimeError("Unsupported rate-limit database.")
        table = RateLimitBucket.__table__
        expired = table.c.expires_at <= now
        statement = insert(table).values(key=key, count=1, expires_at=now + window)
        statement = statement.on_conflict_do_update(
            index_elements=[table.c.key],
            set_={"count": case((expired, 1), else_=table.c.count + 1),
                  "expires_at": case((expired, now + window), else_=table.c.expires_at)},
            where=or_(expired, table.c.count < limit),
        ).returning(table.c.count)
        allowed = db.execute(statement).scalar_one_or_none() is not None
        # Bounded retention; no usernames/IP addresses are stored in cleartext.
        db.execute(delete(table).where(table.c.expires_at < now - 3600))
        return allowed


def clear_limit(identity: str, bucket: str) -> None:
    table = RateLimitBucket.__table__
    with SessionLocal.begin() as db:
        db.execute(delete(table).where(table.c.key == _bucket_key(identity, bucket)))
