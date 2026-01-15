"""
Arquivo: alembic/versions/0024_fiscal_enhancements.py

Responsabilidade:
Adiciona melhorias ao módulo fiscal: nota de débito, plano detalhe, gateways TV/Telefonia.

Integrações:
- app.modules.fiscal.models
"""

from alembic import op
import sqlalchemy as sa


revision = "0024_fiscal_enhancements"
down_revision = "0023_referrals_program"
branch_labels = None
depends_on = None


def upgrade():
    # Adicionar campos à tabela invoices
    op.add_column("invoices", sa.Column("invoice_type", sa.String(20), server_default="service", nullable=False))
    op.add_column("invoices", sa.Column("reference_invoice_id", sa.Integer(), nullable=True))
    op.add_column("invoices", sa.Column("debit_reason", sa.String(500), nullable=True))

    # Criar índice
    op.create_index("idx_invoices_type", "invoices", ["invoice_type"])

    # FK para reference_invoice_id
    op.create_foreign_key(
        "fk_invoices_reference_invoice",
        "invoices",
        "invoices",
        ["reference_invoice_id"],
        ["id"],
        ondelete="SET NULL"
    )

    # ===== SERVICE PLAN DETAILS =====
    op.create_table(
        "service_plan_details",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("plan_id", sa.Integer(), nullable=False),
        sa.Column("service_code", sa.String(20), nullable=False),
        sa.Column("cnae_code", sa.String(10), nullable=True),
        sa.Column("taxation_code", sa.String(10), server_default="0000", nullable=False),
        sa.Column("fiscal_description", sa.String(500), nullable=False),
        sa.Column("iss_rate", sa.Float(), server_default="0.0", nullable=False),
        sa.Column("cofins_rate", sa.Float(), server_default="0.0", nullable=False),
        sa.Column("pis_rate", sa.Float(), server_default="0.0", nullable=False),
        sa.Column("csll_rate", sa.Float(), server_default="0.0", nullable=False),
        sa.Column("irpj_rate", sa.Float(), server_default="0.0", nullable=False),
        sa.Column("iss_retention", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("municipality_code", sa.String(10), nullable=False),
        sa.Column("notes", sa.String(1000), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["plan_id"], ["plans.id"], ondelete="CASCADE"),
    )
    op.create_index("idx_service_plan_details_plan", "service_plan_details", ["plan_id"])

    # ===== TV TELEPHONY GATEWAYS =====
    op.create_table(
        "tv_telephony_gateways",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("gateway_type", sa.String(20), nullable=False),
        sa.Column("provider", sa.String(50), nullable=False),
        sa.Column("api_url", sa.String(500), nullable=False),
        sa.Column("api_key", sa.String(255), nullable=True),
        sa.Column("api_secret", sa.String(255), nullable=True),
        sa.Column("config_json", sa.String(2000), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("is_default", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("last_test_at", sa.String(30), nullable=True),
        sa.Column("last_test_success", sa.Boolean(), nullable=True),
        sa.Column("last_test_message", sa.String(500), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index("idx_tv_telephony_gateways_type", "tv_telephony_gateways", ["gateway_type"])
    op.create_index("idx_tv_telephony_gateways_active", "tv_telephony_gateways", ["is_active"])


def downgrade():
    # Remover TV/Telephony gateways
    op.drop_index("idx_tv_telephony_gateways_active", "tv_telephony_gateways")
    op.drop_index("idx_tv_telephony_gateways_type", "tv_telephony_gateways")
    op.drop_table("tv_telephony_gateways")

    # Remover service plan details
    op.drop_index("idx_service_plan_details_plan", "service_plan_details")
    op.drop_table("service_plan_details")

    # Remover campos de invoices
    op.drop_constraint("fk_invoices_reference_invoice", "invoices", type_="foreignkey")
    op.drop_index("idx_invoices_type", "invoices")
    op.drop_column("invoices", "debit_reason")
    op.drop_column("invoices", "reference_invoice_id")
    op.drop_column("invoices", "invoice_type")
