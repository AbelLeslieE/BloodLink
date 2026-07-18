"""Update donor management fields.

Revision ID: 2d00ee800210
Revises: 631622072e68
Create Date: 2026-07-18 21:26:30.581089
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


# ==========================================================
# ALEMBIC REVISION IDENTIFIERS
# ==========================================================

revision = "2d00ee800210"
down_revision = "631622072e68"
branch_labels = None
depends_on = None


# ==========================================================
# UPGRADE
# ==========================================================

def upgrade() -> None:
    """
    Upgrade the donors table for the Donor Management module.

    Batch mode is used because BloodLink currently uses SQLite,
    which does not directly support several ALTER COLUMN operations.
    """

    with op.batch_alter_table("donors") as batch_op:

        # --------------------------------------------------
        # New donor fields
        # --------------------------------------------------

        batch_op.add_column(
            sa.Column(
                "class_department",
                sa.String(length=150),
                nullable=True,
            )
        )

        batch_op.add_column(
            sa.Column(
                "hb_above_12_5",
                sa.String(length=20),
                server_default="Not Recorded",
                nullable=False,
            )
        )

        batch_op.add_column(
            sa.Column(
                "regular_medication",
                sa.String(length=20),
                server_default="Not Recorded",
                nullable=False,
            )
        )

        batch_op.add_column(
            sa.Column(
                "bp_normal",
                sa.String(length=20),
                server_default="Not Recorded",
                nullable=False,
            )
        )

        # --------------------------------------------------
        # Allow incomplete historical/imported donor data
        # --------------------------------------------------

        batch_op.alter_column(
            "gender",
            existing_type=sa.String(length=20),
            nullable=True,
        )

        batch_op.alter_column(
            "date_of_birth",
            existing_type=sa.Date(),
            nullable=True,
        )

        batch_op.alter_column(
            "phone",
            existing_type=sa.String(length=30),
            nullable=True,
        )

        batch_op.alter_column(
            "district",
            existing_type=sa.String(length=100),
            nullable=True,
        )

        batch_op.alter_column(
            "city",
            existing_type=sa.String(length=100),
            nullable=True,
        )

        # --------------------------------------------------
        # Blood-group filtering performance
        # --------------------------------------------------

        batch_op.create_index(
            "ix_donors_blood_group",
            ["blood_group"],
            unique=False,
        )


# ==========================================================
# DOWNGRADE
# ==========================================================

def downgrade() -> None:
    """
    Restore the previous donor table structure.

    Note:
    A downgrade can only restore NOT NULL constraints if all
    existing donor records contain values for those fields.
    """

    with op.batch_alter_table("donors") as batch_op:

        # --------------------------------------------------
        # Remove blood-group index
        # --------------------------------------------------

        batch_op.drop_index(
            "ix_donors_blood_group"
        )

        # --------------------------------------------------
        # Restore previous required fields
        # --------------------------------------------------

        batch_op.alter_column(
            "city",
            existing_type=sa.String(length=100),
            nullable=False,
        )

        batch_op.alter_column(
            "district",
            existing_type=sa.String(length=100),
            nullable=False,
        )

        batch_op.alter_column(
            "phone",
            existing_type=sa.String(length=30),
            nullable=False,
        )

        batch_op.alter_column(
            "date_of_birth",
            existing_type=sa.Date(),
            nullable=False,
        )

        batch_op.alter_column(
            "gender",
            existing_type=sa.String(length=20),
            nullable=False,
        )

        # --------------------------------------------------
        # Remove new donor fields
        # --------------------------------------------------

        batch_op.drop_column(
            "bp_normal"
        )

        batch_op.drop_column(
            "regular_medication"
        )

        batch_op.drop_column(
            "hb_above_12_5"
        )

        batch_op.drop_column(
            "class_department"
        )