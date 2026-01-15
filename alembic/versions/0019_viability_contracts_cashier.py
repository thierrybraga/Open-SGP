"""
Arquivo: alembic/versions/0019_viability_contracts_cashier.py

Responsabilidade:
Cria tabelas de Viabilidade, Templates de Contrato, Aditivos e Caixa.

Integrações:
- app.modules.viability.models
- app.modules.contract_templates.models
- app.modules.cashier.models
"""

from alembic import op
import sqlalchemy as sa


revision = "0019_viability_contracts_cashier"
down_revision = "0018_suppliers"
branch_labels = None
depends_on = None


def upgrade():
    # ===== VIABILIDADE =====
    op.create_table(
        "viabilities",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("client_id", sa.Integer(), nullable=False),
        sa.Column("address_id", sa.Integer(), nullable=True),
        sa.Column("plan_id", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("distance_to_pop", sa.Float(), nullable=True),
        sa.Column("signal_quality", sa.String(50), nullable=True),
        sa.Column("latitude", sa.Float(), nullable=True),
        sa.Column("longitude", sa.Float(), nullable=True),
        sa.Column("equipment_needed", sa.Text(), nullable=True),
        sa.Column("estimated_cost", sa.Float(), nullable=True),
        sa.Column("installation_complexity", sa.String(20), nullable=True),
        sa.Column("technician_notes", sa.Text(), nullable=True),
        sa.Column("rejection_reason", sa.Text(), nullable=True),
        sa.Column("analyzed_by", sa.Integer(), nullable=True),
        sa.Column("analyzed_at", sa.DateTime(), nullable=True),
        sa.Column("expires_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["client_id"], ["clients.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["address_id"], ["client_addresses.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["plan_id"], ["plans.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["analyzed_by"], ["users.id"], ondelete="SET NULL"),
    )
    op.create_index("idx_viabilities_client", "viabilities", ["client_id"])
    op.create_index("idx_viabilities_status", "viabilities", ["status"])

    # ===== TEMPLATES DE CONTRATO =====
    op.create_table(
        "contract_templates",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(150), nullable=False),
        sa.Column("version", sa.String(20), nullable=False),
        sa.Column("description", sa.String(500), nullable=True),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("available_variables", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("is_default", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_by", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="SET NULL"),
    )
    op.create_index("idx_contract_templates_name", "contract_templates", ["name"])

    # ===== ADITIVOS CONTRATUAIS =====
    op.create_table(
        "contract_addendums",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("contract_id", sa.Integer(), nullable=False),
        sa.Column("addendum_number", sa.Integer(), nullable=False),
        sa.Column("type", sa.String(50), nullable=False),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("effective_date", sa.DateTime(), nullable=False),
        sa.Column("old_value", sa.Text(), nullable=True),
        sa.Column("new_value", sa.Text(), nullable=True),
        sa.Column("document_url", sa.String(500), nullable=True),
        sa.Column("created_by", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["contract_id"], ["contracts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="RESTRICT"),
    )
    op.create_index("idx_contract_addendums_contract", "contract_addendums", ["contract_id"])

    # ===== CAIXA =====
    op.create_table(
        "cash_registers",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("opened_at", sa.DateTime(), nullable=False),
        sa.Column("closed_at", sa.DateTime(), nullable=True),
        sa.Column("opening_balance", sa.Float(), nullable=False, server_default="0"),
        sa.Column("closing_balance", sa.Float(), nullable=True),
        sa.Column("expected_balance", sa.Float(), nullable=True),
        sa.Column("difference", sa.Float(), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="open"),
        sa.Column("opening_notes", sa.Text(), nullable=True),
        sa.Column("closing_notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="RESTRICT"),
    )
    op.create_index("idx_cash_registers_user", "cash_registers", ["user_id"])
    op.create_index("idx_cash_registers_opened", "cash_registers", ["opened_at"])
    op.create_index("idx_cash_registers_status", "cash_registers", ["status"])

    # ===== MOVIMENTAÇÕES DE CAIXA =====
    op.create_table(
        "cash_movements",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("cash_register_id", sa.Integer(), nullable=False),
        sa.Column("type", sa.String(10), nullable=False),
        sa.Column("category", sa.String(50), nullable=False),
        sa.Column("amount", sa.Float(), nullable=False),
        sa.Column("title_id", sa.Integer(), nullable=True),
        sa.Column("client_id", sa.Integer(), nullable=True),
        sa.Column("payment_method", sa.String(50), nullable=True),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("document_number", sa.String(100), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["cash_register_id"], ["cash_registers.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["title_id"], ["titles.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["client_id"], ["clients.id"], ondelete="SET NULL"),
    )
    op.create_index("idx_cash_movements_register", "cash_movements", ["cash_register_id"])
    op.create_index("idx_cash_movements_type", "cash_movements", ["type"])
    op.create_index("idx_cash_movements_category", "cash_movements", ["category"])


def downgrade():
    # Remover movimentações de caixa
    op.drop_index("idx_cash_movements_category", "cash_movements")
    op.drop_index("idx_cash_movements_type", "cash_movements")
    op.drop_index("idx_cash_movements_register", "cash_movements")
    op.drop_table("cash_movements")

    # Remover caixa
    op.drop_index("idx_cash_registers_status", "cash_registers")
    op.drop_index("idx_cash_registers_opened", "cash_registers")
    op.drop_index("idx_cash_registers_user", "cash_registers")
    op.drop_table("cash_registers")

    # Remover aditivos
    op.drop_index("idx_contract_addendums_contract", "contract_addendums")
    op.drop_table("contract_addendums")

    # Remover templates
    op.drop_index("idx_contract_templates_name", "contract_templates")
    op.drop_table("contract_templates")

    # Remover viabilidade
    op.drop_index("idx_viabilities_status", "viabilities")
    op.drop_index("idx_viabilities_client", "viabilities")
    op.drop_table("viabilities")
