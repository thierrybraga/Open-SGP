"""
Arquivo: alembic/versions/0004_contracts.py

Responsabilidade:
Cria a tabela de contratos com FKs para clientes e planos e índices úteis.

Integrações:
- app.modules.contracts.models
"""

from alembic import op
import sqlalchemy as sa


revision = "0004_contracts"
down_revision = "0003_plans"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "contracts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("client_id", sa.Integer(), sa.ForeignKey("clients.id", ondelete="CASCADE"), nullable=False),
        sa.Column("plan_id", sa.Integer(), sa.ForeignKey("plans.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=True),
        sa.Column("installation_address", sa.String(500), nullable=False),
        sa.Column("billing_day", sa.Integer(), nullable=False, server_default="10"),
        sa.Column("suspend_on_arrears", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("loyalty_months", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("price_override", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_contracts_status", "contracts", ["status"]) 
    op.create_index("ix_contracts_client", "contracts", ["client_id"]) 
    op.create_index("ix_contracts_plan", "contracts", ["plan_id"]) 


def downgrade():
    op.drop_index("ix_contracts_plan")
    op.drop_index("ix_contracts_client")
    op.drop_index("ix_contracts_status")
    op.drop_table("contracts")

