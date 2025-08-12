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
python manage.py migrate --no-input 2>&1 | tee /tmp/migrate.log || {
    # Check if it's the duplicate column error
    if grep -q "column.*already exists" /tmp/migrate.log; then
        echo "⚠️  Detected duplicate column error. Attempting to fix..."
        
        # Try to reset and recreate from scratch
        python -c "
import django
django.setup()
from django.db import connection
with connection.cursor() as cursor:
    # Drop all tables in public schema
    cursor.execute('''
        DO \$\$ 
        DECLARE r RECORD;
        BEGIN
            FOR r IN (SELECT tablename FROM pg_tables WHERE schemaname = 'public') 
            LOOP
                EXECUTE 'DROP TABLE IF EXISTS ' || quote_ident(r.tablename) || ' CASCADE';
            END LOOP;
        END \$\$;
    ''')
    print('✅ All tables dropped')
"
        
        # Try migrations again
        echo "🔄 Retrying migrations after cleanup..."
        python manage.py migrate --no-input || echo "⚠️  Migrations still having issues"
    else
        echo "⚠️  Some migrations failed, but continuing..."
    fi
}

# Collect static files
echo "📦 Collecting static files..."
python manage.py collectstatic --no-input || echo "⚠️  Static files collection had issues"

# Initialize production data
echo "📊 Initializing production data..."

# Create subscription plans
echo "  Creating subscription plans..."
python manage.py create_subscription_plans 2>/dev/null || echo "  ℹ️  Subscription plans already exist or could not be created"

# Sync Pluggy connectors (banks)
if [ -n "$PLUGGY_CLIENT_ID" ] && [ -n "$PLUGGY_CLIENT_SECRET" ]; then
    echo "  Syncing Pluggy connectors..."
    python manage.py sync_pluggy_connectors 2>/dev/null || echo "  ⚠️  Could not sync Pluggy connectors"
else
    echo "  ℹ️  Skipping Pluggy sync (API keys not configured)"
fi

# Create default transaction categories
echo "  Creating default categories..."
python -c "
import django
django.setup()
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
print('  ✅ Default categories created')
" 2>/dev/null || echo "  ℹ️  Categories already exist or could not be created"

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