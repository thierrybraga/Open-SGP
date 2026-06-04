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


def _inspector():
    return sa.inspect(op.get_bind())


def _tables() -> set[str]:
    return set(_inspector().get_table_names())


def _columns(table_name: str) -> set[str]:
    return {col["name"] for col in _inspector().get_columns(table_name)}


def _indexes(table_name: str) -> set[str]:
    return {idx["name"] for idx in _inspector().get_indexes(table_name)}


def _create_index_once(name: str, table_name: str, columns: list[str]) -> None:
    if name not in _indexes(table_name):
        op.create_index(name, table_name, columns)


def _ensure_billing_gap_tables() -> None:
    existing = _tables()
    if "title_adjustments" not in existing:
        op.create_table(
            "title_adjustments",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("title_id", sa.Integer(), nullable=False),
            sa.Column("type", sa.String(20), nullable=False),
            sa.Column("amount", sa.Float(), nullable=False),
            sa.Column("reason", sa.String(255), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(["title_id"], ["titles.id"], ondelete="CASCADE"),
        )
        _create_index_once("ix_title_adjustments_title_id", "title_adjustments", ["title_id"])
        _create_index_once("ix_title_adjustments_type", "title_adjustments", ["type"])

    existing = _tables()
    if "payment_gateway_configs" not in existing:
        op.create_table(
            "payment_gateway_configs",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("provider", sa.String(50), nullable=False),
            sa.Column("api_key", sa.String(255), nullable=False),
            sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.text("true")),
            sa.Column("webhook_secret", sa.String(255), nullable=True),
            sa.Column("hmac_algorithm", sa.String(10), nullable=False, server_default="sha256"),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), nullable=False),
        )

    existing = _tables()
    if "payment_charges" not in existing:
        op.create_table(
            "payment_charges",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("title_id", sa.Integer(), nullable=False),
            sa.Column("gateway_id", sa.Integer(), nullable=True),
            sa.Column("status", sa.String(20), nullable=False, server_default="created"),
            sa.Column("reference", sa.String(100), nullable=False),
            sa.Column("amount", sa.Float(), nullable=False, server_default="0"),
            sa.Column("payment_url", sa.String(500), nullable=True),
            sa.Column("external_id", sa.String(100), nullable=True),
            sa.Column("paid_at", sa.DateTime(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(["title_id"], ["titles.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["gateway_id"], ["payment_gateway_configs.id"], ondelete="SET NULL"),
        )
        _create_index_once("ix_payment_charges_reference", "payment_charges", ["reference"])


def _alter_money_columns(target_type, existing_type) -> None:
    existing_tables = _tables()
    for table_name, column_name in MONEY_TABLE_COLUMNS:
        if table_name not in existing_tables or column_name not in _columns(table_name):
            continue
        with op.batch_alter_table(table_name, schema=None) as batch_op:
            batch_op.alter_column(
                column_name,
                existing_type=existing_type,
                type_=target_type,
                existing_nullable=False,
            )


def upgrade():
    _ensure_billing_gap_tables()
    _alter_money_columns(sa.Numeric(12, 2), sa.Float())


def downgrade():
    _alter_money_columns(sa.Float(), sa.Numeric(12, 2))
