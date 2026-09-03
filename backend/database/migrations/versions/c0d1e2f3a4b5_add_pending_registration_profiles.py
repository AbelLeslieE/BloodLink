"""Add pending-registration state and structured donor profiles.

Revision ID: c0d1e2f3a4b5
Revises: b9c0d1e2f3a4
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "c0d1e2f3a4b5"
down_revision = "b9c0d1e2f3a4"
branch_labels = None
depends_on = None


def upgrade() -> None:
    columns = {column["name"] for column in sa.inspect(op.get_bind()).get_columns("users")}
    with op.batch_alter_table("users") as batch:
        if "registration_status" not in columns:
            batch.add_column(sa.Column("registration_status", sa.String(30), nullable=False, server_default="ACTIVE"))
        if "email_verified_at" not in columns:
            batch.add_column(sa.Column("email_verified_at", sa.DateTime(timezone=True), nullable=True))
        if "password_setup_token_hash" not in columns:
            batch.add_column(sa.Column("password_setup_token_hash", sa.String(128), nullable=True, unique=True))
        if "password_setup_expires_at" not in columns:
            batch.add_column(sa.Column("password_setup_expires_at", sa.DateTime(timezone=True), nullable=True))
        if "password_setup_sent_at" not in columns:
            batch.add_column(sa.Column("password_setup_sent_at", sa.DateTime(timezone=True), nullable=True))

    if "donor_profiles" not in sa.inspect(op.get_bind()).get_table_names():
        op.create_table(
            "donor_profiles",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("donor_id", sa.Integer(), sa.ForeignKey("donors.id", ondelete="CASCADE"), nullable=False, unique=True, index=True),
            sa.Column("current_status", sa.String(40), nullable=False),
            sa.Column("education_level", sa.String(40)), sa.Column("education_level_other", sa.String(150)),
            sa.Column("institution_name", sa.String(255)), sa.Column("school_class", sa.String(40)),
            sa.Column("education_board", sa.String(100)), sa.Column("education_board_other", sa.String(150)),
            sa.Column("stream", sa.String(60)), sa.Column("course_level", sa.String(100)),
            sa.Column("course_level_other", sa.String(150)), sa.Column("course_name", sa.String(150)),
            sa.Column("academic_department", sa.String(150)), sa.Column("semester_or_year", sa.String(40)),
            sa.Column("university", sa.String(150)), sa.Column("expected_graduation_year", sa.Integer()),
            sa.Column("employment_type", sa.String(60)), sa.Column("employment_type_other", sa.String(150)),
            sa.Column("occupation", sa.String(150)), sa.Column("organization_name", sa.String(200)),
            sa.Column("employment_department", sa.String(150)), sa.Column("industry", sa.String(100)),
            sa.Column("industry_other", sa.String(150)), sa.Column("work_location", sa.String(200)),
            sa.Column("previous_occupation", sa.String(150)), sa.Column("area_of_interest", sa.String(150)),
            sa.Column("status_description", sa.String(300)),
        )


def downgrade() -> None:
    op.drop_table("donor_profiles")
    with op.batch_alter_table("users") as batch:
        batch.drop_column("password_setup_sent_at")
        batch.drop_column("password_setup_expires_at")
        batch.drop_column("password_setup_token_hash")
        batch.drop_column("email_verified_at")
        batch.drop_column("registration_status")
