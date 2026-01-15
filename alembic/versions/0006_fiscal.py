"""
Arquivo: alembic/versions/0006_fiscal.py

Responsabilidade:
Cria tabela de invoices com campos fiscais e vinculação a contratos/títulos.

Integrações:
- app.modules.fiscal.models
"""

from alembic import op
import sqlalchemy as sa


revision = "0006_fiscal"
down_revision = "0005_billing"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "invoices",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("contract_id", sa.Integer(), sa.ForeignKey("contracts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title_id", sa.Integer(), sa.ForeignKey("titles.id", ondelete="SET NULL"), nullable=True),
        sa.Column("number", sa.String(20), nullable=False),
        sa.Column("series", sa.String(5), nullable=False, server_default="1"),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("issue_date", sa.Date(), nullable=True),
        sa.Column("cancel_date", sa.Date(), nullable=True),
        sa.Column("total_amount", sa.Float(), nullable=False),
        sa.Column("service_description", sa.String(500), nullable=False),
        sa.Column("municipality_code", sa.String(10), nullable=False),
        sa.Column("taxation_code", sa.String(10), nullable=False, server_default="0000"),
        sa.Column("xml_path", sa.String(500), nullable=True),
        sa.Column("pdf_url", sa.String(500), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_invoices_status", "invoices", ["status"]) 
    op.create_index("ix_invoices_number", "invoices", ["number"]) 


def downgrade():
    op.drop_index("ix_invoices_number")
    op.drop_index("ix_invoices_status")
    op.drop_table("invoices")

