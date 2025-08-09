#!/bin/bash
# Startup script for production deployment

echo "🚀 Starting Finance Hub Backend..."

# Set default environment variables if not set
export DJANGO_SETTINGS_MODULE=${DJANGO_SETTINGS_MODULE:-core.settings.production}

# If ALLOWED_HOSTS is not set, try to auto-detect from Railway
if [ -z "$ALLOWED_HOSTS" ]; then
    if [ -n "$RAILWAY_PUBLIC_DOMAIN" ]; then
        export ALLOWED_HOSTS="$RAILWAY_PUBLIC_DOMAIN,*.railway.app,localhost,127.0.0.1"
        echo "📝 Auto-configured ALLOWED_HOSTS: $ALLOWED_HOSTS"
    else
        # Fallback to permissive for Railway deployment
        export ALLOWED_HOSTS="*"
        echo "⚠️  Warning: Using permissive ALLOWED_HOSTS"
    fi
fi

# Wait for database to be ready (max 30 seconds)
echo "⏳ Waiting for database..."
for i in {1..30}; do
    if python -c "import django; django.setup(); from django.db import connection; connection.cursor().execute('SELECT 1')" 2>/dev/null; then
        echo "✅ Database is ready!"
        break
    fi
    if [ $i -eq 30 ]; then
        echo "⚠️  Database not ready after 30 seconds, continuing anyway..."
    fi
    sleep 1
done

# Run migrations
echo "🔄 Running migrations..."
python manage.py migrate --no-input || {
    echo "⚠️  Some migrations failed, but continuing..."
}

# Collect static files
echo "📦 Collecting static files..."
python manage.py collectstatic --no-input || echo "⚠️  Static files collection had issues"

# Create default superuser if it doesn't exist
echo "👤 Checking for superuser..."
python -c "
import os
import django
django.setup()
from django.contrib.auth import get_user_model
User = get_user_model()
try:
    if not User.objects.filter(is_superuser=True).exists():
        email = os.environ.get('DJANGO_SUPERUSER_EMAIL', 'admin@finance-hub.com')
        password = os.environ.get('DJANGO_SUPERUSER_PASSWORD', 'admin123')
        if email and password:
            User.objects.create_superuser(username='admin', email=email, password=password)
            print(f'✅ Created superuser: {email}')
        else:
            print('ℹ️  No superuser created (set DJANGO_SUPERUSER_EMAIL and DJANGO_SUPERUSER_PASSWORD to create one)')
    else:
        print('✅ Superuser already exists')
except Exception as e:
    print(f'⚠️  Could not check/create superuser: {e}')
"

# Log configuration for debugging
echo "📋 Configuration:"
echo "  - DJANGO_SETTINGS_MODULE: $DJANGO_SETTINGS_MODULE"
echo "  - ALLOWED_HOSTS: $ALLOWED_HOSTS"
echo "  - DATABASE_URL: ${DATABASE_URL:0:50}..."
echo "  - PORT: ${PORT:-8000}"

# Start the server
echo "✅ Starting Gunicorn server..."
exec gunicorn core.wsgi:application \
    --bind 0.0.0.0:${PORT:-8000} \
    --workers ${WEB_CONCURRENCY:-4} \
    --timeout 120 \
    --access-logfile - \
    --error-logfile - \
    --log-level info \
    --preload