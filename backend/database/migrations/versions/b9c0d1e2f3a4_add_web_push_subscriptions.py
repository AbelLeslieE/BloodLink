"""Add authenticated browser push subscriptions.

Revision ID: b9c0d1e2f3a4
Revises: e8f9a0b1c2d3
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "b9c0d1e2f3a4"
down_revision = "e8f9a0b1c2d3"
branch_labels = None
depends_on = None


def upgrade() -> None:
    if "push_subscriptions" in sa.inspect(op.get_bind()).get_table_names():
        return
    op.create_table(
        "push_subscriptions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("endpoint", sa.Text(), nullable=False, unique=True),
        sa.Column("p256dh", sa.String(length=255), nullable=False),
        sa.Column("auth", sa.String(length=255), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("minimum_priority", sa.String(length=20), nullable=False, server_default="Normal"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("push_subscriptions")
