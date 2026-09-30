"""Add donor-controlled outreach preferences.

Revision ID: 1b2c3d4e5f6a
Revises: 0a1b2c3d4e5f
Create Date: 2026-09-30
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "1b2c3d4e5f6a"
down_revision = "0a1b2c3d4e5f"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("donors") as batch_op:
        batch_op.add_column(sa.Column("availability_paused_until", sa.DateTime(timezone=True), nullable=True))
        batch_op.add_column(sa.Column("travel_radius_km", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("contact_window_start", sa.Time(), nullable=True))
        batch_op.add_column(sa.Column("contact_window_end", sa.Time(), nullable=True))
        batch_op.add_column(sa.Column("preferences_updated_at", sa.DateTime(timezone=True), nullable=True))
        batch_op.create_index(
            "ix_donors_availability_paused_until",
            ["availability_paused_until"],
            unique=False,
        )


def downgrade() -> None:
    with op.batch_alter_table("donors") as batch_op:
        batch_op.drop_index("ix_donors_availability_paused_until")
        batch_op.drop_column("preferences_updated_at")
        batch_op.drop_column("contact_window_end")
        batch_op.drop_column("contact_window_start")
        batch_op.drop_column("travel_radius_km")
        batch_op.drop_column("availability_paused_until")
