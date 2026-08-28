"""Add the donation-history fields used by the reporting endpoints.

Revision ID: c5e6f7a8b9d0
Revises: a4d8e7f2b9c1
Create Date: 2026-08-28
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "c5e6f7a8b9d0"
down_revision = "a4d8e7f2b9c1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add missing fields while preserving existing donation records."""
    inspector = sa.inspect(op.get_bind())
    columns = {column["name"] for column in inspector.get_columns("donation_history")}

    with op.batch_alter_table("donation_history") as batch:
        if "units" not in columns:
            batch.add_column(
                sa.Column("units", sa.Integer(), nullable=False, server_default="1")
            )
        if "donation_type" not in columns:
            batch.add_column(
                sa.Column(
                    "donation_type",
                    sa.String(length=30),
                    nullable=False,
                    server_default="Voluntary",
                )
            )


def downgrade() -> None:
    """Remove the fields introduced by this revision."""
    inspector = sa.inspect(op.get_bind())
    columns = {column["name"] for column in inspector.get_columns("donation_history")}

    with op.batch_alter_table("donation_history") as batch:
        if "donation_type" in columns:
            batch.drop_column("donation_type")
        if "units" in columns:
            batch.drop_column("units")
