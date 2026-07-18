"""Extend blood request details.

Revision ID: 22abb347eeb6
Revises: 0001_initial_schema
Create Date: 2026-07-18
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


# ==========================================================
# REVISION IDENTIFIERS
# ==========================================================

revision = "22abb347eeb6"
down_revision = "0001_initial_schema"
branch_labels = None
depends_on = None


# ==========================================================
# UPGRADE
# ==========================================================

def upgrade() -> None:
    """Add detailed patient and contact fields to blood requests."""

    # ------------------------------------------------------
    # Step 1:
    # Add required columns as temporarily nullable.
    #
    # This allows the migration to work even if older
    # blood request records already exist.
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

        batch_op.add_column(
            sa.Column(
                "required_date",
                sa.Date(),
                nullable=True,
            )
        )

        batch_op.add_column(
            sa.Column(
                "contact_person",
                sa.String(length=200),
                nullable=True,
            )
        )

        batch_op.add_column(
            sa.Column(
                "contact_phone",
                sa.String(length=30),
                nullable=True,
            )
        )

        batch_op.add_column(
            sa.Column(
                "additional_notes",
                sa.Text(),
                nullable=True,
            )
        )


    # ------------------------------------------------------
    # Step 2:
    # Populate safe values for any existing legacy records.
    # ------------------------------------------------------

    op.execute(
        """
        UPDATE blood_requests
        SET
            patient_age = COALESCE(patient_age, 1),
            patient_gender = COALESCE(patient_gender, 'Not specified'),
            required_date = COALESCE(required_date, DATE(created_at)),
            contact_person = COALESCE(contact_person, 'Not specified'),
            contact_phone = COALESCE(contact_phone, 'Not specified')
        """
    )


    # ------------------------------------------------------
    # Step 3:
    # Make required fields NOT NULL after legacy rows
    # have valid values.
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

        batch_op.alter_column(
            "required_date",
            existing_type=sa.Date(),
            nullable=False,
        )

        batch_op.alter_column(
            "contact_person",
            existing_type=sa.String(length=200),
            nullable=False,
        )

        batch_op.alter_column(
            "contact_phone",
            existing_type=sa.String(length=30),
            nullable=False,
        )


# ==========================================================
# DOWNGRADE
# ==========================================================

def downgrade() -> None:
    """Remove the detailed blood request fields."""

    with op.batch_alter_table("blood_requests") as batch_op:

        batch_op.drop_column("additional_notes")
        batch_op.drop_column("contact_phone")
        batch_op.drop_column("contact_person")
        batch_op.drop_column("required_date")
        batch_op.drop_column("patient_gender")
        batch_op.drop_column("patient_age")