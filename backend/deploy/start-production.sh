#!/bin/bash
# Production startup script with comprehensive error handling

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Configuration
export DJANGO_SETTINGS_MODULE=${DJANGO_SETTINGS_MODULE:-core.settings.production}
export PORT=${PORT:-8000}
export WORKERS=${WEB_CONCURRENCY:-4}
export TIMEOUT=${GUNICORN_TIMEOUT:-120}

log_info "Starting Finance Hub Backend in Production Mode"
log_info "Configuration:"
log_info "  - Django Settings: $DJANGO_SETTINGS_MODULE"
log_info "  - Port: $PORT"
log_info "  - Workers: $WORKERS"
log_info "  - Timeout: $TIMEOUT"

# Auto-configure ALLOWED_HOSTS if not set
if [ -z "$ALLOWED_HOSTS" ]; then
    if [ -n "$RAILWAY_PUBLIC_DOMAIN" ]; then
        export ALLOWED_HOSTS="$RAILWAY_PUBLIC_DOMAIN,*.railway.app,localhost,127.0.0.1"
        log_info "Auto-configured ALLOWED_HOSTS: $ALLOWED_HOSTS"
    else
        export ALLOWED_HOSTS="*"
        log_warning "Using permissive ALLOWED_HOSTS - configure for production!"
    fi
fi

# Check if DATABASE_URL is configured
check_database_url() {
    if [ -z "$DATABASE_URL" ]; then
        log_error "DATABASE_URL is not configured!"
        log_info "Please add PostgreSQL service in Railway Dashboard:"
        log_info "1. Click 'New' → 'Database' → 'PostgreSQL'"
        log_info "2. Go to your service Variables"
        log_info "3. Add reference: DATABASE_URL → \${{Postgres.DATABASE_URL}}"
        
        # Start without database for now (will fail health checks)
        log_warning "Starting without database - service will not be fully functional"
        return 1
    fi
    return 0
}

# Wait for database with exponential backoff
wait_for_db() {
    local max_attempts=30
    local attempt=1
    local wait_time=1
    
    log_info "Waiting for database connection..."
    
    # First check if DATABASE_URL exists
    if ! check_database_url; then
        return 1
    fi
    
    while [ $attempt -le $max_attempts ]; do
        if python -c "
import os
import sys

# Check DATABASE_URL
database_url = os.environ.get('DATABASE_URL')
if not database_url or database_url == 'dummy':
    print('WARNING: DATABASE_URL environment variable is not set or invalid!')
    print('Using a dummy database URL - database operations will fail.')
    print('Please set DATABASE_URL in Railway dashboard.')
    print('Use the reference button to link to your database service.')
    sys.exit(1)

import django
django.setup()
from django.db import connection
with connection.cursor() as cursor:
    cursor.execute('SELECT 1')
" 2>/dev/null; then
            log_info "Database connection established!"
            return 0
        fi
        
        log_warning "Database not ready (attempt $attempt/$max_attempts), waiting ${wait_time}s..."
        sleep $wait_time
        
        # Exponential backoff with max wait of 10 seconds
        wait_time=$((wait_time * 2))
        if [ $wait_time -gt 10 ]; then
            wait_time=10
        fi
        
        attempt=$((attempt + 1))
    done
    
    log_error "Database connection failed after $max_attempts attempts"
    return 1
}

# Run database migrations safely
run_migrations() {
    log_info "Running database migrations..."
    
    # Create migration lock to prevent concurrent migrations
    python -c "
import django
django.setup()
from django.db import connection
with connection.cursor() as cursor:
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS migration_lock (
            id INTEGER PRIMARY KEY DEFAULT 1,
            locked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            CHECK (id = 1)
        )
    ''')
" 2>/dev/null || true
    
    # Try to acquire lock
    local locked=false
    for i in {1..10}; do
        if python -c "
import django
django.setup()
from django.db import connection
with connection.cursor() as cursor:
    try:
        cursor.execute('INSERT INTO migration_lock (id) VALUES (1)')
        connection.commit()
        print('LOCK_ACQUIRED')
    except:
        print('LOCK_BUSY')
" | grep -q "LOCK_ACQUIRED"; then
            locked=true
            break
        fi
        log_warning "Migration lock busy, waiting 5s..."
        sleep 5
    done
    
    if [ "$locked" = true ]; then
        # Run migrations
        python manage.py migrate --noinput || {
            log_error "Migration failed!"
            # Release lock on failure
            python -c "
import django
django.setup()
from django.db import connection
with connection.cursor() as cursor:
    cursor.execute('DELETE FROM migration_lock WHERE id = 1')
" 2>/dev/null || true
            exit 1
        }
        
        # Release lock
        python -c "
import django
django.setup()
from django.db import connection
with connection.cursor() as cursor:
    cursor.execute('DELETE FROM migration_lock WHERE id = 1')
" 2>/dev/null || true
        
        log_info "Migrations completed successfully"
    else
        log_warning "Could not acquire migration lock, assuming another instance is migrating"
    fi
}

# Create superuser if needed
create_superuser() {
    if [ -n "$DJANGO_SUPERUSER_EMAIL" ] && [ -n "$DJANGO_SUPERUSER_PASSWORD" ]; then
        log_info "Checking for superuser..."
        python -c "
import os
import django
django.setup()
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(is_superuser=True).exists():
    email = os.environ.get('DJANGO_SUPERUSER_EMAIL')
    password = os.environ.get('DJANGO_SUPERUSER_PASSWORD')
    User.objects.create_superuser(
        username='admin',
        email=email,
        password=password
    )
    print('Superuser created successfully')
else:
    print('Superuser already exists')
" || log_warning "Could not create superuser"
    fi
}

# Initialize default data
initialize_data() {
    log_info "Initializing default data..."
    python -c "
import django
django.setup()

# Create default subscription plans if they don't exist
from apps.subscriptions.models import Plan, Feature
from decimal import Decimal

# Define default plans
default_plans = [
    {
        'name': 'Free',
        'slug': 'free',
        'price': Decimal('0.00'),
        'interval': 'month',
        'trial_days': 0,
        'features': {
            'bank_accounts': 1,
            'transactions_per_month': 100,
            'users': 1,
            'ai_insights': False,
            'custom_reports': False,
            'api_access': False
        }
    },
    {
        'name': 'Starter',
        'slug': 'starter',
        'price': Decimal('29.90'),
        'interval': 'month',
        'trial_days': 14,
        'features': {
            'bank_accounts': 3,
            'transactions_per_month': 1000,
            'users': 2,
            'ai_insights': True,
            'custom_reports': False,
            'api_access': False
        }
    },
    {
        'name': 'Professional',
        'slug': 'professional',
        'price': Decimal('79.90'),
        'interval': 'month',
        'trial_days': 14,
        'features': {
            'bank_accounts': 10,
            'transactions_per_month': 10000,
            'users': 5,
            'ai_insights': True,
            'custom_reports': True,
            'api_access': True
        }
    },
    {
        'name': 'Enterprise',
        'slug': 'enterprise',
        'price': Decimal('299.90'),
        'interval': 'month',
        'trial_days': 30,
        'features': {
            'bank_accounts': -1,  # Unlimited
            'transactions_per_month': -1,  # Unlimited
            'users': -1,  # Unlimited
            'ai_insights': True,
            'custom_reports': True,
            'api_access': True
        }
    }
]

for plan_data in default_plans:
    features = plan_data.pop('features')
    plan, created = Plan.objects.get_or_create(
        slug=plan_data['slug'],
        defaults=plan_data
    )
    if created:
        print(f'Created plan: {plan.name}')
        
        # Create features for the plan
        for feature_key, value in features.items():
            Feature.objects.get_or_create(
                plan=plan,
                name=feature_key,
                defaults={'value': str(value)}
            )
    else:
        print(f'Plan already exists: {plan.name}')

print('Default data initialization complete')
" || log_warning "Could not initialize default data"
}

# Main execution
main() {
    # Wait for database
    if ! wait_for_db; then
        log_error "Database is not available, exiting..."
        exit 1
    fi
    
    # Run migrations
    run_migrations
    
    # Create superuser if configured
    create_superuser
    
    # Initialize default data
    initialize_data
    
    # Start Gunicorn with optimal settings
    log_info "Starting Gunicorn server..."
    exec gunicorn core.wsgi:application \
        --bind 0.0.0.0:$PORT \
        --workers $WORKERS \
        --worker-class sync \
        --worker-connections 1000 \
        --max-requests 1000 \
        --max-requests-jitter 100 \
        --timeout $TIMEOUT \
        --graceful-timeout 30 \
        --keep-alive 5 \
        --access-logfile - \
        --error-logfile - \
        --log-level info \
        --capture-output \
        --enable-stdio-inheritance \
        --preload
}

# Run main function
main