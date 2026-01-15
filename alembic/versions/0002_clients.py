"""
Arquivo: alembic/versions/0002_clients.py

Responsabilidade:
Cria as tabelas de clientes, endereços e contatos.

Integrações:
- app.modules.clients.models
"""

from alembic import op
import sqlalchemy as sa


revision = "0002_clients"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "clients",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("person_type", sa.String(2), nullable=False),
        sa.Column("name", sa.String(150), nullable=False),
        sa.Column("document", sa.String(20), nullable=False, unique=True),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("phone", sa.String(30), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_clients_name", "clients", ["name"]) 

    op.create_table(
        "client_addresses",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("client_id", sa.Integer(), sa.ForeignKey("clients.id", ondelete="CASCADE"), nullable=False),
        sa.Column("street", sa.String(255), nullable=False),
        sa.Column("number", sa.String(20), nullable=False),
        sa.Column("neighborhood", sa.String(120), nullable=False),
        sa.Column("city", sa.String(120), nullable=False),
        sa.Column("state", sa.String(2), nullable=False),
        sa.Column("zipcode", sa.String(20), nullable=False),
        sa.Column("is_primary", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_client_addresses_city", "client_addresses", ["city"]) 

    op.create_table(
        "client_contacts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("client_id", sa.Integer(), sa.ForeignKey("clients.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("phone", sa.String(30), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("role", sa.String(80), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )


def downgrade():
    op.drop_table("client_contacts")
    op.drop_index("ix_client_addresses_city")
    op.drop_table("client_addresses")
    op.drop_index("ix_clients_name")
    op.drop_table("clients")

