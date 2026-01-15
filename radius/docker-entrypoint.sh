#!/bin/sh
set -e

# Render SQL module config with env variables
DB_HOST=${DB_HOST:-db}
DB_PORT=${DB_PORT:-5432}
DB_USER=${DB_USER:-root}
DB_PASS=${DB_PASS:-root}
DB_NAME=${DB_NAME:-isp_erp}

sed -i "s/@DB_HOST@/${DB_HOST}/g" /etc/raddb/mods-available/sql
sed -i "s/@DB_PORT@/${DB_PORT}/g" /etc/raddb/mods-available/sql
sed -i "s/@DB_USER@/${DB_USER}/g" /etc/raddb/mods-available/sql
sed -i "s/@DB_PASS@/${DB_PASS}/g" /etc/raddb/mods-available/sql
sed -i "s/@DB_NAME@/${DB_NAME}/g" /etc/raddb/mods-available/sql

# Start FreeRADIUS in foreground (binary name is 'freeradius' in this image)
exec freeradius -f
