"""
Arquivo: alembic/versions/0018_suppliers.py

Responsabilidade:
Cria fornecedores e completa as tabelas de estoque que já existem nos modelos
atuais do módulo.
"""

from alembic import op
import sqlalchemy as sa


revision = "0018_suppliers"
down_revision = "0017_comm_retries"
branch_labels = None
depends_on = None


def _tables() -> set[str]:
    return set(sa.inspect(op.get_bind()).get_table_names())


def _indexes(table: str) -> set[str]:
    if table not in _tables():
        return set()
    return {idx["name"] for idx in sa.inspect(op.get_bind()).get_indexes(table)}


def _columns(table: str) -> set[str]:
    if table not in _tables():
        return set()
    return {col["name"] for col in sa.inspect(op.get_bind()).get_columns(table)}


def _create_index_once(name: str, table: str, columns: list[str]) -> None:
    if name not in _indexes(table):
        op.create_index(name, table, columns)


def upgrade():
    existing = _tables()

    if "suppliers" not in existing:
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
    _create_index_once("idx_suppliers_name", "suppliers", ["name"])
    _create_index_once("idx_suppliers_document", "suppliers", ["document"])

    existing = _tables()

    if "stock_adjustments" not in existing:
        op.create_table(
            "stock_adjustments",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("item_id", sa.Integer(), nullable=False),
            sa.Column("warehouse_id", sa.Integer(), nullable=False),
            sa.Column("type", sa.String(10), nullable=False),
            sa.Column("quantity", sa.Float(), nullable=False),
            sa.Column("reason", sa.String(255), nullable=False),
            sa.Column("ref_document", sa.String(100), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(["item_id"], ["stock_items.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["warehouse_id"], ["warehouses.id"], ondelete="CASCADE"),
        )
        _create_index_once("ix_stock_adjustments_item_id", "stock_adjustments", ["item_id"])
        _create_index_once("ix_stock_adjustments_warehouse_id", "stock_adjustments", ["warehouse_id"])

    if "stock_categories" not in existing:
        op.create_table(
            "stock_categories",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("name", sa.String(120), nullable=False, unique=True),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), nullable=False),
        )

    if "manufacturers" not in existing:
        op.create_table(
            "manufacturers",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("name", sa.String(120), nullable=False, unique=True),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), nullable=False),
        )

    if "vehicles" not in existing:
        op.create_table(
            "vehicles",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("plate", sa.String(10), nullable=False, unique=True),
            sa.Column("description", sa.String(150), nullable=False),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), nullable=False),
        )

    if "kits" not in existing:
        op.create_table(
            "kits",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("name", sa.String(120), nullable=False, unique=True),
            sa.Column("description", sa.String(255), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), nullable=False),
        )

    if "kit_items" not in existing:
        op.create_table(
            "kit_items",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("kit_id", sa.Integer(), nullable=False),
            sa.Column("item_id", sa.Integer(), nullable=False),
            sa.Column("quantity", sa.Float(), nullable=False, server_default="1.0"),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(["kit_id"], ["kits.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["item_id"], ["stock_items.id"], ondelete="RESTRICT"),
        )
        _create_index_once("ix_kit_items_kit_id", "kit_items", ["kit_id"])
        _create_index_once("ix_kit_items_item_id", "kit_items", ["item_id"])

    if "purchases" not in existing:
        op.create_table(
            "purchases",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("supplier_id", sa.Integer(), nullable=True),
            sa.Column("supplier_name", sa.String(150), nullable=False),
            sa.Column("document_number", sa.String(50), nullable=False, unique=True),
            sa.Column("total_value", sa.Float(), nullable=False, server_default="0.0"),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(["supplier_id"], ["suppliers.id"], ondelete="SET NULL"),
        )
    elif "supplier_id" not in _columns("purchases"):
        op.add_column("purchases", sa.Column("supplier_id", sa.Integer(), nullable=True))
        op.create_foreign_key(
            "fk_purchases_supplier",
            "purchases",
            "suppliers",
            ["supplier_id"],
            ["id"],
            ondelete="SET NULL",
        )
    _create_index_once("idx_purchases_supplier_id", "purchases", ["supplier_id"])

    if "purchase_items" not in existing:
        op.create_table(
            "purchase_items",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("purchase_id", sa.Integer(), nullable=False),
            sa.Column("item_id", sa.Integer(), nullable=False),
            sa.Column("quantity", sa.Float(), nullable=False),
            sa.Column("unit_cost", sa.Float(), nullable=False),
            sa.Column("warehouse_id", sa.Integer(), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(["purchase_id"], ["purchases.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["item_id"], ["stock_items.id"], ondelete="RESTRICT"),
            sa.ForeignKeyConstraint(["warehouse_id"], ["warehouses.id"], ondelete="RESTRICT"),
        )
        _create_index_once("ix_purchase_items_purchase_id", "purchase_items", ["purchase_id"])
        _create_index_once("ix_purchase_items_item_id", "purchase_items", ["item_id"])
        _create_index_once("ix_purchase_items_warehouse_id", "purchase_items", ["warehouse_id"])

    if "transfers" not in existing:
        op.create_table(
            "transfers",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("from_warehouse_id", sa.Integer(), nullable=False),
            sa.Column("to_warehouse_id", sa.Integer(), nullable=False),
            sa.Column("note", sa.String(255), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(["from_warehouse_id"], ["warehouses.id"], ondelete="RESTRICT"),
            sa.ForeignKeyConstraint(["to_warehouse_id"], ["warehouses.id"], ondelete="RESTRICT"),
        )
        _create_index_once("ix_transfers_from_warehouse_id", "transfers", ["from_warehouse_id"])
        _create_index_once("ix_transfers_to_warehouse_id", "transfers", ["to_warehouse_id"])

    if "transfer_items" not in existing:
        op.create_table(
            "transfer_items",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("transfer_id", sa.Integer(), nullable=False),
            sa.Column("item_id", sa.Integer(), nullable=False),
            sa.Column("quantity", sa.Float(), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(["transfer_id"], ["transfers.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["item_id"], ["stock_items.id"], ondelete="RESTRICT"),
        )
        _create_index_once("ix_transfer_items_transfer_id", "transfer_items", ["transfer_id"])
        _create_index_once("ix_transfer_items_item_id", "transfer_items", ["item_id"])


def downgrade():
    for table in [
        "transfer_items",
        "transfers",
        "purchase_items",
        "purchases",
        "kit_items",
        "kits",
        "vehicles",
        "manufacturers",
        "stock_categories",
        "stock_adjustments",
        "suppliers",
    ]:
        if table in _tables():
            op.drop_table(table)
