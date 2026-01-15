"""
Arquivo: alembic/versions/0021_client_pre_registration.py

Responsabilidade:
Adiciona campos de pré-cadastro e aprovação de clientes.

Integrações:
- app.modules.clients.models
"""

from alembic import op
import sqlalchemy as sa


revision = "0021_client_pre_registration"
down_revision = "0020_due_dates_discounts_comodato"
branch_labels = None
depends_on = None


def upgrade():
    # Adicionar campos de status e aprovação em clients
    op.add_column("clients", sa.Column("status", sa.String(20), nullable=False, server_default="active"))
    op.add_column("clients", sa.Column("approved_by", sa.Integer(), nullable=True))
    op.add_column("clients", sa.Column("approved_at", sa.String(30), nullable=True))

    # Criar índice para status
    op.create_index("idx_clients_status", "clients", ["status"])

    # Criar foreign key para approved_by
    op.create_foreign_key("fk_clients_approved_by", "clients", "users", ["approved_by"], ["id"], ondelete="SET NULL")


def downgrade():
    # Remover foreign key
    op.drop_constraint("fk_clients_approved_by", "clients", type_="foreignkey")

    # Remover índice
    op.drop_index("idx_clients_status", "clients")

    # Remover colunas
    op.drop_column("clients", "approved_at")
    op.drop_column("clients", "approved_by")
    op.drop_column("clients", "status")
