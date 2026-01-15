"""
Arquivo: alembic/versions/0022_setup_operation_points_email.py

Responsabilidade:
Cria tabelas de Setup Progress, Operation Points e Email Configuration.

Integrações:
- app.modules.administration.setup.models
- app.modules.administration.operation_points.models
- app.modules.administration.email_config.models
"""

from alembic import op
import sqlalchemy as sa


revision = "0022_setup_operation_points_email"
down_revision = "0021_client_pre_registration"
branch_labels = None
depends_on = None


def upgrade():
    # ===== SETUP PROGRESS =====
    op.create_table(
        "setup_progress",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("is_completed", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("current_step", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("company_configured", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("financial_configured", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("network_configured", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("plans_configured", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("contract_template_configured", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("email_configured", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("first_user_created", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("config_data", sa.Text(), nullable=True),
        sa.Column("notes", sa.String(500), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )

    # ===== OPERATION POINTS =====
    op.create_table(
        "operation_points",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(150), nullable=False),
        sa.Column("code", sa.String(20), nullable=False, unique=True),
        sa.Column("description", sa.String(500), nullable=True),
        sa.Column("point_type", sa.String(50), nullable=False),
        sa.Column("address", sa.String(255), nullable=False),
        sa.Column("city", sa.String(100), nullable=False),
        sa.Column("state", sa.String(2), nullable=False),
        sa.Column("postal_code", sa.String(10), nullable=True),
        sa.Column("neighborhood", sa.String(100), nullable=True),
        sa.Column("latitude", sa.Float(), nullable=True),
        sa.Column("longitude", sa.Float(), nullable=True),
        sa.Column("phone", sa.String(20), nullable=True),
        sa.Column("email", sa.String(120), nullable=True),
        sa.Column("opening_time", sa.String(5), nullable=True),
        sa.Column("closing_time", sa.String(5), nullable=True),
        sa.Column("working_days", sa.String(50), nullable=True),
        sa.Column("manager_name", sa.String(150), nullable=True),
        sa.Column("manager_phone", sa.String(20), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("notes", sa.String(500), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index("idx_operation_points_name", "operation_points", ["name"])
    op.create_index("idx_operation_points_code", "operation_points", ["code"])

    # ===== EMAIL CONFIGURATIONS =====
    op.create_table(
        "email_configurations",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(150), nullable=False),
        sa.Column("description", sa.String(500), nullable=True),
        sa.Column("smtp_host", sa.String(255), nullable=False),
        sa.Column("smtp_port", sa.Integer(), nullable=False, server_default="587"),
        sa.Column("smtp_user", sa.String(255), nullable=False),
        sa.Column("smtp_password", sa.String(255), nullable=False),
        sa.Column("use_tls", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("use_ssl", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("from_email", sa.String(255), nullable=False),
        sa.Column("from_name", sa.String(150), nullable=False),
        sa.Column("reply_to_email", sa.String(255), nullable=True),
        sa.Column("max_emails_per_hour", sa.Integer(), nullable=True),
        sa.Column("max_emails_per_day", sa.Integer(), nullable=True),
        sa.Column("timeout", sa.Integer(), nullable=False, server_default="30"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("is_default", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("last_test_at", sa.String(30), nullable=True),
        sa.Column("last_test_success", sa.Boolean(), nullable=True),
        sa.Column("last_test_error", sa.String(500), nullable=True),
        sa.Column("company_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="CASCADE"),
    )
    op.create_index("idx_email_configurations_active", "email_configurations", ["is_active"])
    op.create_index("idx_email_configurations_default", "email_configurations", ["is_default"])


def downgrade():
    # Remover email configurations
    op.drop_index("idx_email_configurations_default", "email_configurations")
    op.drop_index("idx_email_configurations_active", "email_configurations")
    op.drop_table("email_configurations")

    # Remover operation points
    op.drop_index("idx_operation_points_code", "operation_points")
    op.drop_index("idx_operation_points_name", "operation_points")
    op.drop_table("operation_points")

    # Remover setup progress
    op.drop_table("setup_progress")
