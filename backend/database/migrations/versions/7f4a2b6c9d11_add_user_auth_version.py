"""Add JWT session-version revocation support."""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "7f4a2b6c9d11"
down_revision = "3b8e9a1c4d20"
branch_labels = None
depends_on = None


def upgrade() -> None:
    columns = {column["name"] for column in sa.inspect(op.get_bind()).get_columns("users")}
    if "auth_version" not in columns:
        with op.batch_alter_table("users") as batch:
            batch.add_column(sa.Column("auth_version", sa.Integer(), nullable=False, server_default="0"))


def downgrade() -> None:
    with op.batch_alter_table("users") as batch:
        batch.drop_column("auth_version")
