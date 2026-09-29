"""Reconcile historical prototype constraints with the current models.

Revision ID: 0a1b2c3d4e5f
Revises: f1a2b3c4d5e6
Create Date: 2026-09-29
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "0a1b2c3d4e5f"
down_revision = "f1a2b3c4d5e6"
branch_labels = None
depends_on = None


def _column_sets(items: list[dict]) -> set[tuple[str, ...]]:
    return {
        tuple(item.get("column_names") or ())
        for item in items
    }


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    duplicate = bind.execute(sa.text(
        "SELECT donor_id, blood_request_id, COUNT(*) AS response_count "
        "FROM donor_responses "
        "GROUP BY donor_id, blood_request_id "
        "HAVING COUNT(*) > 1 "
        "LIMIT 1"
    )).mappings().first()
    if duplicate is not None:
        raise RuntimeError(
            "Cannot add the donor-response uniqueness safeguard because duplicate "
            f"rows exist for donor {duplicate['donor_id']} and request "
            f"{duplicate['blood_request_id']}. Resolve those records without "
            "discarding response history, then run the migration again."
        )

    response_columns = {
        column["name"]: column
        for column in inspector.get_columns("donor_responses")
    }
    response_unique_columns = _column_sets(
        inspector.get_unique_constraints("donor_responses")
    )
    response_indexes = {
        index["name"]
        for index in inspector.get_indexes("donor_responses")
    }
    with op.batch_alter_table("donor_responses") as batch_op:
        if not response_columns["email_token_id"]["nullable"]:
            batch_op.alter_column(
                "email_token_id",
                existing_type=sa.Integer(),
                nullable=True,
            )
        if ("donor_id", "blood_request_id") not in response_unique_columns:
            batch_op.create_unique_constraint(
                "uq_donor_response_donor_request",
                ["donor_id", "blood_request_id"],
            )
        if "ix_donor_responses_id" not in response_indexes:
            batch_op.create_index("ix_donor_responses_id", ["id"], unique=False)

    inspector = sa.inspect(bind)
    user_constraints = inspector.get_unique_constraints("users")
    user_indexes = inspector.get_indexes("users")
    user_unique_columns = _column_sets(user_constraints) | {
        tuple(index.get("column_names") or ())
        for index in user_indexes
        if index.get("unique")
    }
    # Do not rebuild the live users table merely to change a unique constraint
    # into an equivalent unique index. SQLite cannot safely perform that table
    # swap while sessions, requests, and audit records reference users. Create
    # a non-destructive unique index only when the protection is truly absent.
    if ("donor_id",) not in user_unique_columns:
        op.create_index("ix_users_donor_id", "users", ["donor_id"], unique=True)
    if ("password_setup_token_hash",) not in user_unique_columns:
        op.create_index(
            "ix_users_password_setup_token_hash",
            "users",
            ["password_setup_token_hash"],
            unique=True,
        )


def downgrade() -> None:
    raise RuntimeError(
        "Downgrade is intentionally unsupported for the schema-reconciliation "
        "migration because older schemas can reject portal-only donor responses."
    )
