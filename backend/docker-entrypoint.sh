#!/bin/sh
set -e

# Use PORT environment variable, default to 8000 if not set
export PORT=${PORT:-8000}

# Ensure we're using production settings
export DJANGO_ENV=${DJANGO_ENV:-production}
export DJANGO_SETTINGS_MODULE=${DJANGO_SETTINGS_MODULE:-core.settings.production}

echo "Starting Django server on port $PORT"
echo "Using settings: $DJANGO_SETTINGS_MODULE"

# Check for critical environment variables
if [ -z "$DJANGO_SECRET_KEY" ]; then
    echo "WARNING: DJANGO_SECRET_KEY is not set!"
    echo "Please set it in Railway dashboard > Variables"
    echo "The app will start with a temporary key but this is INSECURE!"
fi

if [ -z "$DATABASE_URL" ]; then
    echo "WARNING: DATABASE_URL is not set!"
    echo "Railway should provide this automatically."
    echo "Check your database service configuration."
fi

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