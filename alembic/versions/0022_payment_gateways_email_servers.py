"""
Arquivo: alembic/versions/0022_payment_gateways_email_servers.py

Responsabilidade:
Cria tabelas de Payment Gateways e Email Servers.

Integrações:
- app.modules.administration.payment_gateways.models
- app.modules.administration.email_servers.models
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSON


revision = "0022_payment_gateways_email_servers"
down_revision = "0021_client_pre_registration"
branch_labels = None
depends_on = None


def upgrade():
    # ===== PAYMENT GATEWAYS =====
    op.create_table(
        "payment_gateways",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(150), nullable=False),
        sa.Column("provider", sa.String(50), nullable=False),
        sa.Column("payment_type", sa.String(50), nullable=False),
        sa.Column("credentials", JSON, nullable=False),
        sa.Column("settings", JSON, nullable=True),
        sa.Column("environment", sa.String(20), nullable=False, server_default="sandbox"),
        sa.Column("webhook_url", sa.String(500), nullable=True),
        sa.Column("webhook_secret", sa.String(255), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("is_default", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index("idx_payment_gateways_provider", "payment_gateways", ["provider"])
    op.create_index("idx_payment_gateways_type", "payment_gateways", ["payment_type"])
    op.create_index("idx_payment_gateways_active", "payment_gateways", ["is_active"])

    # ===== EMAIL SERVERS =====
    op.create_table(
        "email_servers",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(150), nullable=False),
        sa.Column("description", sa.String(500), nullable=True),
        sa.Column("smtp_host", sa.String(255), nullable=False),
        sa.Column("smtp_port", sa.Integer(), nullable=False, server_default="587"),
        sa.Column("smtp_username", sa.String(255), nullable=False),
        sa.Column("smtp_password", sa.String(255), nullable=False),
        sa.Column("use_tls", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("use_ssl", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("from_email", sa.String(255), nullable=False),
        sa.Column("from_name", sa.String(150), nullable=True),
        sa.Column("max_emails_per_hour", sa.Integer(), nullable=True),
        sa.Column("max_emails_per_day", sa.Integer(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("is_default", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("emails_sent_today", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("emails_sent_this_hour", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_used_at", sa.String(30), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index("idx_email_servers_active", "email_servers", ["is_active"])

    # ===== EMPLOYEES =====
    op.create_table(
        "employees",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("full_name", sa.String(200), nullable=False),
        sa.Column("document", sa.String(20), nullable=False, unique=True),
        sa.Column("rg", sa.String(20), nullable=True),
        sa.Column("birth_date", sa.Date(), nullable=True),
        sa.Column("email", sa.String(255), nullable=True),
        sa.Column("phone", sa.String(20), nullable=True),
        sa.Column("mobile", sa.String(20), nullable=True),
        sa.Column("address", sa.String(255), nullable=True),
        sa.Column("city", sa.String(100), nullable=True),
        sa.Column("state", sa.String(2), nullable=True),
        sa.Column("postal_code", sa.String(10), nullable=True),
        sa.Column("position", sa.String(100), nullable=True),
        sa.Column("department", sa.String(100), nullable=True),
        sa.Column("admission_date", sa.Date(), nullable=True),
        sa.Column("termination_date", sa.Date(), nullable=True),
        sa.Column("salary", sa.Float(), nullable=True),
        sa.Column("payment_type", sa.String(20), nullable=True),
        sa.Column("bank_code", sa.String(10), nullable=True),
        sa.Column("bank_agency", sa.String(20), nullable=True),
        sa.Column("bank_account", sa.String(30), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="active"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("notes", sa.String(1000), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index("idx_employees_document", "employees", ["document"])
    op.create_index("idx_employees_email", "employees", ["email"])
    op.create_index("idx_employees_status", "employees", ["status"])


def downgrade():
    # Remover employees
    op.drop_index("idx_employees_status", "employees")
    op.drop_index("idx_employees_email", "employees")
    op.drop_index("idx_employees_document", "employees")
    op.drop_table("employees")
    # Remover email servers
    op.drop_index("idx_email_servers_active", "email_servers")
    op.drop_table("email_servers")

    # Remover payment gateways
    op.drop_index("idx_payment_gateways_active", "payment_gateways")
    op.drop_index("idx_payment_gateways_type", "payment_gateways")
    op.drop_index("idx_payment_gateways_provider", "payment_gateways")
    op.drop_table("payment_gateways")
