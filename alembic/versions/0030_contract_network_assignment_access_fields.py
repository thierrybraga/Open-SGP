"""Add network assignment access fields.

Revision ID: 0030_cna_access_fields
Revises: 0029_client_password_hash
Create Date: 2026-06-04
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "0030_cna_access_fields"
down_revision = "0029_client_password_hash"
branch_labels = None
depends_on = None


def _columns(table_name: str) -> set[str]:
    return {col["name"] for col in sa.inspect(op.get_bind()).get_columns(table_name)}


def _unique_constraints(table_name: str) -> set[str]:
    return {constraint["name"] for constraint in sa.inspect(op.get_bind()).get_unique_constraints(table_name)}


def upgrade() -> None:
    columns = _columns("contract_network_assignments")
    missing_columns = [
        ("pppoe_user", sa.String(64)),
        ("pppoe_password", sa.String(64)),
        ("mac_address", sa.String(17)),
        ("wifi_ssid", sa.String(64)),
        ("wifi_password", sa.String(64)),
    ]
    for name, column_type in missing_columns:
        if name not in columns:
            op.add_column("contract_network_assignments", sa.Column(name, column_type, nullable=True))

    if "uq_cna_pppoe_user" not in _unique_constraints("contract_network_assignments"):
        op.create_unique_constraint("uq_cna_pppoe_user", "contract_network_assignments", ["pppoe_user"])


def downgrade() -> None:
    if "uq_cna_pppoe_user" in _unique_constraints("contract_network_assignments"):
        op.drop_constraint("uq_cna_pppoe_user", "contract_network_assignments", type_="unique")

    columns = _columns("contract_network_assignments")
    for name in ["wifi_password", "wifi_ssid", "mac_address", "pppoe_password", "pppoe_user"]:
        if name in columns:
            op.drop_column("contract_network_assignments", name)
