"""Align support schema with current models.

Revision ID: 0032_support_schema
Revises: 0031_comm_queue_context
Create Date: 2026-06-04
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "0032_support_schema"
down_revision = "0031_comm_queue_context"
branch_labels = None
depends_on = None


def _inspector():
    return sa.inspect(op.get_bind())


def _tables() -> set[str]:
    return set(_inspector().get_table_names())


def _columns(table_name: str) -> set[str]:
    if table_name not in _tables():
        return set()
    return {col["name"] for col in _inspector().get_columns(table_name)}


def _foreign_keys(table_name: str) -> set[str]:
    if table_name not in _tables():
        return set()
    return {fk["name"] for fk in _inspector().get_foreign_keys(table_name)}


def upgrade() -> None:
    tables = _tables()

    if "support_categories" not in tables:
        op.create_table(
            "support_categories",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("name", sa.String(100), nullable=False, unique=True),
            sa.Column("description", sa.String(255), nullable=True),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
            sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        )

    ticket_columns = _columns("support_tickets")
    if ticket_columns:
        missing_ticket_columns = [
            ("protocol", sa.String(20)),
            ("category_id", sa.Integer()),
            ("assignee_id", sa.Integer()),
            ("description", sa.Text()),
            ("origin", sa.String(20)),
        ]
        for name, column_type in missing_ticket_columns:
            if name not in ticket_columns:
                op.add_column("support_tickets", sa.Column(name, column_type, nullable=True))

        if "category" in ticket_columns:
            op.alter_column("support_tickets", "category", existing_type=sa.String(50), nullable=True)
        if "opened_at" in ticket_columns:
            op.alter_column("support_tickets", "opened_at", existing_type=sa.DateTime(), nullable=True)

        foreign_keys = _foreign_keys("support_tickets")
        if "fk_support_tickets_category" not in foreign_keys:
            op.create_foreign_key(
                "fk_support_tickets_category",
                "support_tickets",
                "support_categories",
                ["category_id"],
                ["id"],
            )
        if "fk_support_tickets_assignee" not in foreign_keys:
            op.create_foreign_key(
                "fk_support_tickets_assignee",
                "support_tickets",
                "users",
                ["assignee_id"],
                ["id"],
            )
        if "uq_support_tickets_protocol" not in {c["name"] for c in _inspector().get_unique_constraints("support_tickets")}:
            op.create_unique_constraint("uq_support_tickets_protocol", "support_tickets", ["protocol"])

    if "support_messages" not in _tables():
        op.create_table(
            "support_messages",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("ticket_id", sa.Integer(), sa.ForeignKey("support_tickets.id", ondelete="CASCADE"), nullable=False),
            sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
            sa.Column("content", sa.Text(), nullable=False),
            sa.Column("is_internal", sa.Boolean(), nullable=False, server_default=sa.text("false")),
            sa.Column("attachment_url", sa.String(255), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        )
        op.create_index("ix_support_messages_ticket_id", "support_messages", ["ticket_id"])

    if "occurrences" not in _tables():
        op.create_table(
            "occurrences",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("client_id", sa.Integer(), sa.ForeignKey("clients.id", ondelete="SET NULL"), nullable=True),
            sa.Column("contract_id", sa.Integer(), sa.ForeignKey("contracts.id", ondelete="SET NULL"), nullable=True),
            sa.Column("category", sa.String(50), nullable=False, server_default="general"),
            sa.Column("severity", sa.String(20), nullable=False, server_default="medium"),
            sa.Column("description", sa.Text(), nullable=False),
            sa.Column("status", sa.String(20), nullable=False, server_default="open"),
            sa.Column("ticket_id", sa.Integer(), sa.ForeignKey("support_tickets.id", ondelete="SET NULL"), nullable=True),
            sa.Column("service_order_id", sa.Integer(), nullable=True),
            sa.Column("closed_at", sa.DateTime(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        )
        op.create_index("ix_occurrences_client_id", "occurrences", ["client_id"])
        op.create_index("ix_occurrences_contract_id", "occurrences", ["contract_id"])


def downgrade() -> None:
    if "occurrences" in _tables():
        op.drop_index("ix_occurrences_contract_id", table_name="occurrences")
        op.drop_index("ix_occurrences_client_id", table_name="occurrences")
        op.drop_table("occurrences")

    if "support_messages" in _tables():
        op.drop_index("ix_support_messages_ticket_id", table_name="support_messages")
        op.drop_table("support_messages")

    if "support_tickets" in _tables():
        foreign_keys = _foreign_keys("support_tickets")
        if "fk_support_tickets_assignee" in foreign_keys:
            op.drop_constraint("fk_support_tickets_assignee", "support_tickets", type_="foreignkey")
        if "fk_support_tickets_category" in foreign_keys:
            op.drop_constraint("fk_support_tickets_category", "support_tickets", type_="foreignkey")
        unique_constraints = {c["name"] for c in _inspector().get_unique_constraints("support_tickets")}
        if "uq_support_tickets_protocol" in unique_constraints:
            op.drop_constraint("uq_support_tickets_protocol", "support_tickets", type_="unique")

        columns = _columns("support_tickets")
        for name in ["origin", "description", "assignee_id", "category_id", "protocol"]:
            if name in columns:
                op.drop_column("support_tickets", name)

    if "support_categories" in _tables():
        op.drop_table("support_categories")
