"""Add communication queue context fields.

Revision ID: 0031_comm_queue_context
Revises: 0030_cna_access_fields
Create Date: 2026-06-04
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "0031_comm_queue_context"
down_revision = "0030_cna_access_fields"
branch_labels = None
depends_on = None


def _columns(table_name: str) -> set[str]:
    return {col["name"] for col in sa.inspect(op.get_bind()).get_columns(table_name)}


def _foreign_keys(table_name: str) -> set[str]:
    return {fk["name"] for fk in sa.inspect(op.get_bind()).get_foreign_keys(table_name)}


def upgrade() -> None:
    columns = _columns("comm_message_queue")
    missing_columns = [
        ("contract_id", sa.Integer()),
        ("client_id", sa.Integer()),
        ("provider", sa.String(50)),
        ("provider_message_id", sa.String(100)),
    ]
    for name, column_type in missing_columns:
        if name not in columns:
            op.add_column("comm_message_queue", sa.Column(name, column_type, nullable=True))

    foreign_keys = _foreign_keys("comm_message_queue")
    if "fk_comm_message_queue_contract" not in foreign_keys:
        op.create_foreign_key(
            "fk_comm_message_queue_contract",
            "comm_message_queue",
            "contracts",
            ["contract_id"],
            ["id"],
            ondelete="SET NULL",
        )
    if "fk_comm_message_queue_client" not in foreign_keys:
        op.create_foreign_key(
            "fk_comm_message_queue_client",
            "comm_message_queue",
            "clients",
            ["client_id"],
            ["id"],
            ondelete="SET NULL",
        )


def downgrade() -> None:
    foreign_keys = _foreign_keys("comm_message_queue")
    if "fk_comm_message_queue_client" in foreign_keys:
        op.drop_constraint("fk_comm_message_queue_client", "comm_message_queue", type_="foreignkey")
    if "fk_comm_message_queue_contract" in foreign_keys:
        op.drop_constraint("fk_comm_message_queue_contract", "comm_message_queue", type_="foreignkey")

    columns = _columns("comm_message_queue")
    for name in ["provider_message_id", "provider", "client_id", "contract_id"]:
        if name in columns:
            op.drop_column("comm_message_queue", name)
