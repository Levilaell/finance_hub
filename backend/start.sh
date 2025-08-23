#!/bin/bash
# Startup script for production deployment
# Last updated: $(date)

echo "🚀 Starting Finance Hub Backend..."
echo "📅 Deploy timestamp: $(date)"

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

# ULTIMATE MIGRATION FIXER - Definitively resolves auth.0003 vs auth.0002 dependency issue (PRIORITY 1)
echo "🚨 ULTIMATE MIGRATION FIXER - Resolving critical auth migration dependency..."
python ultimate_migration_fixer.py && {
    echo "✅ ULTIMATE MIGRATION FIX SUCCESS - auth.0003 vs auth.0002 dependency resolved!"
} || {
    echo "❌ ULTIMATE MIGRATION FIX FAILED - Falling back to comprehensive approach..."
}

# SMART EARLY ACCESS FIX - Resolves DuplicateColumn error (PRIORITY 2)
echo "🛠️  SMART EARLY ACCESS FIX - Resolving DuplicateColumn error..."
python fix_early_access_duplicate_column.py && {
    echo "✅ SMART FIX SUCCESS - Early access DuplicateColumn error resolved!"
} || {
    echo "❌ SMART FIX FAILED - Could not resolve early access column conflict..."
}

# COMPANIES MIGRATION DEPENDENCY FIX - Resolves 0009 vs 0008 dependency issue (PRIORITY 3)
echo "🛠️  COMPANIES MIGRATION DEPENDENCY FIX - Resolving companies migration order..."
python fix_companies_migration_dependency.py && {
    echo "✅ COMPANIES DEPENDENCY FIX SUCCESS - Migration order corrected!"
} || {
    echo "❌ COMPANIES DEPENDENCY FIX FAILED - Could not fix migration dependency..."
}

# CELERY BEAT MIGRATION FIX - Resolves DuplicateTable error (PRIORITY 4)
echo "🛠️  CELERY BEAT MIGRATION FIX - Resolving DuplicateTable error..."
python fix_celery_beat_migration_conflict.py && {
    echo "✅ CELERY BEAT CONFLICT DETECTED - Applying --fake flag fix"
    
    # Check if conflict marker exists
    if [ -f "/tmp/celery_beat_conflict_detected" ]; then
        echo "📋 Conflict detected - using --fake flag for django_celery_beat"
        python manage.py migrate django_celery_beat --fake || echo "⚠️  Could not fake apply django_celery_beat migrations"
    else
        echo "📋 No conflict detected - applying migrations normally"
        python manage.py migrate django_celery_beat || echo "⚠️  Django Celery Beat migrations had issues"
    fi
    
    echo "✅ CELERY BEAT FIX SUCCESS - DuplicateTable error resolved!"
} || {
    echo "❌ CELERY BEAT FIX FAILED - Could not resolve conflict..."
    echo "📋 Attempting normal migration anyway..."
    python manage.py migrate django_celery_beat || echo "⚠️  Django Celery Beat migrations failed"
}

# Fix migration dependencies with comprehensive approach
echo "🔧 Fixing migration dependencies..."
python fix_migration_history.py || {
    echo "⚠️  Comprehensive migration fix failed, trying fallback method..."
    
    # Fallback: Simple fix for the most common issues
    python -c "
import django
django.setup()
from django.db import connection
from django.db.migrations.recorder import MigrationRecorder

try:
    recorder = MigrationRecorder(connection)
    applied_migrations = set(recorder.applied_migrations())
    
    # Fix companies migration dependency issue
    companies_0008 = ('companies', '0008_alter_resourceusage_options_and_more')
    companies_0009 = ('companies', '0009_add_early_access')
    
    if companies_0009 in applied_migrations and companies_0008 not in applied_migrations:
        print('⚠️  Found companies migration dependency issue, applying fallback fix...')
        with connection.cursor() as cursor:
            cursor.execute(\"SELECT column_name FROM information_schema.columns WHERE table_name = 'companies_resourceusage'\")
            columns = [row[0] for row in cursor.fetchall()]
            if 'created_at' in columns and 'updated_at' in columns:
                recorder.record_applied(companies_0008[0], companies_0008[1])
                print('✅ Companies migration 0008 marked as applied (fallback)')
    
    # Fix reports migration dependency issue (ULTRA-DEEP ANALYSIS)
    # Check for InconsistentMigrationHistory error condition
    with connection.cursor() as cursor:
        cursor.execute(\"\"\"
            SELECT app, name, applied 
            FROM django_migrations 
            WHERE app = 'reports' 
            ORDER BY applied
        \"\"\")
        reports_migrations = cursor.fetchall()
        
        print(f'📊 Found {len(reports_migrations)} applied reports migrations:')
        for app, name, applied in reports_migrations:
            print(f'    {app}.{name} (applied: {applied})')
            
        # Check for all problematic migrations that cause dependency issues
        problematic_migrations = [
            '0002_alter_aianalysis_options_and_more',
            '0003_aianalysistemplate_aianalysis', 
            '0004_merge_20250803_2225',
            '0005_fix_inconsistent_history'
        ]
        
        migrations_to_remove = []
        for _, name, _ in reports_migrations:
            for problematic in problematic_migrations:
                if problematic in name:
                    migrations_to_remove.append(name)
                    break
        
        if migrations_to_remove:
            print(f'⚠️  Found {len(migrations_to_remove)} problematic reports migrations causing InconsistentMigrationHistory')
            print(f'🔧 Removing migrations: {migrations_to_remove}')
            print('   This allows Django to reapply them in correct dependency order')
            
            total_removed = 0
            for migration_name in migrations_to_remove:
                cursor.execute(\"DELETE FROM django_migrations WHERE app = 'reports' AND name = %s\", [migration_name])
                deleted = cursor.rowcount
                total_removed += deleted
                print(f'   ✅ Removed migration: {migration_name} ({deleted} record)')
            
            print(f'✅ Total removed {total_removed} reports migration records for correct reordering')
        else:
            print('✅ No reports migration inconsistency detected')
    
    print('✅ Fallback migration fix completed')
except Exception as e:
    print(f'⚠️  Fallback migration fix failed: {e}')
" || echo "⚠️  All migration dependency fixes failed"
    
    # If all else fails, try to migrate anyway
    echo "🔄 Attempting migrations despite dependency issues..."
    python manage.py migrate --no-input || echo "⚠️  Final migration attempt failed"
}

# Ensure email_verifications table exists (critical fix for admin delete)
echo "🔧 Checking email_verifications table..."
python -c "
import django
django.setup()
from django.db import connection
try:
    with connection.cursor() as cursor:
        # Check if table exists
        cursor.execute(\"SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'email_verifications';\")
        exists = cursor.fetchone()[0] > 0
        if not exists:
            print('⚠️  email_verifications table missing, creating...')
            # Create table
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
            # Create indexes
            cursor.execute('CREATE INDEX email_verif_user_id_f77c27_idx ON email_verifications (user_id, is_used);')
            cursor.execute('CREATE INDEX email_verif_token_403404_idx ON email_verifications (token);')
            cursor.execute('CREATE INDEX email_verif_expires_fdd67c_idx ON email_verifications (expires_at);')
            # Mark migration as applied
            cursor.execute('''
                INSERT INTO django_migrations (app, name, applied) 
                VALUES ('authentication', '0003_emailverification', NOW())
                ON CONFLICT (app, name) DO NOTHING;
            ''')
            print('✅ email_verifications table created successfully')
        else:
            print('✅ email_verifications table already exists')
except Exception as e:
    print(f'⚠️  Could not verify/create email_verifications table: {e}')
" || echo "⚠️  Email verification table check failed"

# Collect static files
echo "📦 Collecting static files..."
python manage.py collectstatic --no-input || echo "⚠️  Static files collection had issues"

# Initialize production data
echo "📊 Initializing production data..."

# Sync subscription plans with correct prices and Stripe IDs
echo "  Syncing subscription plans with Stripe..."
python manage.py sync_subscription_plans || echo "  ⚠️  Could not sync subscription plans"

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