"""
Arquivo: alembic/versions/0012_reports.py

Responsabilidade:
Cria tabelas de Relatórios/Dashboards: definições, widgets e logs de execução.

Integrações:
- app.modules.reports.models
"""

from alembic import op
import sqlalchemy as sa


revision = "0012_reports"
down_revision = "0011_communication"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "report_definitions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("code", sa.String(60), nullable=False, unique=True),
        sa.Column("query_type", sa.String(20), nullable=False),
        sa.Column("parameters", sa.JSON(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )

    op.create_table(
        "dashboard_widgets",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("code", sa.String(60), nullable=False, unique=True),
        sa.Column("type", sa.String(20), nullable=False),
        sa.Column("config", sa.JSON(), nullable=True),
        sa.Column("position_row", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("position_col", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("size_x", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("size_y", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )

    op.create_table(
        "report_execution_logs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("report_id", sa.Integer(), nullable=False),
        sa.Column("executed_at", sa.DateTime(), nullable=False),
        sa.Column("duration_ms", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("error", sa.String(500), nullable=True),
        sa.Column("rows_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )


def downgrade():
    op.drop_table("report_execution_logs")
    op.drop_table("dashboard_widgets")
    op.drop_table("report_definitions")

