"""Add soft delete to existing models

Revision ID: 0026_soft_delete
Revises: 0025_anatel_reports
Create Date: 2024-01-01 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "0026_soft_delete"
down_revision = "0025_anatel_reports"
branch_labels = None
depends_on = None


TABLES = [
    "users", "roles", "permissions", "role_permissions", "user_roles",
    "clients", "client_contacts", "client_addresses",
    "plans", "contracts", "contract_network_assignments",
    "titles", "payments", "title_adjustments", "payment_promises",
    "invoices", "invoice_items",
    "network_devices", "vlans", "ip_pools", "nas",
    "tickets", "ticket_messages", "service_orders", "occurrences",
    "warehouses", "stock_items", "stock_movements", "stock_adjustments",
    "stock_categories", "manufacturers", "vehicles", "kits", "kit_items",
    "comodatos", "purchases", "purchase_items", "transfers", "transfer_items", "suppliers",
    "comm_message_queue", "message_templates",
    "pops", "backups", "backup_executions", "companies", "carriers",
    "receipt_points", "financial_parameters",
    "employees", "email_servers", "email_configurations", "payment_gateways", "payment_gateway_configs",
    "viabilities", "discounts", "cash_registers", "cash_movements",
    "referrals", "referral_rewards",
]


def _inspector():
    return sa.inspect(op.get_bind())


def _tables() -> set[str]:
    return set(_inspector().get_table_names())


def _columns(table: str) -> set[str]:
    return {col["name"] for col in _inspector().get_columns(table)}


def _indexes(table: str) -> set[str]:
    return {idx["name"] for idx in _inspector().get_indexes(table)}


def upgrade():
    existing_tables = _tables()
    for table in TABLES:
        if table not in existing_tables:
            continue
        columns = _columns(table)
        if "deleted_at" not in columns:
            op.add_column(table, sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True))
        if "deleted_by" not in columns:
            op.add_column(table, sa.Column("deleted_by", sa.Integer(), nullable=True))
        index_name = f"ix_{table}_deleted_at"
        if index_name not in _indexes(table):
            op.create_index(index_name, table, ["deleted_at"])


def downgrade():
    existing_tables = _tables()
    for table in reversed(TABLES):
        if table not in existing_tables:
            continue
        columns = _columns(table)
        index_name = f"ix_{table}_deleted_at"
        if index_name in _indexes(table):
            op.drop_index(index_name, table_name=table)
        if "deleted_by" in columns:
            op.drop_column(table, "deleted_by")
        if "deleted_at" in columns:
            op.drop_column(table, "deleted_at")
