"""
Arquivo: alembic/versions/0017_comm_retries.py

Responsabilidade:
Adiciona colunas de tentativas e próximo agendamento à comm_message_queue.

Integrações:
- app.modules.communication.models
"""

from alembic import op
import sqlalchemy as sa


revision = "0017_comm_retries"
down_revision = "0016_fk_constraints"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("comm_message_queue", sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("comm_message_queue", sa.Column("next_attempt_at", sa.DateTime(), nullable=True))


def downgrade():
    op.drop_column("comm_message_queue", "next_attempt_at")
    op.drop_column("comm_message_queue", "attempts")

