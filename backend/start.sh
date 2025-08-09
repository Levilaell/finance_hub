#!/bin/bash
# Startup script for production deployment

echo "🚀 Starting Finance Hub Backend..."

# Ensure database is properly initialized
echo "📊 Checking database..."
python manage.py ensure_database

# Run migrations
echo "🔄 Running migrations..."
python manage.py migrate --no-input

# Collect static files
echo "📦 Collecting static files..."
python manage.py collectstatic --no-input

# Start the server
echo "✅ Starting server..."
exec gunicorn core.wsgi:application \
    --bind 0.0.0.0:${PORT:-8000} \
    --workers ${WEB_CONCURRENCY:-4} \
    --timeout 120 \
    --access-logfile - \
    --error-logfile - \
    --log-level info