"""
Arquivo: alembic/versions/0005_billing.py

Responsabilidade:
Cria tabelas de financeiro: títulos, pagamentos, remessas, retornos e promessas.

Integrações:
- app.modules.billing.models
"""

from alembic import op
import sqlalchemy as sa


revision = "0005_billing"
down_revision = "0004_contracts"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "titles",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("contract_id", sa.Integer(), sa.ForeignKey("contracts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("issue_date", sa.Date(), nullable=False),
        sa.Column("due_date", sa.Date(), nullable=False),
        sa.Column("paid_date", sa.Date(), nullable=True),
        sa.Column("amount", sa.Float(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("fine_percent", sa.Float(), nullable=False, server_default="2"),
        sa.Column("interest_percent", sa.Float(), nullable=False, server_default="1"),
        sa.Column("bank_code", sa.String(10), nullable=False, server_default="341"),
        sa.Column("document_number", sa.String(30), nullable=False, unique=True),
        sa.Column("our_number", sa.String(20), nullable=False, unique=True),
        sa.Column("payment_slip_url", sa.String(500), nullable=True),
        sa.Column("bar_code", sa.String(100), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_titles_status", "titles", ["status"]) 
    op.create_index("ix_titles_due_date", "titles", ["due_date"]) 

    op.create_table(
        "payments",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("title_id", sa.Integer(), sa.ForeignKey("titles.id", ondelete="CASCADE"), nullable=False),
        sa.Column("payment_date", sa.Date(), nullable=False),
        sa.Column("amount", sa.Float(), nullable=False),
        sa.Column("method", sa.String(20), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )

    op.create_table(
        "remittances",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("file_name", sa.String(100), nullable=False),
        sa.Column("generated_at", sa.DateTime(), nullable=False),
        sa.Column("total_titles", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("status", sa.String(20), nullable=False, server_default="generated"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )

    op.create_table(
        "remittance_items",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("remittance_id", sa.Integer(), sa.ForeignKey("remittances.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title_id", sa.Integer(), sa.ForeignKey("titles.id", ondelete="CASCADE"), nullable=False),
        sa.Column("value", sa.Float(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )

    op.create_table(
        "return_files",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("file_name", sa.String(100), nullable=False),
        sa.Column("processed_at", sa.DateTime(), nullable=True),
        sa.Column("total_items", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )

    op.create_table(
        "return_items",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("return_file_id", sa.Integer(), sa.ForeignKey("return_files.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title_id", sa.Integer(), sa.ForeignKey("titles.id", ondelete="SET NULL"), nullable=True),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("value", sa.Float(), nullable=False),
        sa.Column("occurred_at", sa.Date(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )

    op.create_table(
        "payment_promises",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("client_id", sa.Integer(), sa.ForeignKey("clients.id", ondelete="CASCADE"), nullable=False),
        sa.Column("contract_id", sa.Integer(), sa.ForeignKey("contracts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title_id", sa.Integer(), sa.ForeignKey("titles.id", ondelete="SET NULL"), nullable=True),
        sa.Column("promised_date", sa.Date(), nullable=False),
        sa.Column("amount", sa.Float(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="open"),
        sa.Column("notes", sa.String(500), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )


def downgrade():
    op.drop_table("payment_promises")
    op.drop_table("return_items")
    op.drop_table("return_files")
    op.drop_table("remittance_items")
    op.drop_table("remittances")
    op.drop_table("payments")
    op.drop_index("ix_titles_due_date")
    op.drop_index("ix_titles_status")
    op.drop_table("titles")

