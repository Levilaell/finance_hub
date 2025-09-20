#!/bin/bash

echo "🚀 Starting CaixaHub Backend..."

# Set environment variables
export DJANGO_SETTINGS_MODULE=${DJANGO_SETTINGS_MODULE:-core.settings.production}

# Wait for database to be ready
echo "⏳ Waiting for database..."
python -c "
import time
import django
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.production')
django.setup()

for i in range(30):
    try:
        from django.db import connection
        cursor = connection.cursor()
        cursor.execute('SELECT 1')
        print('✅ Database is ready!')
        break
    except Exception as e:
        if i == 29:
            print('⚠️ Database not ready after 30 seconds, continuing anyway...')
        time.sleep(1)
"

# Run migrations
echo "🔧 Running migrations..."
python manage.py migrate --noinput

# Collect static files
echo "📦 Collecting static files..."
python manage.py collectstatic --noinput

# Start the server
echo "✅ Starting server..."
exec gunicorn core.wsgi:application \
    --bind 0.0.0.0:${PORT:-8000} \
    --workers ${WEB_CONCURRENCY:-4} \
    --timeout 120 \
    --access-logfile - \
    --error-logfile - \
    --log-level info \
    --preload