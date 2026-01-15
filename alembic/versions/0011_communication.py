"""
Arquivo: alembic/versions/0011_communication.py

Responsabilidade:
Cria tabelas de comunicação: templates e fila de mensagens.

Integrações:
- app.modules.communication.models
"""

from alembic import op
import sqlalchemy as sa


revision = "0011_communication"
down_revision = "0010_service_orders"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "comm_templates",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(100), nullable=False, unique=True),
        sa.Column("channel", sa.String(20), nullable=False),
        sa.Column("content", sa.String(2000), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )

    op.create_table(
        "comm_message_queue",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("channel", sa.String(20), nullable=False),
        sa.Column("destination", sa.String(200), nullable=False),
        sa.Column("content", sa.String(2000), nullable=False),
        sa.Column("template_id", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="queued"),
        sa.Column("scheduled_at", sa.DateTime(), nullable=True),
        sa.Column("dispatched_at", sa.DateTime(), nullable=True),
        sa.Column("error", sa.String(500), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )


def downgrade():
    op.drop_table("comm_message_queue")
    op.drop_table("comm_templates")

