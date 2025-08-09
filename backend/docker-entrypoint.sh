#!/bin/sh
set -e

# Use PORT environment variable, default to 8000 if not set
export PORT=${PORT:-8000}

echo "Starting Django server on port $PORT"

# Run migrations in correct order to handle dependencies
echo "Running migrations..."

# First, migrate the core Django apps
python manage.py migrate contenttypes --noinput || true
python manage.py migrate auth --noinput || true

# Then our custom user model
python manage.py migrate authentication --noinput || true

# Then companies (depends on authentication)
python manage.py migrate companies --noinput || true

# Then all other apps
python manage.py migrate --noinput || true

echo "Migrations completed"

# Collect static files
python manage.py collectstatic --noinput

# Start gunicorn
exec gunicorn core.wsgi:application --bind 0.0.0.0:$PORT --workers 4 --timeout 120 --log-level info