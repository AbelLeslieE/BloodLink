"""Persist administrator donor selections for blood requests."""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "a4d8e7f2b9c1"
down_revision = "f1c2d3e4a5b6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    if "saved_matches" not in sa.inspect(op.get_bind()).get_table_names():
        op.create_table(
            "saved_matches",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("blood_request_id", sa.Integer(), sa.ForeignKey("blood_requests.id"), nullable=False, index=True),
            sa.Column("donor_id", sa.Integer(), sa.ForeignKey("donors.id"), nullable=False, index=True),
            sa.Column("saved_by", sa.Integer(), sa.ForeignKey("users.id"), nullable=False, index=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.UniqueConstraint("blood_request_id", "donor_id", name="uq_saved_matches_request_donor"),
        )


def downgrade() -> None:
    op.drop_table("saved_matches")
