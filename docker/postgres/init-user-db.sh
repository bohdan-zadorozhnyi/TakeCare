#!/bin/bash
set -e

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    ALTER SYSTEM SET listen_addresses TO '*';
    ALTER SYSTEM SET password_encryption TO 'md5';
EOSQL

# Modify pg_hba.conf to allow connections from Docker network
echo "host all all all trust" >> /var/lib/postgresql/data/pg_hba.conf