#!/bin/sh
set -e

# Use PORT environment variable, default to 8000 if not set
export PORT=${PORT:-8000}

# Ensure we're using production settings
export DJANGO_ENV=${DJANGO_ENV:-production}
export DJANGO_SETTINGS_MODULE=${DJANGO_SETTINGS_MODULE:-core.settings.production}

echo "Starting Django server on port $PORT"
echo "Using settings: $DJANGO_SETTINGS_MODULE"

# Check for critical environment variables
if [ -z "$DJANGO_SECRET_KEY" ]; then
    echo "WARNING: DJANGO_SECRET_KEY is not set!"
    echo "Please set it in Railway dashboard > Variables"
    echo "The app will start with a temporary key but this is INSECURE!"
fi

if [ -z "$DATABASE_URL" ]; then
    echo "WARNING: DATABASE_URL is not set!"
    echo "Railway should provide this automatically."
    echo "Check your database service configuration."
fi

# Run migrations in correct order to handle dependencies
echo "Running migrations..."

# First, try the emergency fix script if it exists
if [ -f "/app/fix_database.py" ]; then
    echo "🔧 Running emergency database fix..."
    python /app/fix_database.py || echo "⚠️ Fix script had issues but continuing..."
fi

# Try to fix any migration inconsistencies first (if command exists)
python manage.py fix_migrations 2>/dev/null || true

# Try normal migration process
python manage.py migrate --noinput 2>&1 | tee /tmp/migrate.log || {
    echo "⚠️ Migration failed, checking error..."
    
    # Check if it's the inconsistent migration history error
    if grep -q "InconsistentMigrationHistory" /tmp/migrate.log; then
        echo "⚠️ Detected inconsistent migration history, attempting to fix..."
        
        # Try to fake the problematic migration
        python manage.py migrate reports 0002 --fake --noinput 2>/dev/null || true
        
        # Try migrate again
        python manage.py migrate --noinput || {
            echo "⚠️ Still failing, ensuring critical tables exist..."
            python manage.py ensure_critical_tables 2>/dev/null || {
                # If the command doesn't exist, run fix_database.py again
                [ -f "/app/fix_database.py" ] && python /app/fix_database.py || true
            }
        }
    else
        echo "⚠️ Other migration error, ensuring critical tables exist..."
        python manage.py ensure_critical_tables 2>/dev/null || {
            # If the command doesn't exist, run fix_database.py
            [ -f "/app/fix_database.py" ] && python /app/fix_database.py || true
        }
    fi
}

echo "Migration process completed (with possible warnings)"

# Collect static files
python manage.py collectstatic --noinput

# Start gunicorn
exec gunicorn core.wsgi:application --bind 0.0.0.0:$PORT --workers 4 --timeout 120 --log-level info