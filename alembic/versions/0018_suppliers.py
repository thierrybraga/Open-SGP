"""
Arquivo: alembic/versions/0018_suppliers.py

Responsabilidade:
Cria tabela de Fornecedores (Suppliers) e adiciona relacionamento em purchases.

Integrações:
- app.modules.stock.models
"""

from alembic import op
import sqlalchemy as sa


revision = "0018_suppliers"
down_revision = "0017_comm_retries"
branch_labels = None
depends_on = None


def upgrade():
    # Criar tabela suppliers
    op.create_table(
        "suppliers",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(150), nullable=False),
        sa.Column("document", sa.String(20), nullable=False, unique=True),
        sa.Column("person_type", sa.String(2), nullable=False),
        sa.Column("email", sa.String(120), nullable=True),
        sa.Column("phone", sa.String(20), nullable=True),
        sa.Column("address", sa.String(255), nullable=True),
        sa.Column("city", sa.String(100), nullable=True),
        sa.Column("state", sa.String(2), nullable=True),
        sa.Column("postal_code", sa.String(10), nullable=True),
        sa.Column("contact_person", sa.String(120), nullable=True),
        sa.Column("payment_terms", sa.String(100), nullable=True),
        sa.Column("notes", sa.String(500), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )

    # Adicionar índices
    op.create_index("idx_suppliers_name", "suppliers", ["name"])
    op.create_index("idx_suppliers_document", "suppliers", ["document"])

    # Adicionar coluna supplier_id em purchases
    op.add_column("purchases", sa.Column("supplier_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "fk_purchases_supplier",
        "purchases",
        "suppliers",
        ["supplier_id"],
        ["id"],
        ondelete="SET NULL"
    )
    op.create_index("idx_purchases_supplier_id", "purchases", ["supplier_id"])


def downgrade():
    # Remover relacionamento em purchases
    op.drop_index("idx_purchases_supplier_id", "purchases")
    op.drop_constraint("fk_purchases_supplier", "purchases", type_="foreignkey")
    op.drop_column("purchases", "supplier_id")

    # Remover índices
    op.drop_index("idx_suppliers_document", "suppliers")
    op.drop_index("idx_suppliers_name", "suppliers")

    # Remover tabela suppliers
    op.drop_table("suppliers")
