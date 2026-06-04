"""Create indexes declared by ORM models.

Revision ID: 0034_orm_indexes
Revises: 0033_schema_consolidation
Create Date: 2026-06-04
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "0034_orm_indexes"
down_revision = "0033_schema_consolidation"
branch_labels = None
depends_on = None


INDEXES: list[tuple[str, str, list[str]]] = [
    ("ix_anatel_reports_reference_period", "anatel_reports", ["reference_period"]),
    ("ix_anatel_reports_reference_year", "anatel_reports", ["reference_year"]),
    ("ix_cash_movements_client_id", "cash_movements", ["client_id"]),
    ("ix_cash_movements_title_id", "cash_movements", ["title_id"]),
    ("ix_client_addresses_client_id", "client_addresses", ["client_id"]),
    ("ix_client_contacts_client_id", "client_contacts", ["client_id"]),
    ("ix_comodatos_item_id", "comodatos", ["item_id"]),
    ("ix_comodatos_warehouse_id", "comodatos", ["warehouse_id"]),
    ("ix_contract_addendums_created_by", "contract_addendums", ["created_by"]),
    ("ix_contract_tech_history_contract_id", "contract_tech_history", ["contract_id"]),
    ("ix_customer_device_tokens_client_id", "customer_device_tokens", ["client_id"]),
    ("ix_customer_preferences_client_id", "customer_preferences", ["client_id"]),
    ("ix_nas_ip_address", "nas", ["ip_address"]),
    ("ix_payment_promises_client_id", "payment_promises", ["client_id"]),
    ("ix_payment_promises_contract_id", "payment_promises", ["contract_id"]),
    ("ix_payments_title_id", "payments", ["title_id"]),
    ("ix_radippool_nasipaddress", "radippool", ["nasipaddress"]),
    ("ix_remittance_items_remittance_id", "remittance_items", ["remittance_id"]),
    ("ix_remittance_items_title_id", "remittance_items", ["title_id"]),
    ("ix_report_definitions_name", "report_definitions", ["name"]),
    ("ix_report_execution_logs_report_id", "report_execution_logs", ["report_id"]),
    ("ix_return_items_return_file_id", "return_items", ["return_file_id"]),
    ("ix_service_order_items_order_id", "service_order_items", ["order_id"]),
    ("ix_stock_items_name", "stock_items", ["name"]),
    ("ix_stock_movements_item_id", "stock_movements", ["item_id"]),
    ("ix_stock_movements_warehouse_id", "stock_movements", ["warehouse_id"]),
    ("ix_support_tickets_client_id", "support_tickets", ["client_id"]),
    ("ix_support_tickets_contract_id", "support_tickets", ["contract_id"]),
    ("ix_technician_material_usages_item_id", "technician_material_usages", ["item_id"]),
    ("ix_technician_material_usages_order_id", "technician_material_usages", ["order_id"]),
    ("ix_technician_material_usages_warehouse_id", "technician_material_usages", ["warehouse_id"]),
    ("ix_technician_profiles_user_id", "technician_profiles", ["user_id"]),
    ("ix_technician_work_logs_order_id", "technician_work_logs", ["order_id"]),
    ("ix_technician_work_logs_user_id", "technician_work_logs", ["user_id"]),
    ("ix_titles_contract_id", "titles", ["contract_id"]),
    ("ix_viabilities_address_id", "viabilities", ["address_id"]),
    ("ix_viabilities_analyzed_by", "viabilities", ["analyzed_by"]),
    ("ix_viabilities_plan_id", "viabilities", ["plan_id"]),
    ("ix_vlans_device_id", "vlans", ["device_id"]),
]


def _tables() -> set[str]:
    return set(sa.inspect(op.get_bind()).get_table_names())


def _indexes(table_name: str) -> set[str]:
    return {idx["name"] for idx in sa.inspect(op.get_bind()).get_indexes(table_name)}


def upgrade() -> None:
    tables = _tables()
    for index_name, table_name, columns in INDEXES:
        if table_name in tables and index_name not in _indexes(table_name):
            op.create_index(index_name, table_name, columns)


def downgrade() -> None:
    tables = _tables()
    for index_name, table_name, _columns in reversed(INDEXES):
        if table_name in tables and index_name in _indexes(table_name):
            op.drop_index(index_name, table_name=table_name)
