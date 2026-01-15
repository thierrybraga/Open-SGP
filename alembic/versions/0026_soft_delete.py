"""Add soft delete to all models

Revision ID: 0026_soft_delete
Revises: 0025_anatel_reports
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import func


# revision identifiers, used by Alembic.
revision = '0026_soft_delete'
down_revision = '0025_anatel_reports'
branch_labels = None
depends_on = None


# Lista de todas as tabelas que precisam de soft delete
TABLES = [
    'users', 'roles', 'permissions', 'role_permissions', 'user_roles',
    'clients', 'client_contacts', 'addresses',
    'plans', 'contracts', 'contract_network_assignments',
    'titles', 'payments', 'title_adjustments', 'payment_promises',
    'invoices', 'invoice_items',
    'network_devices', 'vlans', 'ip_pools', 'nas',
    'tickets', 'ticket_messages', 'service_orders', 'occurrences',
    'warehouses', 'stock_items', 'stock_movements', 'comodatos', 'purchases', 'suppliers',
    'message_queue', 'message_templates',
    'pops', 'backups', 'carriers', 'financial_parameters',
    'employees', 'email_servers', 'payment_gateways',
    'viabilities', 'discounts', 'cashier_transactions', 'referrals', 'referral_rewards'
]


def upgrade():
    """Add deleted_at and deleted_by columns to all tables"""
    for table in TABLES:
        try:
            op.add_column(table, sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True))
            op.add_column(table, sa.Column('deleted_by', sa.Integer(), nullable=True))
            op.create_index(f'ix_{table}_deleted_at', table, ['deleted_at'])
        except Exception as e:
            print(f"Warning: Could not add soft delete to {table}: {e}")


def downgrade():
    """Remove deleted_at and deleted_by columns"""
    for table in TABLES:
        try:
            op.drop_index(f'ix_{table}_deleted_at', table_name=table)
            op.drop_column(table, 'deleted_by')
            op.drop_column(table, 'deleted_at')
        except Exception as e:
            print(f"Warning: Could not remove soft delete from {table}: {e}")
