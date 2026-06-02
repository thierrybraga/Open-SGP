"""Use fixed precision decimals for billing money

Revision ID: 0028_billing_decimal_money
Revises: 0027_encryption_upgrade
Create Date: 2026-06-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = "0028_billing_decimal_money"
down_revision = "0027_encryption_upgrade"
branch_labels = None
depends_on = None


MONEY_TABLE_COLUMNS = (
    ("titles", "amount"),
    ("payments", "amount"),
    ("remittance_items", "value"),
    ("return_items", "value"),
    ("payment_promises", "amount"),
    ("title_adjustments", "amount"),
    ("payment_charges", "amount"),
)


def upgrade():
    for table_name, column_name in MONEY_TABLE_COLUMNS:
        with op.batch_alter_table(table_name, schema=None) as batch_op:
            batch_op.alter_column(
                column_name,
                existing_type=sa.Float(),
                type_=sa.Numeric(12, 2),
                existing_nullable=False,
            )


def downgrade():
    for table_name, column_name in MONEY_TABLE_COLUMNS:
        with op.batch_alter_table(table_name, schema=None) as batch_op:
            batch_op.alter_column(
                column_name,
                existing_type=sa.Numeric(12, 2),
                type_=sa.Float(),
                existing_nullable=False,
            )
