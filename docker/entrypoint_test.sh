

: "${POSTGRES_HOST:=db}"

until PGPASSWORD=$POSTGRES_PASSWORD psql -h "$POSTGRES_HOST" -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c '\q'; do
  >&2 echo "Postgres is unavailable - sleeping"
  sleep 1
done

>&2 echo "Postgres is up - executing tests"

: "${DJANGO_SETTINGS_MODULE:=TakeCare.settings_test}"
export DJANGO_SETTINGS_MODULE

echo "Using settings module: $DJANGO_SETTINGS_MODULE"

if python -c "import coverage" 2>/dev/null; then
    echo "Running tests with coverage..."
    python -m coverage run --source='.' manage.py test "$@"
    
    python -m coverage report
else
    echo "Coverage package not found. Running tests without coverage..."
    python manage.py test "$@"
fi

exit $?