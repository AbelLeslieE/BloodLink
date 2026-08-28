"""Add donation certificate records."""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "f1c2d3e4a5b6"
down_revision = "7f4a2b6c9d11"
branch_labels = None
depends_on = None


def upgrade() -> None:
    if "donation_certificates" not in sa.inspect(op.get_bind()).get_table_names():
        op.create_table(
            "donation_certificates",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("donation_history_id", sa.Integer(), sa.ForeignKey("donation_history.id"), nullable=False, unique=True, index=True),
            sa.Column("certificate_number", sa.String(64), nullable=False, unique=True, index=True),
            sa.Column("issued_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        )


def downgrade() -> None:
    op.drop_table("donation_certificates")
