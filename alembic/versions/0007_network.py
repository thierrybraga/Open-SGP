"""
Arquivo: alembic/versions/0007_network.py

Responsabilidade:
Cria tabelas de rede: dispositivos, VLANs, pools, perfis, atribuições e histórico.

Integrações:
- app.modules.network.models
"""

from alembic import op
import sqlalchemy as sa


revision = "0007_network"
down_revision = "0006_fiscal"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "network_devices",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(100), nullable=False, unique=True),
        sa.Column("type", sa.String(20), nullable=False),
        sa.Column("vendor", sa.String(20), nullable=False),
        sa.Column("host", sa.String(100), nullable=False),
        sa.Column("port", sa.Integer(), nullable=False, server_default="8728"),
        sa.Column("username", sa.String(100), nullable=False),
        sa.Column("password", sa.String(200), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )

    op.create_table(
        "vlans",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("device_id", sa.Integer(), sa.ForeignKey("network_devices.id", ondelete="CASCADE"), nullable=False),
        sa.Column("vlan_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("purpose", sa.String(50), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )

    op.create_table(
        "ip_pools",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(100), nullable=False, unique=True),
        sa.Column("cidr", sa.String(50), nullable=False),
        sa.Column("type", sa.String(20), nullable=False),
        sa.Column("gateway", sa.String(50), nullable=False),
        sa.Column("dns_primary", sa.String(50), nullable=False),
        sa.Column("dns_secondary", sa.String(50), nullable=False),
        sa.Column("device_id", sa.Integer(), sa.ForeignKey("network_devices.id", ondelete="SET NULL"), nullable=True),
        sa.Column("vlan_id", sa.Integer(), sa.ForeignKey("vlans.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )

    op.create_table(
        "service_profiles",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(100), nullable=False, unique=True),
        sa.Column("download_speed_mbps", sa.Float(), nullable=False, server_default="0"),
        sa.Column("upload_speed_mbps", sa.Float(), nullable=False, server_default="0"),
        sa.Column("burst_enabled", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("burst_rate_percent", sa.Float(), nullable=False, server_default="0"),
        sa.Column("burst_threshold_seconds", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )

    op.create_table(
        "contract_network_assignments",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("contract_id", sa.Integer(), sa.ForeignKey("contracts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("device_id", sa.Integer(), sa.ForeignKey("network_devices.id", ondelete="SET NULL"), nullable=True),
        sa.Column("ip_pool_id", sa.Integer(), sa.ForeignKey("ip_pools.id", ondelete="SET NULL"), nullable=True),
        sa.Column("vlan_id", sa.Integer(), sa.ForeignKey("vlans.id", ondelete="SET NULL"), nullable=True),
        sa.Column("profile_id", sa.Integer(), sa.ForeignKey("service_profiles.id", ondelete="SET NULL"), nullable=True),
        sa.Column("static_ip", sa.String(50), nullable=True),
        sa.Column("cgnat", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("status", sa.String(20), nullable=False, server_default="active"),
        sa.Column("last_provisioned_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_cna_contract", "contract_network_assignments", ["contract_id"]) 
    op.create_index("ix_cna_status", "contract_network_assignments", ["status"]) 

    op.create_table(
        "contract_tech_history",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("contract_id", sa.Integer(), sa.ForeignKey("contracts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("action", sa.String(50), nullable=False),
        sa.Column("details", sa.String(500), nullable=False),
        sa.Column("occurred_at", sa.DateTime(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )


def downgrade():
    op.drop_table("contract_tech_history")
    op.drop_index("ix_cna_status")
    op.drop_index("ix_cna_contract")
    op.drop_table("contract_network_assignments")
    op.drop_table("service_profiles")
    op.drop_table("ip_pools")
    op.drop_table("vlans")
    op.drop_table("network_devices")

