"""Allow donation records to capture external donors."""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "e8f9a0b1c2d3"
down_revision = "c5e6f7a8b9d0"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Make the registered donor optional and store an external donor name."""
    columns = {
        column["name"]
        for column in sa.inspect(op.get_bind()).get_columns("donation_history")
    }
    with op.batch_alter_table("donation_history") as batch:
        if "external_donor_name" not in columns:
            batch.add_column(sa.Column("external_donor_name", sa.String(200), nullable=True))
        batch.alter_column(
            "donor_id",
            existing_type=sa.Integer(),
            existing_nullable=False,
            nullable=True,
        )


def downgrade() -> None:
    """Remove external-donor support after removing its dependent records."""
    bind = op.get_bind()
    bind.execute(sa.text("DELETE FROM donation_history WHERE donor_id IS NULL"))
    with op.batch_alter_table("donation_history") as batch:
        batch.alter_column(
            "donor_id",
            existing_type=sa.Integer(),
            existing_nullable=True,
            nullable=False,
        )
        batch.drop_column("external_donor_name")
