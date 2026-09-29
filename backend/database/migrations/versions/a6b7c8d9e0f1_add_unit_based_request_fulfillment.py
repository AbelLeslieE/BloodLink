"""Track partial and multi-donor request fulfilment by unit.

Revision ID: a6b7c8d9e0f1
Revises: f2a3b4c5d6e7
Create Date: 2026-09-27
"""

from alembic import op
import sqlalchemy as sa


revision = "a6b7c8d9e0f1"
down_revision = "f2a3b4c5d6e7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "blood_requests",
        sa.Column("units_fulfilled", sa.Integer(), server_default="0", nullable=False),
    )

    bind = op.get_bind()
    metadata = sa.MetaData()
    requests = sa.Table("blood_requests", metadata, autoload_with=bind)
    donations = sa.Table("donation_history", metadata, autoload_with=bind)

    totals = dict(bind.execute(
        sa.select(
            donations.c.blood_request_id,
            sa.func.coalesce(sa.func.sum(donations.c.units), 0),
        ).group_by(donations.c.blood_request_id)
    ).all())

    for row in bind.execute(
        sa.select(requests.c.id, requests.c.units_required, requests.c.status)
    ).mappings():
        fulfilled = min(int(totals.get(row["id"], 0)), int(row["units_required"]))
        values = {"units_fulfilled": fulfilled}
        if row["status"] not in {"Closed", "Cancelled"}:
            if fulfilled >= row["units_required"]:
                values["status"] = "Fulfilled"
            elif fulfilled > 0:
                values["status"] = "Partially Fulfilled"
            elif row["status"] == "Fulfilled":
                # Older versions allowed a manual status click to claim
                # fulfilment without any corresponding donation record.
                values["status"] = "In Progress"
        bind.execute(requests.update().where(requests.c.id == row["id"]).values(**values))


def downgrade() -> None:
    op.drop_column("blood_requests", "units_fulfilled")
