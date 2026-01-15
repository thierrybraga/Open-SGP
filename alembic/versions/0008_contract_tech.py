"""
Arquivo: alembic/versions/0008_contract_tech.py

Responsabilidade:
Cria tabelas de informações técnicas do contrato: equipamentos, medições, speedtests, logs.

Integrações:
- app.modules.contract_tech.models
"""

from alembic import op
import sqlalchemy as sa


revision = "0008_contract_tech"
down_revision = "0007_network"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "contract_equipments",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("contract_id", sa.Integer(), sa.ForeignKey("contracts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("device_type", sa.String(30), nullable=False),
        sa.Column("vendor", sa.String(30), nullable=False),
        sa.Column("model", sa.String(60), nullable=False),
        sa.Column("serial_number", sa.String(60), nullable=False),
        sa.Column("installed_at", sa.DateTime(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )

    op.create_table(
        "signal_measurements",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("contract_id", sa.Integer(), sa.ForeignKey("contracts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("rx_level_dbm", sa.Float(), nullable=False),
        sa.Column("tx_level_dbm", sa.Float(), nullable=False),
        sa.Column("snr_db", sa.Float(), nullable=False),
        sa.Column("measured_at", sa.DateTime(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )

    op.create_table(
        "speed_tests",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("contract_id", sa.Integer(), sa.ForeignKey("contracts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("download_mbps", sa.Float(), nullable=False),
        sa.Column("upload_mbps", sa.Float(), nullable=False),
        sa.Column("latency_ms", sa.Integer(), nullable=False),
        sa.Column("jitter_ms", sa.Integer(), nullable=False),
        sa.Column("tested_at", sa.DateTime(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )

    op.create_table(
        "tech_logs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("contract_id", sa.Integer(), sa.ForeignKey("contracts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("event", sa.String(60), nullable=False),
        sa.Column("details", sa.String(500), nullable=False),
        sa.Column("occurred_at", sa.DateTime(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )


def downgrade():
    op.drop_table("tech_logs")
    op.drop_table("speed_tests")
    op.drop_table("signal_measurements")
    op.drop_table("contract_equipments")

