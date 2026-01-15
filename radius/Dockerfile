FROM freeradius/freeradius-server:latest

# Install PostgreSQL support
USER root
RUN apt-get update && apt-get install -y freeradius-postgresql && rm -rf /var/lib/apt/lists/*

# Enable SQL module
RUN ln -s /etc/raddb/mods-available/sql /etc/raddb/mods-enabled/sql

# Enable SQL IP Pool module
RUN ln -s /etc/raddb/mods-available/sqlippool /etc/raddb/mods-enabled/sqlippool

# Copy SQL configurations
COPY sql /etc/raddb/mods-available/sql
COPY queries.conf /etc/raddb/mods-config/sql/main/postgresql/queries.conf

# Copy SQL IP Pool configurations
COPY sqlippool.conf /etc/raddb/mods-available/sqlippool
COPY ippool_queries.conf /etc/raddb/mods-config/sql/main/postgresql/ippool_queries.conf

# Copy Site Configuration
COPY default /etc/raddb/sites-available/default

# Performance Tuning in radiusd.conf
# Increase max_servers for concurrency and request queue size
RUN sed -i 's/max_servers = 32/max_servers = 64/g' /etc/raddb/radiusd.conf && \
    sed -i 's/max_requests = 1024/max_requests = 16384/g' /etc/raddb/radiusd.conf

# Fix permissions
RUN chown -R freerad:freerad /etc/raddb

# Entrypoint to template configs from env
COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh
USER freerad
ENTRYPOINT ["/bin/sh", "/docker-entrypoint.sh"]


# Expose ports:
# 1812: Authentication
# 1813: Accounting
# 3799: CoA (Change of Authorization) - For Disconnect Requests
EXPOSE 1812/udp 1813/udp 3799/udp
