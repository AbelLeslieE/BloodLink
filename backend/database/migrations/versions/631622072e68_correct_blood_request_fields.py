"""Correct blood request fields.

Revision ID: 631622072e68
Revises: 22abb347eeb6
Create Date: 2026-07-18
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


# ==========================================================
# REVISION IDENTIFIERS
# ==========================================================

revision = "631622072e68"
down_revision = "22abb347eeb6"
branch_labels = None
depends_on = None


# ==========================================================
# UPGRADE
# ==========================================================

def upgrade() -> None:
    """
    Correct the Blood Request structure.

    - Add case_details
    - Preserve existing request records
    - Remove patient_age
    - Remove patient_gender
    """

    # ------------------------------------------------------
    # 1. Add case_details temporarily as nullable
    # ------------------------------------------------------

    with op.batch_alter_table("blood_requests") as batch_op:

        batch_op.add_column(
            sa.Column(
                "case_details",
                sa.String(length=255),
                nullable=True,
            )
        )

    # ------------------------------------------------------
    # 2. Give existing legacy requests a safe value
    # ------------------------------------------------------

    op.execute(
        """
        UPDATE blood_requests
        SET case_details = 'Not specified'
        WHERE case_details IS NULL
        """
    )

    # ------------------------------------------------------
    # 3. Make case_details required and remove obsolete fields
    # ------------------------------------------------------

    with op.batch_alter_table("blood_requests") as batch_op:

        batch_op.alter_column(
            "case_details",
            existing_type=sa.String(length=255),
            nullable=False,
        )

        batch_op.drop_column(
            "patient_gender"
        )

        batch_op.drop_column(
            "patient_age"
        )


# ==========================================================
# DOWNGRADE
# ==========================================================

def downgrade() -> None:
    """
    Restore the previous Blood Request structure.
    """

    # ------------------------------------------------------
    # 1. Restore old fields temporarily as nullable
    # ------------------------------------------------------

    with op.batch_alter_table("blood_requests") as batch_op:

        batch_op.add_column(
            sa.Column(
                "patient_age",
                sa.Integer(),
                nullable=True,
            )
        )

        batch_op.add_column(
            sa.Column(
                "patient_gender",
                sa.String(length=20),
                nullable=True,
            )
        )

    # ------------------------------------------------------
    # 2. Populate restored fields for existing records
    # ------------------------------------------------------

    op.execute(
        """
        UPDATE blood_requests
        SET
            patient_age = 1,
            patient_gender = 'Not specified'
        WHERE
            patient_age IS NULL
            OR patient_gender IS NULL
        """
    )

    # ------------------------------------------------------
    # 3. Restore NOT NULL constraints and remove case_details
    # ------------------------------------------------------

    with op.batch_alter_table("blood_requests") as batch_op:

        batch_op.alter_column(
            "patient_age",
            existing_type=sa.Integer(),
            nullable=False,
        )

        batch_op.alter_column(
            "patient_gender",
            existing_type=sa.String(length=20),
            nullable=False,
        )

        batch_op.drop_column(
            "case_details"
        )