"""
Arquivo: alembic/versions/0025_anatel_reports.py

Responsabilidade:
Adiciona tabela de relatórios ANATEL (SICI e PPP SCM).

Integrações:
- app.modules.anatel.models
"""

from alembic import op
import sqlalchemy as sa


revision = "0025_anatel_reports"
down_revision = "0024_fiscal_enhancements"
branch_labels = None
depends_on = None


def upgrade():
    # ===== ANATEL REPORTS =====
    op.create_table(
        "anatel_reports",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("report_type", sa.String(50), nullable=False),
        sa.Column("reference_period", sa.String(7), nullable=False),
        sa.Column("reference_year", sa.Integer(), nullable=False),
        sa.Column("reference_month", sa.Integer(), nullable=False),
        sa.Column("total_records", sa.Integer(), server_default="0", nullable=False),
        sa.Column("file_content", sa.Text(), nullable=True),
        sa.Column("stats_json", sa.String(2000), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )

    # Índices para performance
    op.create_index("idx_anatel_reports_type", "anatel_reports", ["report_type"])
    op.create_index("idx_anatel_reports_period", "anatel_reports", ["reference_year", "reference_month"])
    op.create_index("idx_anatel_reports_type_period", "anatel_reports", ["report_type", "reference_year", "reference_month"])


def downgrade():
    # Remover índices
    op.drop_index("idx_anatel_reports_type_period", "anatel_reports")
    op.drop_index("idx_anatel_reports_period", "anatel_reports")
    op.drop_index("idx_anatel_reports_type", "anatel_reports")

    # Remover tabela
    op.drop_table("anatel_reports")
