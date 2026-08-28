"""Add secure donor rewards, confirmations, and campaign tables.

This revision also reconciles the early prototype migration with the ORM schema
that was previously created at application startup.
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "3b8e9a1c4d20"
down_revision = "2d00ee800210"
branch_labels = None
depends_on = None


def _columns(table: str) -> set[str]:
    return {column["name"] for column in sa.inspect(op.get_bind()).get_columns(table)}


def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())

    # The initial migration predates account profiles. Defaults make this safe
    # for existing installations while preserving the current ORM contract.
    user_columns = _columns("users")
    with op.batch_alter_table("users") as batch:
        if "department" not in user_columns:
            batch.add_column(sa.Column("department", sa.String(100), nullable=False, server_default="Blood Bank"))
        if "role" not in user_columns:
            batch.add_column(sa.Column("role", sa.String(50), nullable=False, server_default="Donor"))
        if "email" not in user_columns:
            batch.add_column(sa.Column("email", sa.String(255), nullable=True))
        if "phone" not in user_columns:
            batch.add_column(sa.Column("phone", sa.String(20), nullable=False, server_default="Not recorded"))
        if "donor_id" not in user_columns:
            batch.add_column(sa.Column("donor_id", sa.Integer(), nullable=True))
        if "total_points" not in user_columns:
            batch.add_column(sa.Column("total_points", sa.Integer(), nullable=False, server_default="0"))
        if "donation_count" not in user_columns:
            batch.add_column(sa.Column("donation_count", sa.Integer(), nullable=False, server_default="0"))
        if "hide_from_leaderboard" not in user_columns:
            batch.add_column(sa.Column("hide_from_leaderboard", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.execute("UPDATE users SET email = 'legacy-' || id || '@local.invalid' WHERE email IS NULL")
    existing_user_constraints = {item["name"] for item in inspector.get_unique_constraints("users")}
    existing_user_fks = {item.get("name") for item in inspector.get_foreign_keys("users")}
    with op.batch_alter_table("users") as batch:
        batch.alter_column("email", existing_type=sa.String(255), nullable=False)
        if "uq_users_email" not in existing_user_constraints:
            batch.create_unique_constraint("uq_users_email", ["email"])
        if "fk_users_donor_id_donors" not in existing_user_fks:
            batch.create_foreign_key("fk_users_donor_id_donors", "donors", ["donor_id"], ["id"])
        if "uq_users_donor_id" not in existing_user_constraints:
            batch.create_unique_constraint("uq_users_donor_id", ["donor_id"])

    donor_columns = _columns("donors")
    with op.batch_alter_table("donors") as batch:
        if "total_points" not in donor_columns:
            batch.add_column(sa.Column("total_points", sa.Integer(), nullable=False, server_default="0"))
        if "donation_count" not in donor_columns:
            batch.add_column(sa.Column("donation_count", sa.Integer(), nullable=False, server_default="0"))
        if "hide_from_leaderboard" not in donor_columns:
            batch.add_column(sa.Column("hide_from_leaderboard", sa.Boolean(), nullable=False, server_default=sa.false()))

    # The old prototype used the same table name with incompatible columns.
    if "notifications" in inspector.get_table_names() and "title" not in _columns("notifications"):
        # SQLite index names are global. Remove the old conflicting index
        # before preserving the legacy table under a different name.
        old_indexes = {item["name"] for item in inspector.get_indexes("notifications")}
        if "ix_notifications_blood_request_id" in old_indexes:
            op.drop_index("ix_notifications_blood_request_id", table_name="notifications")
        op.rename_table("notifications", "legacy_notifications")
        inspector = sa.inspect(op.get_bind())
    if "notifications" not in inspector.get_table_names():
        op.create_table(
            "notifications",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("blood_request_id", sa.Integer(), sa.ForeignKey("blood_requests.id"), nullable=False, index=True),
            sa.Column("title", sa.String(255), nullable=False),
            sa.Column("status", sa.String(50), nullable=False, server_default="ACTIVE"),
            sa.Column("total_sent", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("accepted_count", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("declined_count", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("pending_count", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        )
    inspector = sa.inspect(op.get_bind())
    if "email_tokens" not in inspector.get_table_names():
        op.create_table(
            "email_tokens",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("token", sa.String(512), nullable=False, unique=True),
            sa.Column("used", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        )
    if "notification_recipients" not in inspector.get_table_names():
        op.create_table(
            "notification_recipients",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("notification_id", sa.Integer(), sa.ForeignKey("notifications.id"), nullable=False, index=True),
            sa.Column("donor_id", sa.Integer(), sa.ForeignKey("donors.id"), nullable=False, index=True),
            sa.Column("email_token_id", sa.Integer(), sa.ForeignKey("email_tokens.id"), nullable=True),
            sa.Column("email", sa.String(255), nullable=False),
            sa.Column("distance", sa.Float(), nullable=True),
            sa.Column("status", sa.String(20), nullable=False, server_default="PENDING"),
            sa.Column("sent_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.Column("responded_at", sa.DateTime(timezone=True), nullable=True),
        )
    if "donor_responses" not in inspector.get_table_names():
        op.create_table(
            "donor_responses",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("email_token_id", sa.Integer(), sa.ForeignKey("email_tokens.id"), nullable=True, index=True),
            sa.Column("donor_id", sa.Integer(), sa.ForeignKey("donors.id"), nullable=False, index=True),
            sa.Column("blood_request_id", sa.Integer(), sa.ForeignKey("blood_requests.id"), nullable=False, index=True),
            sa.Column("response", sa.String(20), nullable=False),
            sa.Column("remarks", sa.Text(), nullable=True),
            sa.Column("responded_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.UniqueConstraint("donor_id", "blood_request_id", name="uq_donor_response_donor_request"),
        )

    history_columns = _columns("donation_history")
    history_constraints = {item["name"] for item in inspector.get_unique_constraints("donation_history")}
    with op.batch_alter_table("donation_history") as batch:
        if "points_awarded" not in history_columns:
            batch.add_column(sa.Column("points_awarded", sa.Integer(), nullable=False, server_default="0"))
        if "status" not in history_columns:
            batch.add_column(sa.Column("status", sa.String(50), nullable=False, server_default="Donation Confirmed"))
        if "awarded_at" not in history_columns:
            batch.add_column(sa.Column("awarded_at", sa.DateTime(timezone=True), nullable=True))
        if "uq_donation_history_donor_request" not in history_constraints:
            batch.create_unique_constraint("uq_donation_history_donor_request", ["donor_id", "blood_request_id"])


def downgrade() -> None:
    # Data-bearing reward and campaign tables intentionally require a manual
    # migration plan before rollback in a production deployment.
    raise RuntimeError("Downgrade is not supported for the rewards migration.")
