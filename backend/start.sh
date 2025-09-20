#!/bin/bash

echo "🚀 Starting Django Backend..."

# Activate the virtual environment first
source /app/.venv/bin/activate

# Change to backend directory
cd /app/backend

# Run migrations
echo "Running migrations..."
python manage.py migrate --noinput

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput

# Start server
echo "Starting server..."
exec gunicorn core.wsgi:application --bind 0.0.0.0:${PORT:-8000} --workers 4