#!/bin/bash
# Simplified startup script for production deployment - NO missing file references

echo "🚀 Starting CaixaHub Backend..."

# Set default environment variables if not set
export DJANGO_SETTINGS_MODULE=${DJANGO_SETTINGS_MODULE:-core.settings.production}

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

# Run migrations (simple approach)
echo "🔧 Running migrations..."
python manage.py migrate --no-input

# Collect static files
echo "📦 Collecting static files..."
python manage.py collectstatic --no-input

# Initialize production data
echo "📊 Initializing production data..."

# Sync Pluggy connectors (only if configured)
if [ -n "$PLUGGY_CLIENT_ID" ] && [ -n "$PLUGGY_CLIENT_SECRET" ]; then
    echo "🔌 Syncing Pluggy connectors..."
    python manage.py sync_pluggy_connectors 2>/dev/null || {
        echo "⚠️ Could not sync Pluggy connectors - continuing..."
    }
else
    echo "⚠️ Pluggy not configured (missing PLUGGY_CLIENT_ID or PLUGGY_CLIENT_SECRET)"
fi

# Note: Rate limiting and session clearing disabled in production
# - django_ratelimit disabled (RATELIMIT_ENABLE = False)
# - Sessions use dummy backend (no Redis dependency)
# - DRF throttling handles rate limiting via dummy cache
echo "🔧 Production authentication: JWT-only (no sessions, no Redis)"

# Check authentication configuration
echo "🔐 Validating authentication configuration..."
python -c "
import django
django.setup()
from django.conf import settings
import os

print('=== AUTHENTICATION CONFIGURATION ===')
print(f'Frontend URL: {getattr(settings, \"FRONTEND_URL\", \"NOT SET\")}')
print(f'Backend URL: {getattr(settings, \"BACKEND_URL\", \"NOT SET\")}')
print(f'CORS Origins: {getattr(settings, \"CORS_ALLOWED_ORIGINS\", [])}')
print(f'JWT Cookie SameSite: {getattr(settings, \"JWT_COOKIE_SAMESITE\", \"NOT SET\")}')
print(f'JWT Cookie Secure: {getattr(settings, \"JWT_COOKIE_SECURE\", \"NOT SET\")}')
print(f'JWT Algorithm: {settings.SIMPLE_JWT.get(\"ALGORITHM\", \"NOT SET\")}')
print('✅ Simplified JWT Authentication ready')
print('=== END AUTHENTICATION CONFIG ===')
" 2>&1 | {
    while IFS= read -r line; do
        echo "AUTH-CONFIG: $line"
    done
}

echo "✅ System ready - Starting server..."

# Start the server with proper configuration for Railway
exec gunicorn core.wsgi:application \
    --bind 0.0.0.0:${PORT:-8000} \
    --workers ${WEB_CONCURRENCY:-4} \
    --timeout 120 \
    --access-logfile - \
    --error-logfile - \
    --log-level info \
    --preload