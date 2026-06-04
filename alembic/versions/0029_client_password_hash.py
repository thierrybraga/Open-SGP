"""Add client portal password hash

Revision ID: 0029_client_password_hash
Revises: 0028_billing_decimal_money
Create Date: 2026-06-04 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "0029_client_password_hash"
down_revision = "0028_billing_decimal_money"
branch_labels = None
depends_on = None


def _columns(table_name: str) -> set[str]:
    return {col["name"] for col in sa.inspect(op.get_bind()).get_columns(table_name)}


def upgrade():
    if "password_hash" not in _columns("clients"):
        op.add_column("clients", sa.Column("password_hash", sa.String(255), nullable=True))


def downgrade():
    if "password_hash" in _columns("clients"):
        op.drop_column("clients", "password_hash")
