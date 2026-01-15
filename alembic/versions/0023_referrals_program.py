"""
Arquivo: alembic/versions/0023_referrals_program.py

Responsabilidade:
Cria tabelas de Programa de Indicações (Referrals).

Integrações:
- app.modules.referrals.models
"""

from alembic import op
import sqlalchemy as sa


revision = "0023_referrals_program"
down_revision = "0022_setup_operation_points_email"
branch_labels = None
depends_on = None


def upgrade():
    # ===== REFERRAL PROGRAMS =====
    op.create_table(
        "referral_programs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(150), nullable=False),
        sa.Column("description", sa.String(500), nullable=True),
        sa.Column("default_reward_type", sa.String(20), nullable=False, server_default="discount"),
        sa.Column("default_reward_value", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("reward_referred_client", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("referred_reward_value", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("min_active_months", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("max_referrals_per_client", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("valid_from", sa.String(30), nullable=True),
        sa.Column("valid_until", sa.String(30), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )

    # ===== REFERRALS =====
    op.create_table(
        "referrals",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("referrer_client_id", sa.Integer(), nullable=False),
        sa.Column("referred_client_id", sa.Integer(), nullable=False),
        sa.Column("referred_contract_id", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("converted_at", sa.String(30), nullable=True),
        sa.Column("referral_code", sa.String(50), nullable=True),
        sa.Column("notes", sa.String(500), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["referrer_client_id"], ["clients.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["referred_client_id"], ["clients.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["referred_contract_id"], ["contracts.id"], ondelete="SET NULL"),
    )
    op.create_index("idx_referrals_referrer", "referrals", ["referrer_client_id"])
    op.create_index("idx_referrals_referred", "referrals", ["referred_client_id"])
    op.create_index("idx_referrals_status", "referrals", ["status"])
    op.create_index("idx_referrals_code", "referrals", ["referral_code"])

    # ===== REFERRAL REWARDS =====
    op.create_table(
        "referral_rewards",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("referral_id", sa.Integer(), nullable=False),
        sa.Column("reward_type", sa.String(20), nullable=False),
        sa.Column("reward_value", sa.Float(), nullable=False),
        sa.Column("currency", sa.String(10), nullable=False, server_default="BRL"),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("paid_at", sa.String(30), nullable=True),
        sa.Column("payment_reference", sa.String(100), nullable=True),
        sa.Column("description", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["referral_id"], ["referrals.id"], ondelete="CASCADE"),
    )
    op.create_index("idx_referral_rewards_referral", "referral_rewards", ["referral_id"])
    op.create_index("idx_referral_rewards_status", "referral_rewards", ["status"])


def downgrade():
    # Remover referral rewards
    op.drop_index("idx_referral_rewards_status", "referral_rewards")
    op.drop_index("idx_referral_rewards_referral", "referral_rewards")
    op.drop_table("referral_rewards")

    # Remover referrals
    op.drop_index("idx_referrals_code", "referrals")
    op.drop_index("idx_referrals_status", "referrals")
    op.drop_index("idx_referrals_referred", "referrals")
    op.drop_index("idx_referrals_referrer", "referrals")
    op.drop_table("referrals")

    # Remover programs
    op.drop_table("referral_programs")
