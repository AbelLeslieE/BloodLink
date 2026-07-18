"""Create the initial BloodLink database schema.

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-07-17
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "0001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create the initial BloodLink tables and supporting indexes."""
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("username", sa.String(length=100), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("full_name", sa.String(length=200), nullable=False),
        sa.Column(
            "active",
            sa.Boolean(),
            server_default=sa.text("true"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column("last_login", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_users")),
    )
    op.create_index("ix_users_username", "users", ["username"], unique=True)

    op.create_table(
        "donors",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("donor_code", sa.String(length=30), nullable=False),
        sa.Column("full_name", sa.String(length=200), nullable=False),
        sa.Column("gender", sa.String(length=20), nullable=False),
        sa.Column("date_of_birth", sa.Date(), nullable=False),
        sa.Column("blood_group", sa.String(length=5), nullable=False),
        sa.Column("phone", sa.String(length=30), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.Column("district", sa.String(length=100), nullable=False),
        sa.Column("city", sa.String(length=100), nullable=False),
        sa.Column("address", sa.Text(), nullable=True),
        sa.Column("latitude", sa.Numeric(precision=9, scale=6), nullable=True),
        sa.Column("longitude", sa.Numeric(precision=9, scale=6), nullable=True),
        sa.Column("weight", sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column("medical_conditions", sa.Text(), nullable=True),
        sa.Column("last_donation_date", sa.Date(), nullable=True),
        sa.Column(
            "total_donations",
            sa.Integer(),
            server_default=sa.text("0"),
            nullable=False,
        ),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_donors")),
    )
    op.create_index("ix_donors_donor_code", "donors", ["donor_code"], unique=True)
    op.create_index("ix_donors_phone", "donors", ["phone"], unique=False)

    op.create_table(
        "blood_requests",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("patient_name", sa.String(length=200), nullable=False),
        sa.Column("hospital_name", sa.String(length=200), nullable=False),
        sa.Column("hospital_location", sa.String(length=255), nullable=False),
        sa.Column("blood_group", sa.String(length=5), nullable=False),
        sa.Column("units_required", sa.Integer(), nullable=False),
        sa.Column("priority", sa.String(length=50), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("created_by", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["created_by"],
            ["users.id"],
            name=op.f("fk_blood_requests_created_by_users"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_blood_requests")),
    )
    op.create_index(
        "ix_blood_requests_created_by",
        "blood_requests",
        ["created_by"],
        unique=False,
    )

    op.create_table(
        "donation_history",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("donor_id", sa.Integer(), nullable=False),
        sa.Column("blood_request_id", sa.Integer(), nullable=False),
        sa.Column("hospital_name", sa.String(length=200), nullable=False),
        sa.Column("donation_date", sa.Date(), nullable=False),
        sa.Column("remarks", sa.Text(), nullable=True),
        sa.Column("recorded_by", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["blood_request_id"],
            ["blood_requests.id"],
            name=op.f("fk_donation_history_blood_request_id_blood_requests"),
        ),
        sa.ForeignKeyConstraint(
            ["donor_id"],
            ["donors.id"],
            name=op.f("fk_donation_history_donor_id_donors"),
        ),
        sa.ForeignKeyConstraint(
            ["recorded_by"],
            ["users.id"],
            name=op.f("fk_donation_history_recorded_by_users"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_donation_history")),
    )
    op.create_index(
        "ix_donation_history_blood_request_id",
        "donation_history",
        ["blood_request_id"],
        unique=False,
    )
    op.create_index(
        "ix_donation_history_donor_id",
        "donation_history",
        ["donor_id"],
        unique=False,
    )
    op.create_index(
        "ix_donation_history_recorded_by",
        "donation_history",
        ["recorded_by"],
        unique=False,
    )

    op.create_table(
        "notifications",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("blood_request_id", sa.Integer(), nullable=False),
        sa.Column("donor_id", sa.Integer(), nullable=False),
        sa.Column("notification_status", sa.String(length=50), nullable=False),
        sa.Column("response", sa.String(length=100), nullable=True),
        sa.Column(
            "sent_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column("responded_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["blood_request_id"],
            ["blood_requests.id"],
            name=op.f("fk_notifications_blood_request_id_blood_requests"),
        ),
        sa.ForeignKeyConstraint(
            ["donor_id"],
            ["donors.id"],
            name=op.f("fk_notifications_donor_id_donors"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_notifications")),
    )
    op.create_index(
        "ix_notifications_blood_request_id",
        "notifications",
        ["blood_request_id"],
        unique=False,
    )
    op.create_index(
        "ix_notifications_donor_id",
        "notifications",
        ["donor_id"],
        unique=False,
    )


def downgrade() -> None:
    """Remove the initial BloodLink tables and supporting indexes."""
    op.drop_index("ix_notifications_donor_id", table_name="notifications")
    op.drop_index(
        "ix_notifications_blood_request_id",
        table_name="notifications",
    )
    op.drop_table("notifications")

    op.drop_index("ix_donation_history_recorded_by", table_name="donation_history")
    op.drop_index("ix_donation_history_donor_id", table_name="donation_history")
    op.drop_index(
        "ix_donation_history_blood_request_id",
        table_name="donation_history",
    )
    op.drop_table("donation_history")

    op.drop_index("ix_blood_requests_created_by", table_name="blood_requests")
    op.drop_table("blood_requests")

    op.drop_index("ix_donors_phone", table_name="donors")
    op.drop_index("ix_donors_donor_code", table_name="donors")
    op.drop_table("donors")

    op.drop_index("ix_users_username", table_name="users")
    op.drop_table("users")
