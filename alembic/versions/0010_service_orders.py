"""
Arquivo: alembic/versions/0010_service_orders.py

Responsabilidade:
Cria tabelas de ordens de serviço e itens.

Integrações:
- app.modules.service_orders.models
"""

from alembic import op
import sqlalchemy as sa


revision = "0010_service_orders"
down_revision = "0009_support"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "service_orders",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("client_id", sa.Integer(), sa.ForeignKey("clients.id", ondelete="SET NULL"), nullable=True),
        sa.Column("contract_id", sa.Integer(), sa.ForeignKey("contracts.id", ondelete="SET NULL"), nullable=True),
        sa.Column("ticket_id", sa.Integer(), sa.ForeignKey("support_tickets.id", ondelete="SET NULL"), nullable=True),
        sa.Column("type", sa.String(30), nullable=False),
        sa.Column("priority", sa.String(20), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("technician_name", sa.String(100), nullable=True),
        sa.Column("scheduled_at", sa.DateTime(), nullable=True),
        sa.Column("executed_at", sa.DateTime(), nullable=True),
        sa.Column("notes", sa.String(1000), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_service_orders_status", "service_orders", ["status"]) 
    op.create_index("ix_service_orders_type", "service_orders", ["type"]) 

    op.create_table(
        "service_order_items",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("order_id", sa.Integer(), sa.ForeignKey("service_orders.id", ondelete="CASCADE"), nullable=False),
        sa.Column("description", sa.String(200), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("done", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )


def downgrade():
    op.drop_table("service_order_items")
    op.drop_index("ix_service_orders_type")
    op.drop_index("ix_service_orders_status")
    op.drop_table("service_orders")

