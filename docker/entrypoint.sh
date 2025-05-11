#!/bin/bash

# Set POSTGRES_HOST to 'db' if not explicitly set in environment variables
# 'db' is the service name in docker-compose.yml
: "${POSTGRES_HOST:=db}"

until PGPASSWORD=$POSTGRES_PASSWORD psql -h "$POSTGRES_HOST" -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c '\q'; do
  >&2 echo "Postgres is unavailable - sleeping"
  sleep 1
done

>&2 echo "Postgres is up - executing command"

python manage.py migrate
python manage.py collectstatic --noinput

# Check if environment variables are set properly
if [ -z "$DJANGO_SUPERUSER_EMAIL" ] || [ -z "$DJANGO_SUPERUSER_PASSWORD" ]; then
  echo "Warning: DJANGO_SUPERUSER_EMAIL or DJANGO_SUPERUSER_PASSWORD environment variables are not set. Skipping superuser creation."
else
  python manage.py shell -c "
from django.contrib.auth import get_user_model;
User = get_user_model();
if not User.objects.filter(email='$DJANGO_SUPERUSER_EMAIL').exists():
    # Use named parameters to ensure proper parameter passing
    User.objects.create_superuser(email='$DJANGO_SUPERUSER_EMAIL', password='$DJANGO_SUPERUSER_PASSWORD', name='Admin User')
    print('Superuser created successfully!')
else:
    print('Superuser already exists.')
"
fi

# exec daphne -b 0.0.0.0 -p 8000 TakeCare.asgi:application
exec python manage.py runserver 0.0.0.0:8000