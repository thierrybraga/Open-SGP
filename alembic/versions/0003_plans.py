"""
Arquivo: alembic/versions/0003_plans.py

Responsabilidade:
Cria a tabela de planos com campos técnicos e comerciais.

Integrações:
- app.modules.plans.models
"""

from alembic import op
import sqlalchemy as sa


revision = "0003_plans"
down_revision = "0002_clients"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "plans",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(150), nullable=False, unique=True),
        sa.Column("category", sa.String(20), nullable=False),
        sa.Column("description", sa.String(500), nullable=False),
        sa.Column("download_speed_mbps", sa.Float(), nullable=False, server_default="0"),
        sa.Column("upload_speed_mbps", sa.Float(), nullable=False, server_default="0"),
        sa.Column("burst_enabled", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("burst_rate_percent", sa.Float(), nullable=False, server_default="0"),
        sa.Column("burst_threshold_seconds", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("price", sa.Float(), nullable=False, server_default="0"),
        sa.Column("loyalty_months", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_plans_category", "plans", ["category"]) 
    op.create_index("ix_plans_active", "plans", ["is_active"]) 


def downgrade():
    op.drop_index("ix_plans_active")
    op.drop_index("ix_plans_category")
    op.drop_table("plans")

