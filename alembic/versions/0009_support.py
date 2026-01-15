"""
Arquivo: alembic/versions/0009_support.py

Responsabilidade:
Cria tabelas de suporte: tickets, mensagens e tags.

Integrações:
- app.modules.support.models
"""

from alembic import op
import sqlalchemy as sa


revision = "0009_support"
down_revision = "0008_contract_tech"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "support_tags",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(50), nullable=False, unique=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )

    op.create_table(
        "support_tickets",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("client_id", sa.Integer(), sa.ForeignKey("clients.id", ondelete="SET NULL"), nullable=True),
        sa.Column("contract_id", sa.Integer(), sa.ForeignKey("contracts.id", ondelete="SET NULL"), nullable=True),
        sa.Column("subject", sa.String(200), nullable=False),
        sa.Column("category", sa.String(50), nullable=False),
        sa.Column("priority", sa.String(20), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("sla_due_at", sa.DateTime(), nullable=True),
        sa.Column("opened_at", sa.DateTime(), nullable=False),
        sa.Column("closed_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_support_tickets_status", "support_tickets", ["status"]) 
    op.create_index("ix_support_tickets_priority", "support_tickets", ["priority"]) 

    op.create_table(
        "ticket_tags",
        sa.Column("ticket_id", sa.Integer(), sa.ForeignKey("support_tickets.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("tag_id", sa.Integer(), sa.ForeignKey("support_tags.id", ondelete="CASCADE"), primary_key=True),
    )

    op.create_table(
        "support_ticket_messages",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("ticket_id", sa.Integer(), sa.ForeignKey("support_tickets.id", ondelete="CASCADE"), nullable=False),
        sa.Column("author", sa.String(100), nullable=False),
        sa.Column("content", sa.String(2000), nullable=False),
        sa.Column("internal", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )


def downgrade():
    op.drop_table("support_ticket_messages")
    op.drop_table("ticket_tags")
    op.drop_index("ix_support_tickets_priority")
    op.drop_index("ix_support_tickets_status")
    op.drop_table("support_tickets")
    op.drop_table("support_tags")

