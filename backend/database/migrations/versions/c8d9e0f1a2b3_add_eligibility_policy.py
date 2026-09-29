"""Add clinician-reviewed operational eligibility policy.

Revision ID: c8d9e0f1a2b3
Revises: b7c8d9e0f1a2
Create Date: 2026-09-27
"""

from alembic import op
import sqlalchemy as sa


revision = "c8d9e0f1a2b3"
down_revision = "b7c8d9e0f1a2"
branch_labels = None
depends_on = None


SOURCE_REFERENCE = (
    "https://clinicalestablishments.mohfw.gov.in/sites/default/files/2023-03/1491_0.pdf"
)


def upgrade() -> None:
    op.create_table(
        "eligibility_policies",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("enforcement_mode", sa.String(length=20), server_default="ADVISORY", nullable=False),
        sa.Column("minimum_age_years", sa.Integer(), server_default="18", nullable=False),
        sa.Column("maximum_age_years", sa.Integer(), server_default="65", nullable=False),
        sa.Column("minimum_weight_kg", sa.Numeric(precision=5, scale=2), server_default="45.00", nullable=False),
        sa.Column("require_complete_profile", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("reviewer_name", sa.String(length=200), nullable=True),
        sa.Column("review_notes", sa.Text(), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("source_reference", sa.Text(), nullable=False),
        sa.Column("version", sa.Integer(), server_default="1", nullable=False),
        sa.Column("updated_by", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["updated_by"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    policies = sa.table(
        "eligibility_policies",
        sa.column("id", sa.Integer()),
        sa.column("enforcement_mode", sa.String()),
        sa.column("minimum_age_years", sa.Integer()),
        sa.column("maximum_age_years", sa.Integer()),
        sa.column("minimum_weight_kg", sa.Numeric(5, 2)),
        sa.column("require_complete_profile", sa.Boolean()),
        sa.column("source_reference", sa.Text()),
        sa.column("version", sa.Integer()),
    )
    op.bulk_insert(policies, [{
        "id": 1,
        "enforcement_mode": "ADVISORY",
        "minimum_age_years": 18,
        "maximum_age_years": 65,
        "minimum_weight_kg": 45,
        "require_complete_profile": False,
        "source_reference": SOURCE_REFERENCE,
        "version": 1,
    }])


def downgrade() -> None:
    op.drop_table("eligibility_policies")
