"""Add time-bound donor deferrals and backfill recovery dates.

Revision ID: b7c8d9e0f1a2
Revises: a6b7c8d9e0f1
Create Date: 2026-09-27
"""

from datetime import date, timedelta

from alembic import op
import sqlalchemy as sa


revision = "b7c8d9e0f1a2"
down_revision = "a6b7c8d9e0f1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("donors", sa.Column("deferred_until", sa.Date(), nullable=True))
    op.add_column("donors", sa.Column("deferral_reason", sa.String(length=500), nullable=True))
    op.create_index(op.f("ix_donors_deferred_until"), "donors", ["deferred_until"], unique=False)

    # Before this migration, donation confirmation changed a donor to
    # Unavailable indefinitely. Recover those rows using the national default
    # whole-blood intervals. Manually unavailable donors without donation dates
    # remain untouched.
    bind = op.get_bind()
    metadata = sa.MetaData()
    donors = sa.Table("donors", metadata, autoload_with=bind)
    today = date.today()
    rows = bind.execute(
        sa.select(
            donors.c.id,
            donors.c.gender,
            donors.c.last_donation_date,
        ).where(
            donors.c.status == "Unavailable",
            donors.c.last_donation_date.is_not(None),
        )
    ).mappings()
    for row in rows:
        days = 90 if (row["gender"] or "").strip().lower() == "male" else 120
        eligible_on = row["last_donation_date"] + timedelta(days=days)
        values = {
            "status": "Deferred" if eligible_on > today else "Available",
            "deferred_until": eligible_on,
            "deferral_reason": f"Post-donation recovery period ({days} days)",
        }
        bind.execute(donors.update().where(donors.c.id == row["id"]).values(**values))


def downgrade() -> None:
    op.drop_index(op.f("ix_donors_deferred_until"), table_name="donors")
    op.drop_column("donors", "deferral_reason")
    op.drop_column("donors", "deferred_until")
