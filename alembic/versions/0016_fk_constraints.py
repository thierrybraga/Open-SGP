"""
Arquivo: alembic/versions/0016_fk_constraints.py

Responsabilidade:
Adiciona chaves estrangeiras faltantes para garantir integridade referencial.

Integrações:
- múltiplos módulos
"""

from alembic import op
import sqlalchemy as sa


revision = "0016_fk_constraints"
down_revision = "0015_technician_app"
branch_labels = None
depends_on = None


def upgrade():
    op.create_foreign_key(
        "fk_stock_movements_item",
        "stock_movements",
        "stock_items",
        ["item_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "fk_stock_movements_warehouse",
        "stock_movements",
        "warehouses",
        ["warehouse_id"],
        ["id"],
        ondelete="CASCADE",
    )

    op.create_foreign_key(
        "fk_customer_preferences_client",
        "customer_preferences",
        "clients",
        ["client_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "fk_customer_device_tokens_client",
        "customer_device_tokens",
        "clients",
        ["client_id"],
        ["id"],
        ondelete="CASCADE",
    )

    op.create_foreign_key(
        "fk_technician_work_logs_order",
        "technician_work_logs",
        "service_orders",
        ["order_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "fk_technician_work_logs_user",
        "technician_work_logs",
        "users",
        ["user_id"],
        ["id"],
        ondelete="CASCADE",
    )

    op.create_foreign_key(
        "fk_technician_material_usages_order",
        "technician_material_usages",
        "service_orders",
        ["order_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "fk_technician_material_usages_item",
        "technician_material_usages",
        "stock_items",
        ["item_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.create_foreign_key(
        "fk_technician_material_usages_warehouse",
        "technician_material_usages",
        "warehouses",
        ["warehouse_id"],
        ["id"],
        ondelete="RESTRICT",
    )

    op.create_foreign_key(
        "fk_report_execution_logs_report",
        "report_execution_logs",
        "report_definitions",
        ["report_id"],
        ["id"],
        ondelete="CASCADE",
    )

    op.create_foreign_key(
        "fk_comm_message_queue_template",
        "comm_message_queue",
        "comm_templates",
        ["template_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade():
    op.drop_constraint("fk_comm_message_queue_template", "comm_message_queue", type_="foreignkey")
    op.drop_constraint("fk_report_execution_logs_report", "report_execution_logs", type_="foreignkey")
    op.drop_constraint("fk_technician_material_usages_warehouse", "technician_material_usages", type_="foreignkey")
    op.drop_constraint("fk_technician_material_usages_item", "technician_material_usages", type_="foreignkey")
    op.drop_constraint("fk_technician_material_usages_order", "technician_material_usages", type_="foreignkey")
    op.drop_constraint("fk_technician_work_logs_user", "technician_work_logs", type_="foreignkey")
    op.drop_constraint("fk_technician_work_logs_order", "technician_work_logs", type_="foreignkey")
    op.drop_constraint("fk_customer_device_tokens_client", "customer_device_tokens", type_="foreignkey")
    op.drop_constraint("fk_customer_preferences_client", "customer_preferences", type_="foreignkey")
    op.drop_constraint("fk_stock_movements_warehouse", "stock_movements", type_="foreignkey")
    op.drop_constraint("fk_stock_movements_item", "stock_movements", type_="foreignkey")

