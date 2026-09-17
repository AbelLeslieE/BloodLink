"""Shared authentication and public-registration request throttling."""
from alembic import op
import sqlalchemy as sa

revision = "02a_security_rate_limits"
down_revision = "c0d1e2f3a4b5"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table("security_rate_limits",
        sa.Column("key", sa.String(64), primary_key=True),
        sa.Column("count", sa.Integer(), nullable=False),
        sa.Column("expires_at", sa.Integer(), nullable=False))
    op.create_index("ix_security_rate_limits_expires_at", "security_rate_limits", ["expires_at"])


def downgrade():
    op.drop_table("security_rate_limits")
