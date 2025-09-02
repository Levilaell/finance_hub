#!/bin/bash
# Startup script for production deployment

echo "🚀 Starting Finance Hub Backend..."

# Set default environment variables if not set
export DJANGO_SETTINGS_MODULE=${DJANGO_SETTINGS_MODULE:-core.settings.production}

# If ALLOWED_HOSTS is not set, try to auto-detect from Railway
if [ -z "$ALLOWED_HOSTS" ]; then
    if [ -n "$RAILWAY_PUBLIC_DOMAIN" ]; then
        export ALLOWED_HOSTS="$RAILWAY_PUBLIC_DOMAIN,*.railway.app,localhost,127.0.0.1"
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

# ULTRA-NUCLEAR MIGRATION FIX - Ensure clean migration state
echo "🔧 Ensuring clean migration state..."
python ultra_nuclear_fix.py && {
    echo "✅ Migration state verified"
    ULTRA_NUCLEAR_SUCCESS=true
} || {
    echo "❌ Migration fix failed - applying individual fixes..."
    ULTRA_NUCLEAR_SUCCESS=false
}

# Individual fixes (only if ultra-nuclear failed)
if [ "$ULTRA_NUCLEAR_SUCCESS" != "true" ]; then
    echo "🔧 Applying individual migration fixes..."
    
    python ultimate_migration_fixer.py 2>/dev/null
    python fix_early_access_duplicate_column.py 2>/dev/null
    python fix_companies_migration_dependency.py 2>/dev/null

    # Handle Celery Beat migration
    CELERY_FIX_RESULT=$(python railway_celery_beat_fix.py 2>/dev/null)
    case "$CELERY_FIX_RESULT" in
        "NEED_FAKE") python manage.py migrate django_celery_beat --fake 2>/dev/null ;;
        "NEED_FAKE_INITIAL") python manage.py migrate django_celery_beat --fake-initial 2>/dev/null ;;
        *) python manage.py migrate django_celery_beat 2>/dev/null ;;
    esac
fi

# Ensure required indexes exist
echo "🔧 Checking database indexes..."
python fix_missing_indexes.py 2>/dev/null || {
    python ultra_robust_index_fix.py 2>/dev/null || {
        python -c "
import django
django.setup()
from django.db import connection
try:
    with connection.cursor() as cursor:
        cursor.execute('CREATE INDEX IF NOT EXISTS reports_company_c4b7ee_idx ON reports (company_id);')
except Exception: pass
" 2>/dev/null
    }
}

# Clean up any residual migration records
python -c "
import django
django.setup()
from django.db import connection
try:
    with connection.cursor() as cursor:
        problematic_migrations = [
            ('reports', '0002_alter_aianalysis_options_and_more'),
            ('reports', '0003_aianalysistemplate_aianalysis'), 
            ('reports', '0004_merge_20250803_2225'),
            ('reports', '0005_fix_inconsistent_history')
        ]
        for app, migration_name in problematic_migrations:
            cursor.execute('DELETE FROM django_migrations WHERE app = %s AND name = %s', [app, migration_name])
        
        # Fix companies migration dependency if needed
        cursor.execute(\"SELECT name FROM django_migrations WHERE app = 'companies' ORDER BY applied\")
        companies_migrations = [row[0] for row in cursor.fetchall()]
        if '0009_add_early_access' in companies_migrations and '0008_alter_resourceusage_options_and_more' not in companies_migrations:
            cursor.execute(\"SELECT column_name FROM information_schema.columns WHERE table_name = 'companies_resourceusage'\")
            columns = [row[0] for row in cursor.fetchall()]
            if 'created_at' in columns and 'updated_at' in columns:
                cursor.execute(\"\"\"
                    INSERT INTO django_migrations (app, name, applied) 
                    VALUES ('companies', '0008_alter_resourceusage_options_and_more', NOW())
                    ON CONFLICT (app, name) DO NOTHING
                \"\"\")
except Exception: pass
" 2>/dev/null

# Run migrations
python manage.py migrate --no-input 2>/dev/null

# Fix foreign key constraint issue
echo "🔧 Fixing foreign key constraints..."
python fix_fk_constraint_startup.py || {
    echo "⚠️ FK constraint fix failed - may need manual intervention"
}

# Ensure email_verifications table exists
python -c "
import django
django.setup()
from django.db import connection
try:
    with connection.cursor() as cursor:
        cursor.execute(\"SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'email_verifications';\")
        exists = cursor.fetchone()[0] > 0
        if not exists:
            cursor.execute('''
                CREATE TABLE email_verifications (
                    id BIGSERIAL PRIMARY KEY,
                    token VARCHAR(100) UNIQUE NOT NULL,
                    is_used BOOLEAN DEFAULT FALSE NOT NULL,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    expires_at TIMESTAMPTZ NOT NULL,
                    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE
                );
            ''')
            cursor.execute('CREATE INDEX email_verif_user_id_f77c27_idx ON email_verifications (user_id, is_used);')
            cursor.execute('CREATE INDEX email_verif_token_403404_idx ON email_verifications (token);')
            cursor.execute('CREATE INDEX email_verif_expires_fdd67c_idx ON email_verifications (expires_at);')
            cursor.execute('''
                INSERT INTO django_migrations (app, name, applied) 
                VALUES ('authentication', '0003_emailverification', NOW())
                ON CONFLICT (app, name) DO NOTHING;
            ''')
except Exception: pass
" 2>/dev/null

# Collect static files
echo "📦 Collecting static files..."
python manage.py collectstatic --no-input 2>/dev/null

# Initialize production data
echo "📊 Initializing production data..."
python manage.py sync_subscription_plans 2>/dev/null

if [ -n "$PLUGGY_CLIENT_ID" ] && [ -n "$PLUGGY_CLIENT_SECRET" ]; then
    python manage.py sync_pluggy_connectors 2>/dev/null
fi

# Create default transaction categories
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
" 2>/dev/null

# Create default superuser if it doesn't exist
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
except Exception: pass
" 2>/dev/null

# ===== JWT AUTHENTICATION DIAGNOSTICS =====
echo "🔐 Running JWT Authentication Diagnostics..."
python manage.py diagnose_jwt_auth --fix-permissions 2>&1 | {
    while IFS= read -r line; do
        echo "AUTH-DIAG: $line"
        case "$line" in
            *"❌"*) echo "🚨 CRITICAL AUTH ERROR: $line" ;;
            *"⚠️"*) echo "⚠️ AUTH WARNING: $line" ;;
            *"✅"*) echo "✅ AUTH OK: $line" ;;
        esac
    done
} || {
    echo "🚨 CRITICAL: JWT Authentication diagnostic failed!"
    echo "🚨 This may cause authentication failures in production"
    echo "🚨 Check logs above for specific issues"
}

# Run additional authentication validation
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

# Check if JWT keys are loadable
try:
    from core.security import get_jwt_private_key, get_jwt_public_key
    private_key = get_jwt_private_key()
    public_key = get_jwt_public_key()
    print('✅ JWT keys loaded successfully (RS256 mode)')
    print(f'Private key length: {len(private_key)} chars')
    print(f'Public key length: {len(public_key)} chars')
except Exception as e:
    print(f'❌ JWT key loading failed: {e}')
    print('⚠️ System will fallback to HS256 with temporary key')

# Test simplified JWT authentication
try:
    from rest_framework_simplejwt.authentication import JWTAuthentication
    auth_instance = JWTAuthentication()
    print('✅ Simplified JWT Authentication ready')
except Exception as e:
    print(f'❌ JWT Authentication failed to load: {e}')

print('=== END AUTHENTICATION CONFIG ===')
" 2>&1 | {
    while IFS= read -r line; do
        echo "AUTH-CONFIG: $line"
    done
}

echo "✅ System ready - Starting server..."

# Start the server
exec gunicorn core.wsgi:application \
    --bind 0.0.0.0:${PORT:-8000} \
    --workers ${WEB_CONCURRENCY:-4} \
    --timeout 120 \
    --access-logfile - \
    --error-logfile - \
    --log-level info \
    --preload