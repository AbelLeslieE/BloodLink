"""Add ranked staged donor outreach controls.

Revision ID: f1a2b3c4d5e6
Revises: e0f1a2b3c4d5
Create Date: 2026-09-29
"""

from alembic import op
import sqlalchemy as sa


revision = "f1a2b3c4d5e6"
down_revision = "e0f1a2b3c4d5"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("notifications") as batch_op:
        batch_op.add_column(sa.Column("queued_count", sa.Integer(), server_default="0", nullable=False))
        batch_op.add_column(sa.Column("stage_size", sa.Integer(), server_default="5", nullable=False))
        batch_op.add_column(sa.Column("stage_delay_minutes", sa.Integer(), server_default="30", nullable=False))
        batch_op.add_column(sa.Column("current_stage", sa.Integer(), server_default="0", nullable=False))
        batch_op.add_column(sa.Column("target_acceptances", sa.Integer(), server_default="1", nullable=False))
        batch_op.add_column(sa.Column("last_stage_sent_at", sa.DateTime(timezone=True), nullable=True))
        batch_op.add_column(sa.Column("next_stage_at", sa.DateTime(timezone=True), nullable=True))

    with op.batch_alter_table("notification_recipients") as batch_op:
        batch_op.add_column(sa.Column("stage_number", sa.Integer(), server_default="1", nullable=False))
        batch_op.add_column(sa.Column("outreach_order", sa.Integer(), server_default="1", nullable=False))
        batch_op.alter_column(
            "sent_at",
            existing_type=sa.DateTime(timezone=True),
            nullable=True,
            server_default=None,
        )

    bind = op.get_bind()
    metadata = sa.MetaData()
    campaigns = sa.Table("notifications", metadata, autoload_with=bind)
    recipients = sa.Table("notification_recipients", metadata, autoload_with=bind)
    requests = sa.Table("blood_requests", metadata, autoload_with=bind)

    request_units = {
        row.id: max(1, int(row.units_required) - int(row.units_fulfilled or 0))
        for row in bind.execute(
            sa.select(requests.c.id, requests.c.units_required, requests.c.units_fulfilled)
        )
    }
    for campaign in bind.execute(
        sa.select(campaigns.c.id, campaigns.c.blood_request_id, campaigns.c.sent_at)
    ).mappings():
        recipient_ids = list(bind.execute(
            sa.select(recipients.c.id)
            .where(recipients.c.notification_id == campaign["id"])
            .order_by(recipients.c.id)
        ).scalars())
        bind.execute(
            campaigns.update().where(campaigns.c.id == campaign["id"]).values(
                stage_size=max(1, len(recipient_ids)),
                current_stage=1 if recipient_ids else 0,
                target_acceptances=request_units.get(campaign["blood_request_id"], 1),
                last_stage_sent_at=campaign["sent_at"],
            )
        )
        for order, recipient_id in enumerate(recipient_ids, start=1):
            bind.execute(
                recipients.update().where(recipients.c.id == recipient_id).values(
                    stage_number=1,
                    outreach_order=order,
                )
            )


def downgrade() -> None:
    with op.batch_alter_table("notification_recipients") as batch_op:
        batch_op.alter_column(
            "sent_at",
            existing_type=sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        )
        batch_op.drop_column("outreach_order")
        batch_op.drop_column("stage_number")

    with op.batch_alter_table("notifications") as batch_op:
        batch_op.drop_column("next_stage_at")
        batch_op.drop_column("last_stage_sent_at")
        batch_op.drop_column("target_acceptances")
        batch_op.drop_column("current_stage")
        batch_op.drop_column("stage_delay_minutes")
        batch_op.drop_column("stage_size")
        batch_op.drop_column("queued_count")
