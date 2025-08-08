#!/bin/sh
set -e

# Use PORT environment variable, default to 8000 if not set
export PORT=${PORT:-8000}

echo "Starting Django server on port $PORT"

# Run migrations
python manage.py migrate

# Collect static files
python manage.py collectstatic --noinput

# Start gunicorn
exec gunicorn core.wsgi:application --bind 0.0.0.0:$PORT --workers 4 --timeout 120 --log-level info