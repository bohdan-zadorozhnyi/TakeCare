-- Allow connections from all addresses in the Docker network
CREATE USER postgres WITH PASSWORD '12345' SUPERUSER;
ALTER SYSTEM SET listen_addresses TO '*';

-- Add entry to pg_hba.conf through SQL
ALTER SYSTEM SET hba_file TO '/var/lib/postgresql/data/pg_hba.conf';
\connect template1
CREATE EXTENSION IF NOT EXISTS adminpack;