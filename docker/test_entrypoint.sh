#!/bin/bash
set -e

# Explicitly ensure that POSTGRES_HOST is set to 'db' for Docker networking
export POSTGRES_HOST=db

echo "Waiting for PostgreSQL..."
while ! pg_isready -h $POSTGRES_HOST -p $POSTGRES_PORT -U $POSTGRES_USER; do
    sleep 1
done
echo "PostgreSQL is ready."

# Create a migration-ready database first
echo "Creating a migration-ready database..."
psql -h $POSTGRES_HOST -U $POSTGRES_USER -c "DROP DATABASE IF EXISTS migrate_db;"
psql -h $POSTGRES_HOST -U $POSTGRES_USER -c "CREATE DATABASE migrate_db OWNER ${POSTGRES_USER};"

# Set DJANGO_SETTINGS_MODULE to use the migration database
export DJANGO_DB_NAME=migrate_db

# Apply all migrations to the migration database to get a proper schema
echo "Applying all migrations to migration database..."
POSTGRES_DB=migrate_db python manage.py migrate --noinput

# Create a superuser for tests if environment variables are set
if [[ -n "$DJANGO_SUPERUSER_EMAIL" && -n "$DJANGO_SUPERUSER_PASSWORD" ]]; then
    echo "Creating superuser for testing..."
    POSTGRES_DB=migrate_db python manage.py shell -c "
from django.contrib.auth import get_user_model;
User = get_user_model();
if not User.objects.filter(email='$DJANGO_SUPERUSER_EMAIL').exists():
    User.objects.create_superuser('$DJANGO_SUPERUSER_EMAIL', '$DJANGO_SUPERUSER_PASSWORD')
"
fi

# Now create a test database based on the schema of the properly migrated database
echo "Creating test database from migration database schema..."
psql -h $POSTGRES_HOST -U $POSTGRES_USER -c "DROP DATABASE IF EXISTS test_${POSTGRES_DB};"
psql -h $POSTGRES_HOST -U $POSTGRES_USER -c "CREATE DATABASE test_${POSTGRES_DB} WITH TEMPLATE migrate_db OWNER ${POSTGRES_USER};"

# Reset DB name for tests
export DJANGO_DB_NAME=$POSTGRES_DB

echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Running calendar_app tests..."
python manage.py test calendar_app