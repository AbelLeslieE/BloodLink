"""Add structured hospital locations for distance-based matching.

Revision ID: d9e0f1a2b3c4
Revises: c8d9e0f1a2b3
Create Date: 2026-09-29
"""

from alembic import op
import sqlalchemy as sa


revision = "d9e0f1a2b3c4"
down_revision = "c8d9e0f1a2b3"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("blood_requests") as batch_op:
        batch_op.add_column(sa.Column("hospital_district", sa.String(length=100), nullable=True))
        batch_op.add_column(sa.Column("hospital_city", sa.String(length=100), nullable=True))
        batch_op.add_column(sa.Column("hospital_latitude", sa.Numeric(precision=9, scale=6), nullable=True))
        batch_op.add_column(sa.Column("hospital_longitude", sa.Numeric(precision=9, scale=6), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("blood_requests") as batch_op:
        batch_op.drop_column("hospital_longitude")
        batch_op.drop_column("hospital_latitude")
        batch_op.drop_column("hospital_city")
        batch_op.drop_column("hospital_district")
