"""
Arquivo: alembic/versions/0020_due_dates_discounts_comodato.py

Responsabilidade:
Cria tabelas de Vencimentos, Descontos e Comodato.

Integrações:
- app.modules.due_dates.models
- app.modules.discounts.models
- app.modules.stock.models (Comodato)
"""

from alembic import op
import sqlalchemy as sa


revision = "0020_due_dates_discounts_comodato"
down_revision = "0019_viability_contracts_cashier"
branch_labels = None
depends_on = None


def upgrade():
    # ===== DUE DATES =====
    op.create_table(
        "due_date_configs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("client_id", sa.Integer(), nullable=True),
        sa.Column("plan_id", sa.Integer(), nullable=True),
        sa.Column("due_day", sa.Integer(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("priority", sa.String(20), nullable=False, server_default="global"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["client_id"], ["clients.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["plan_id"], ["plans.id"], ondelete="CASCADE"),
    )
    op.create_index("idx_due_date_configs_client", "due_date_configs", ["client_id"])
    op.create_index("idx_due_date_configs_plan", "due_date_configs", ["plan_id"])
    op.create_index("idx_due_date_configs_priority", "due_date_configs", ["priority"])

    # ===== PLAN DISCOUNTS =====
    op.create_table(
        "plan_discounts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("plan_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(150), nullable=False),
        sa.Column("description", sa.String(500), nullable=True),
        sa.Column("discount_type", sa.String(20), nullable=False),
        sa.Column("discount_value", sa.Float(), nullable=False),
        sa.Column("duration_months", sa.Integer(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["plan_id"], ["plans.id"], ondelete="CASCADE"),
    )
    op.create_index("idx_plan_discounts_plan", "plan_discounts", ["plan_id"])
    op.create_index("idx_plan_discounts_active", "plan_discounts", ["is_active"])

    # ===== PAYMENT METHOD DISCOUNTS =====
    op.create_table(
        "payment_method_discounts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(150), nullable=False),
        sa.Column("description", sa.String(500), nullable=True),
        sa.Column("payment_method", sa.String(50), nullable=False),
        sa.Column("discount_type", sa.String(20), nullable=False),
        sa.Column("discount_value", sa.Float(), nullable=False),
        sa.Column("plan_id", sa.Integer(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["plan_id"], ["plans.id"], ondelete="CASCADE"),
    )
    op.create_index("idx_payment_method_discounts_method", "payment_method_discounts", ["payment_method"])
    op.create_index("idx_payment_method_discounts_active", "payment_method_discounts", ["is_active"])

    # ===== COMODATO =====
    op.create_table(
        "comodatos",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("client_id", sa.Integer(), nullable=False),
        sa.Column("contract_id", sa.Integer(), nullable=True),
        sa.Column("item_id", sa.Integer(), nullable=False),
        sa.Column("warehouse_id", sa.Integer(), nullable=False),
        sa.Column("serial_number", sa.String(100), nullable=True),
        sa.Column("quantity", sa.Float(), nullable=False, server_default="1.0"),
        sa.Column("status", sa.String(20), nullable=False, server_default="active"),
        sa.Column("loan_date", sa.String(30), nullable=False),
        sa.Column("return_date", sa.String(30), nullable=True),
        sa.Column("expected_return_date", sa.String(30), nullable=True),
        sa.Column("declared_value", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("loan_notes", sa.String(500), nullable=True),
        sa.Column("return_notes", sa.String(500), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["client_id"], ["clients.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["contract_id"], ["contracts.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["item_id"], ["stock_items.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["warehouse_id"], ["warehouses.id"], ondelete="RESTRICT"),
    )
    op.create_index("ix_comodatos_client", "comodatos", ["client_id"])
    op.create_index("ix_comodatos_status", "comodatos", ["status"])


def downgrade():
    # Remover comodatos
    op.drop_index("ix_comodatos_status", "comodatos")
    op.drop_index("ix_comodatos_client", "comodatos")
    op.drop_table("comodatos")

    # Remover payment method discounts
    op.drop_index("idx_payment_method_discounts_active", "payment_method_discounts")
    op.drop_index("idx_payment_method_discounts_method", "payment_method_discounts")
    op.drop_table("payment_method_discounts")

    # Remover plan discounts
    op.drop_index("idx_plan_discounts_active", "plan_discounts")
    op.drop_index("idx_plan_discounts_plan", "plan_discounts")
    op.drop_table("plan_discounts")

    # Remover due dates
    op.drop_index("idx_due_date_configs_priority", "due_date_configs")
    op.drop_index("idx_due_date_configs_plan", "due_date_configs")
    op.drop_index("idx_due_date_configs_client", "due_date_configs")
    op.drop_table("due_date_configs")
