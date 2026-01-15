"""Upgrade encryption for email and fiscal credentials

Revision ID: 0027_encryption_upgrade
Revises: 0026_soft_delete
Create Date: 2024-12-16 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0027_encryption_upgrade'
down_revision = '0026_soft_delete'
branch_labels = None
depends_on = None


def upgrade():
    """
    Aumenta tamanho do campo smtp_password para suportar criptografia Fernet.

    Fernet tokens são significativamente maiores que base64:
    - Base64: ~100 chars
    - Fernet: ~150-200 chars

    Também aumenta campos similares em outras tabelas.
    """
    # Email servers - smtp_password
    with op.batch_alter_table('email_servers', schema=None) as batch_op:
        batch_op.alter_column('smtp_password',
                              existing_type=sa.String(length=255),
                              type_=sa.String(length=500),
                              existing_nullable=False)

    # Se houver outras tabelas com credenciais criptografadas, adicionar aqui
    # Exemplo:
    # with op.batch_alter_table('payment_gateways', schema=None) as batch_op:
    #     batch_op.alter_column('api_secret',
    #                           existing_type=sa.String(length=255),
    #                           type_=sa.String(length=500),
    #                           existing_nullable=False)


def downgrade():
    """
    Reverte mudanças (cuidado: pode truncar dados se houver tokens Fernet longos)
    """
    with op.batch_alter_table('email_servers', schema=None) as batch_op:
        batch_op.alter_column('smtp_password',
                              existing_type=sa.String(length=500),
                              type_=sa.String(length=255),
                              existing_nullable=False)
