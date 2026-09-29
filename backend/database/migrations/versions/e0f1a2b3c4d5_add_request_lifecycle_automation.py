"""Add request expiry, escalation, and closure metadata.

Revision ID: e0f1a2b3c4d5
Revises: d9e0f1a2b3c4
Create Date: 2026-09-29
"""

from datetime import datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

from alembic import op
import sqlalchemy as sa


revision = "e0f1a2b3c4d5"
down_revision = "d9e0f1a2b3c4"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("blood_requests") as batch_op:
        batch_op.add_column(sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True))
        batch_op.add_column(sa.Column("escalation_level", sa.Integer(), server_default="0", nullable=False))
        batch_op.add_column(sa.Column("escalation_reason", sa.String(length=255), nullable=True))
        batch_op.add_column(sa.Column("escalated_at", sa.DateTime(timezone=True), nullable=True))
        batch_op.add_column(sa.Column("closure_reason", sa.String(length=500), nullable=True))
        batch_op.add_column(sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True))
        batch_op.create_index("ix_blood_requests_expires_at", ["expires_at"], unique=False)

    bind = op.get_bind()
    metadata = sa.MetaData()
    requests = sa.Table("blood_requests", metadata, autoload_with=bind)
    local_timezone = ZoneInfo("Asia/Kolkata")
    legacy_reasons = {
        "Fulfilled": "Fulfilled before closure-reason tracking was enabled.",
        "Cancelled": "Cancelled before closure-reason tracking was enabled.",
        "Closed": "Closed before closure-reason tracking was enabled.",
    }
    for row in bind.execute(
        sa.select(requests.c.id, requests.c.required_date, requests.c.status)
    ).mappings():
        deadline = datetime.combine(
            row["required_date"] + timedelta(days=1),
            time.min,
            tzinfo=local_timezone,
        ).astimezone(timezone.utc)
        values = {"expires_at": deadline}
        if row["status"] in legacy_reasons:
            values["closure_reason"] = legacy_reasons[row["status"]]
        bind.execute(
            requests.update().where(requests.c.id == row["id"]).values(**values)
        )


def downgrade() -> None:
    with op.batch_alter_table("blood_requests") as batch_op:
        batch_op.drop_index("ix_blood_requests_expires_at")
        batch_op.drop_column("closed_at")
        batch_op.drop_column("closure_reason")
        batch_op.drop_column("escalated_at")
        batch_op.drop_column("escalation_reason")
        batch_op.drop_column("escalation_level")
        batch_op.drop_column("expires_at")
