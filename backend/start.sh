#!/bin/bash
# Startup script for production deployment with comprehensive fixes

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

# CRITICAL: Force creation of users table if it doesn't exist
echo "🔧 Ensuring users table exists..."
python create_users_table.py || {
    echo "⚠️  Could not create users table with script, trying migrations..."
    python manage.py migrate contenttypes --no-input 2>/dev/null || true
    python manage.py migrate auth --no-input 2>/dev/null || true
    python manage.py migrate authentication --no-input 2>/dev/null || true
}

# Handle inconsistent migration history (for reports and companies apps)
echo "🔧 Checking for migration inconsistencies..."
python -c "
import django
django.setup()
from django.db import connection

try:
    with connection.cursor() as cursor:
        # Fix reports app issues
        cursor.execute('''
            SELECT COUNT(*) FROM django_migrations 
            WHERE app = 'reports' 
            AND name = '0003_aianalysistemplate_aianalysis'
        ''')
        reports_has_0003 = cursor.fetchone()[0] > 0
        
        cursor.execute('''
            SELECT COUNT(*) FROM django_migrations 
            WHERE app = 'reports' 
            AND name = '0002_alter_aianalysis_options_and_more'
        ''')
        reports_has_0002 = cursor.fetchone()[0] > 0
        
        if reports_has_0003 and not reports_has_0002:
            print('⚠️  Detected inconsistent migration state in reports app')
            print('🔧 Fixing by faking missing migration 0002...')
            cursor.execute('''
                INSERT INTO django_migrations (app, name, applied)
                SELECT 'reports', '0002_alter_aianalysis_options_and_more', applied
                FROM django_migrations
                WHERE app = 'reports' AND name = '0003_aianalysistemplate_aianalysis'
                LIMIT 1
            ''')
            print('✅ Reports migration history fixed!')
        
        # Fix companies app issues
        cursor.execute('''
            SELECT COUNT(*) FROM django_migrations 
            WHERE app = 'companies' 
            AND name = '0012_add_notification_fields'
        ''')
        companies_has_0012 = cursor.fetchone()[0] > 0
        
        cursor.execute('''
            SELECT COUNT(*) FROM django_migrations 
            WHERE app = 'companies' 
            AND name = '0011_merge_fixup'
        ''')
        companies_has_0011 = cursor.fetchone()[0] > 0
        
        if companies_has_0012 and not companies_has_0011:
            print('⚠️  Detected inconsistent migration state in companies app')
            print('🔧 Fixing by faking missing migration 0011...')
            cursor.execute('''
                INSERT INTO django_migrations (app, name, applied)
                SELECT 'companies', '0011_merge_fixup', applied
                FROM django_migrations
                WHERE app = 'companies' AND name = '0012_add_notification_fields'
                LIMIT 1
            ''')
            print('✅ Companies migration history fixed!')
            
except Exception as e:
    print(f'⚠️  Could not check migration consistency: {e}')
"

# Run migrations with better error handling
echo "🔄 Running migrations..."
MIGRATION_OUTPUT=$(python manage.py migrate --no-input 2>&1) || {
    echo "⚠️  Migration failed with error:"
    echo "$MIGRATION_OUTPUT"
    
    # Check if it's the inconsistent history error
    if echo "$MIGRATION_OUTPUT" | grep -q "InconsistentMigrationHistory"; then
        echo "🔧 Attempting to fix inconsistent migration history..."
        
        # Try to fake the problematic migrations for both apps
        python manage.py migrate reports 0001 --fake 2>/dev/null || true
        python manage.py migrate reports 0002 --fake 2>/dev/null || true
        python manage.py migrate reports 0003 --fake 2>/dev/null || true
        python manage.py migrate reports 0004_merge_20250803_2225 --fake 2>/dev/null || true
        python manage.py migrate companies 0010 --fake 2>/dev/null || true
        python manage.py migrate companies 0011 --fake 2>/dev/null || true
        python manage.py migrate companies 0012 --fake 2>/dev/null || true
        
        # Now try to run all migrations again
        echo "🔄 Retrying migrations after fixes..."
        python manage.py migrate --no-input || {
            echo "⚠️  Still couldn't run migrations, but continuing..."
            echo "⚠️  The application may not work properly!"
        }
    elif echo "$MIGRATION_OUTPUT" | grep -q "relation \"users\" does not exist"; then
        echo "🔧 Users table missing, trying to create it..."
        
        # Try to create with our script
        python create_users_table.py || {
            # If that fails, try with Django
            python manage.py migrate contenttypes --no-input --run-syncdb 2>/dev/null || true
            python manage.py migrate auth --no-input --run-syncdb 2>/dev/null || true
            python manage.py migrate authentication --no-input --run-syncdb 2>/dev/null || true
        }
        
        # Reset ai_insights migration if it's the problem
        echo "🔧 Resetting ai_insights migration to retry..."
        python -c "
import django
django.setup()
from django.db import connection
with connection.cursor() as cursor:
    cursor.execute(\"DELETE FROM django_migrations WHERE app = 'ai_insights' AND name = '0001_initial'\")
    print('Removed ai_insights 0001_initial from migration history')
" 2>/dev/null || true
        
        # Retry migrations
        echo "🔄 Retrying migrations after creating users table..."
        python manage.py migrate --no-input || echo "⚠️  Still having issues, but continuing..."
    else
        echo "⚠️  Could not run migrations, but continuing..."
    fi
}

# Collect static files (don't fail if this errors)
echo "📦 Collecting static files..."
python manage.py collectstatic --no-input || echo "⚠️  Static files collection failed, but continuing..."

# Create default superuser if it doesn't exist (optional)
echo "👤 Checking for superuser..."
python -c "
import os
import django
django.setup()
from django.contrib.auth import get_user_model
User = get_user_model()
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
" || echo "⚠️  Could not check/create superuser"

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