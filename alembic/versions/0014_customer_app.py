"""
Arquivo: alembic/versions/0014_customer_app.py

Responsabilidade:
Cria tabelas do App do Cliente: preferências e tokens.

Integrações:
- app.modules.customer_app.models
"""

from alembic import op
import sqlalchemy as sa


revision = "0014_customer_app"
down_revision = "0013_stock"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "customer_preferences",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("client_id", sa.Integer(), nullable=False),
        sa.Column("notify_email", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("notify_sms", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("notify_whatsapp", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )

    op.create_table(
        "customer_device_tokens",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("client_id", sa.Integer(), nullable=False),
        sa.Column("platform", sa.String(20), nullable=False),
        sa.Column("token", sa.String(200), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )


def downgrade():
    op.drop_table("customer_device_tokens")
    op.drop_table("customer_preferences")

