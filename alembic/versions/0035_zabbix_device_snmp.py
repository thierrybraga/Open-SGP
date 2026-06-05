"""Add per-device Zabbix SNMP community.

Revision ID: 0035_zabbix_device_snmp
Revises: 0034_orm_indexes
Create Date: 2026-06-04
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "0035_zabbix_device_snmp"
down_revision = "0034_orm_indexes"
branch_labels = None
depends_on = None


def _columns(table_name: str) -> set[str]:
    return {col["name"] for col in sa.inspect(op.get_bind()).get_columns(table_name)}


def upgrade() -> None:
    if "zabbix_snmp_community" not in _columns("network_devices"):
        op.add_column("network_devices", sa.Column("zabbix_snmp_community", sa.String(100), nullable=True))


def downgrade() -> None:
    if "zabbix_snmp_community" in _columns("network_devices"):
        op.drop_column("network_devices", "zabbix_snmp_community")
