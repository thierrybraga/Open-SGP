"""Consolidate ORM schema drift.

Revision ID: 0033_schema_consolidation
Revises: 0032_support_schema
Create Date: 2026-06-04
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "0033_schema_consolidation"
down_revision = "0032_support_schema"
branch_labels = None
depends_on = None


def _inspector():
    return sa.inspect(op.get_bind())


def _tables() -> set[str]:
    return set(_inspector().get_table_names())


def _columns(table_name: str) -> set[str]:
    if table_name not in _tables():
        return set()
    return {col["name"] for col in _inspector().get_columns(table_name)}


def _indexes(table_name: str) -> set[str]:
    if table_name not in _tables():
        return set()
    return {idx["name"] for idx in _inspector().get_indexes(table_name)}


def _foreign_keys(table_name: str) -> set[str]:
    if table_name not in _tables():
        return set()
    return {fk["name"] for fk in _inspector().get_foreign_keys(table_name)}


def _unique_constraints(table_name: str) -> set[str]:
    if table_name not in _tables():
        return set()
    return {constraint["name"] for constraint in _inspector().get_unique_constraints(table_name)}


def _add_column_if_missing(table_name: str, column: sa.Column) -> None:
    if table_name in _tables() and column.name not in _columns(table_name):
        op.add_column(table_name, column)


def _create_index_if_missing(index_name: str, table_name: str, columns: list[str], unique: bool = False) -> None:
    if table_name in _tables() and index_name not in _indexes(table_name):
        op.create_index(index_name, table_name, columns, unique=unique)


def _create_fk_if_missing(
    constraint_name: str,
    source_table: str,
    referent_table: str,
    local_cols: list[str],
    remote_cols: list[str],
    ondelete: str | None = None,
) -> None:
    if source_table in _tables() and constraint_name not in _foreign_keys(source_table):
        op.create_foreign_key(constraint_name, source_table, referent_table, local_cols, remote_cols, ondelete=ondelete)


def _create_unique_if_missing(constraint_name: str, table_name: str, columns: list[str]) -> None:
    if table_name in _tables() and constraint_name not in _unique_constraints(table_name):
        op.create_unique_constraint(constraint_name, table_name, columns)


def _create_backup_tables() -> None:
    if "backup_jobs" not in _tables():
        op.create_table(
            "backup_jobs",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("name", sa.String(120), nullable=False),
            sa.Column("type", sa.String(20), nullable=False),
            sa.Column("schedule_cron", sa.String(100), nullable=True),
            sa.Column("storage_dir", sa.String(255), nullable=False),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
            sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("deleted_by", sa.Integer(), nullable=True),
        )
        op.create_index("ix_backup_jobs_name", "backup_jobs", ["name"], unique=True)

    if "backup_executions" not in _tables():
        op.create_table(
            "backup_executions",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("job_id", sa.Integer(), sa.ForeignKey("backup_jobs.id", ondelete="CASCADE"), nullable=False),
            sa.Column("started_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.Column("finished_at", sa.DateTime(), nullable=True),
            sa.Column("status", sa.String(20), nullable=False, server_default="running"),
            sa.Column("file_path", sa.String(255), nullable=True),
            sa.Column("error", sa.String(500), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("deleted_by", sa.Integer(), nullable=True),
        )
        op.create_index("ix_backup_executions_job_id", "backup_executions", ["job_id"])
        op.create_index("ix_backup_exec_status", "backup_executions", ["status"])


def _create_network_tables() -> None:
    if "ip_leases" not in _tables():
        op.create_table(
            "ip_leases",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("pool_id", sa.Integer(), sa.ForeignKey("ip_pools.id", ondelete="CASCADE"), nullable=False),
            sa.Column("contract_id", sa.Integer(), sa.ForeignKey("contracts.id", ondelete="SET NULL"), nullable=True),
            sa.Column("ip_address", sa.String(50), nullable=False),
            sa.Column("allocated_at", sa.DateTime(), nullable=True),
            sa.Column("released_at", sa.DateTime(), nullable=True),
            sa.Column("status", sa.String(20), nullable=False, server_default="allocated"),
            sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("deleted_by", sa.Integer(), nullable=True),
        )
        op.create_index("ix_ip_leases_pool_id", "ip_leases", ["pool_id"])
        op.create_index("ix_ip_leases_contract_id", "ip_leases", ["contract_id"])
        op.create_index("ix_ip_leases_ip_address", "ip_leases", ["ip_address"])
        op.create_index("ix_ip_leases_status", "ip_leases", ["status"])

    radius_tables = {
        "radcheck": [sa.Column("username", sa.String(64), nullable=False), sa.Column("attribute", sa.String(64), nullable=False), sa.Column("op", sa.String(2), nullable=False, server_default=":="), sa.Column("value", sa.String(253), nullable=False)],
        "radreply": [sa.Column("username", sa.String(64), nullable=False), sa.Column("attribute", sa.String(64), nullable=False), sa.Column("op", sa.String(2), nullable=False, server_default="="), sa.Column("value", sa.String(253), nullable=False)],
        "radusergroup": [sa.Column("username", sa.String(64), nullable=False), sa.Column("groupname", sa.String(64), nullable=False), sa.Column("priority", sa.Integer(), nullable=False, server_default="1")],
        "radgroupreply": [sa.Column("groupname", sa.String(64), nullable=False), sa.Column("attribute", sa.String(64), nullable=False), sa.Column("op", sa.String(2), nullable=False, server_default="="), sa.Column("value", sa.String(253), nullable=False)],
        "radgroupcheck": [sa.Column("groupname", sa.String(64), nullable=False), sa.Column("attribute", sa.String(64), nullable=False), sa.Column("op", sa.String(2), nullable=False, server_default=":="), sa.Column("value", sa.String(253), nullable=False)],
    }
    for table_name, columns in radius_tables.items():
        if table_name not in _tables():
            op.create_table(table_name, sa.Column("id", sa.Integer(), primary_key=True), *columns)
        first_index_col = "username" if table_name in {"radcheck", "radreply", "radusergroup"} else "groupname"
        _create_index_if_missing(f"ix_{table_name}_{first_index_col}", table_name, [first_index_col])
        if table_name == "radusergroup":
            _create_index_if_missing("ix_radusergroup_groupname", "radusergroup", ["groupname"])

    if "radacct" not in _tables():
        op.create_table(
            "radacct",
            sa.Column("radacctid", sa.Integer(), primary_key=True),
            sa.Column("acctsessionid", sa.String(64), nullable=False),
            sa.Column("acctuniqueid", sa.String(32), nullable=False, unique=True),
            sa.Column("username", sa.String(64), nullable=False),
            sa.Column("groupname", sa.String(64), nullable=True),
            sa.Column("realm", sa.String(64), nullable=True),
            sa.Column("nasipaddress", sa.String(15), nullable=False),
            sa.Column("nasportid", sa.String(15), nullable=True),
            sa.Column("nasporttype", sa.String(32), nullable=True),
            sa.Column("acctstarttime", sa.DateTime(), nullable=True),
            sa.Column("acctupdatetime", sa.DateTime(), nullable=True),
            sa.Column("acctstoptime", sa.DateTime(), nullable=True),
            sa.Column("acctinterval", sa.Integer(), nullable=True),
            sa.Column("acctsessiontime", sa.Integer(), nullable=True),
            sa.Column("acctauthentic", sa.String(32), nullable=True),
            sa.Column("connectinfo_start", sa.String(50), nullable=True),
            sa.Column("connectinfo_stop", sa.String(50), nullable=True),
            sa.Column("acctinputoctets", sa.Integer(), nullable=True),
            sa.Column("acctoutputoctets", sa.Integer(), nullable=True),
            sa.Column("calledstationid", sa.String(50), nullable=True),
            sa.Column("callingstationid", sa.String(50), nullable=True),
            sa.Column("acctterminatecause", sa.String(32), nullable=True),
            sa.Column("servicetype", sa.String(32), nullable=True),
            sa.Column("framedprotocol", sa.String(32), nullable=True),
            sa.Column("framedipaddress", sa.String(15), nullable=True),
        )
        for column in ["acctsessionid", "username", "nasipaddress", "acctstarttime", "acctstoptime"]:
            op.create_index(f"ix_radacct_{column}", "radacct", [column])

    if "radippool" not in _tables():
        op.create_table(
            "radippool",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("pool_name", sa.String(30), nullable=False),
            sa.Column("framedipaddress", sa.String(15), nullable=False),
            sa.Column("nasipaddress", sa.String(15), nullable=False, server_default=""),
            sa.Column("calledstationid", sa.String(30), nullable=False, server_default=""),
            sa.Column("callingstationid", sa.String(30), nullable=False, server_default=""),
            sa.Column("expiry_time", sa.DateTime(), nullable=True),
            sa.Column("username", sa.String(64), nullable=False, server_default=""),
            sa.Column("pool_key", sa.String(30), nullable=False, server_default=""),
        )
        op.create_index("ix_radippool_pool_name", "radippool", ["pool_name"])
        op.create_index("ix_radippool_framedipaddress", "radippool", ["framedipaddress"])


def _create_audit_and_notification_tables() -> None:
    if "audit_logs" not in _tables():
        op.create_table(
            "audit_logs",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("user_id", sa.Integer(), nullable=True),
            sa.Column("username", sa.String(100), nullable=True),
            sa.Column("action", sa.String(50), nullable=False),
            sa.Column("entity_type", sa.String(100), nullable=False),
            sa.Column("entity_id", sa.Integer(), nullable=True),
            sa.Column("old_values", sa.JSON(), nullable=True),
            sa.Column("new_values", sa.JSON(), nullable=True),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("ip_address", sa.String(45), nullable=True),
            sa.Column("user_agent", sa.String(500), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        )
        for column in ["id", "user_id", "username", "action", "entity_type", "entity_id"]:
            op.create_index(f"ix_audit_logs_{column}", "audit_logs", [column])

    if "notifications" not in _tables():
        op.create_table(
            "notifications",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
            sa.Column("title", sa.String(255), nullable=False),
            sa.Column("message", sa.Text(), nullable=False),
            sa.Column("type", sa.String(50), nullable=False, server_default="info"),
            sa.Column("read", sa.Boolean(), nullable=False, server_default=sa.text("false")),
            sa.Column("link", sa.String(500), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("deleted_by", sa.Integer(), nullable=True),
        )
        op.create_index("ix_notifications_user_id", "notifications", ["user_id"])


def _align_existing_tables() -> None:
    _add_column_if_missing("network_devices", sa.Column("zabbix_monitored", sa.Boolean(), nullable=False, server_default=sa.text("false")))
    _add_column_if_missing("network_devices", sa.Column("zabbix_host_id", sa.String(20), nullable=True))

    _add_column_if_missing("anatel_reports", sa.Column("file_path", sa.String(500), nullable=True))
    _add_column_if_missing("anatel_reports", sa.Column("generated_by_user_id", sa.Integer(), nullable=True))
    _add_column_if_missing("anatel_reports", sa.Column("generation_status", sa.String(20), nullable=False, server_default="completed"))
    _add_column_if_missing("anatel_reports", sa.Column("error_message", sa.String(1000), nullable=True))

    _add_column_if_missing("contract_tech_history", sa.Column("technician", sa.String(100), nullable=True))
    _add_column_if_missing("contract_tech_history", sa.Column("description", sa.String(500), nullable=True))
    if "contract_tech_history" in _tables() and {"details", "description"}.issubset(_columns("contract_tech_history")):
        op.execute("UPDATE contract_tech_history SET description = details WHERE description IS NULL")

    _create_fk_if_missing(
        "fk_technician_profiles_user",
        "technician_profiles",
        "users",
        ["user_id"],
        ["id"],
        ondelete="CASCADE",
    )

    for table_name in _tables():
        if table_name == "alembic_version":
            continue
        columns = _columns(table_name)
        if {"created_at", "updated_at"}.issubset(columns):
            if "deleted_at" not in columns:
                op.add_column(table_name, sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True))
            if "deleted_by" not in columns:
                op.add_column(table_name, sa.Column("deleted_by", sa.Integer(), nullable=True))
            _create_index_if_missing(f"ix_{table_name}_deleted_at", table_name, ["deleted_at"])


def upgrade() -> None:
    _create_backup_tables()
    _create_network_tables()
    _create_audit_and_notification_tables()
    _align_existing_tables()


def downgrade() -> None:
    # This migration intentionally avoids dropping columns from existing business
    # tables on downgrade. Removing tables created here is safe because older
    # revisions did not know about them.
    for table_name in [
        "notifications",
        "audit_logs",
        "radippool",
        "radacct",
        "radgroupcheck",
        "radgroupreply",
        "radusergroup",
        "radreply",
        "radcheck",
        "ip_leases",
        "backup_executions",
        "backup_jobs",
    ]:
        if table_name in _tables():
            op.drop_table(table_name)
