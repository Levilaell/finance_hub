#!/bin/bash
# Simplified startup script for production deployment - NO missing file references

echo "🚀 Starting Finance Hub Backend..."

# Set default environment variables if not set
export DJANGO_SETTINGS_MODULE=${DJANGO_SETTINGS_MODULE:-core.settings.production}

# If ALLOWED_HOSTS is not set, try to auto-detect from Railway
if [ -z "$ALLOWED_HOSTS" ]; then
    if [ -n "$RAILWAY_PUBLIC_DOMAIN" ]; then
        export ALLOWED_HOSTS="$RAILWAY_PUBLIC_DOMAIN,*.railway.app,healthcheck.railway.app,localhost,127.0.0.1"
    else
        export ALLOWED_HOSTS="*"
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

# Run migrations (simple approach)
echo "🔧 Running migrations..."
python manage.py migrate --no-input

# Collect static files
echo "📦 Collecting static files..."
python manage.py collectstatic --no-input

# Initialize production data
echo "📊 Initializing production data..."

# Sync subscription plans
python manage.py sync_subscription_plans 2>/dev/null || {
    echo "⚠️ Could not sync subscription plans - continuing..."
}

# Sync Pluggy connectors (only if configured)
if [ -n "$PLUGGY_CLIENT_ID" ] && [ -n "$PLUGGY_CLIENT_SECRET" ]; then
    echo "🔌 Syncing Pluggy connectors..."
    python manage.py sync_pluggy_connectors 2>/dev/null || {
        echo "⚠️ Could not sync Pluggy connectors - continuing..."
    }
else
    echo "⚠️ Pluggy not configured (missing PLUGGY_CLIENT_ID or PLUGGY_CLIENT_SECRET)"
fi

# Create default transaction categories
echo "📊 Creating default transaction categories..."
python -c "
import django
django.setup()
try:
    from apps.banking.models import TransactionCategory
    categories = [
        {'name': 'Alimentação', 'slug': 'alimentacao', 'icon': '🍴', 'color': '#FF6B6B'},
        {'name': 'Transporte', 'slug': 'transporte', 'icon': '🚗', 'color': '#4ECDC4'},
        {'name': 'Moradia', 'slug': 'moradia', 'icon': '🏠', 'color': '#45B7D1'},
        {'name': 'Saúde', 'slug': 'saude', 'icon': '⚕️', 'color': '#96CEB4'},
        {'name': 'Educação', 'slug': 'educacao', 'icon': '📚', 'color': '#FECA57'},
        {'name': 'Lazer', 'slug': 'lazer', 'icon': '🎮', 'color': '#9C88FF'},
        {'name': 'Compras', 'slug': 'compras', 'icon': '🛍️', 'color': '#FD79A8'},
        {'name': 'Serviços', 'slug': 'servicos', 'icon': '🔧', 'color': '#A29BFE'},
        {'name': 'Investimentos', 'slug': 'investimentos', 'icon': '📈', 'color': '#00B894'},
        {'name': 'Outros', 'slug': 'outros', 'icon': '📌', 'color': '#636E72'},
    ]
    for cat in categories:
        TransactionCategory.objects.get_or_create(slug=cat['slug'], defaults=cat)
    print('✅ Transaction categories initialized')
except Exception as e:
    print(f'⚠️ Could not create transaction categories: {e}')
" 2>/dev/null

# Create default superuser if it doesn't exist
echo "👤 Creating superuser if needed..."
python -c "
import os
import django
django.setup()
try:
    from django.contrib.auth import get_user_model
    User = get_user_model()
    if not User.objects.filter(is_superuser=True).exists():
        email = os.environ.get('DJANGO_SUPERUSER_EMAIL', 'admin@finance-hub.com')
        password = os.environ.get('DJANGO_SUPERUSER_PASSWORD', 'admin123')
        if email and password:
            User.objects.create_superuser(username='admin', email=email, password=password)
            print('✅ Superuser created')
    else:
        print('✅ Superuser already exists')
except Exception as e:
    print(f'⚠️ Could not create superuser: {e}')
" 2>/dev/null

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