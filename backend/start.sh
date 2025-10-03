#!/bin/bash
set -e  # Exit on error

echo "========================================="
echo "=� Starting Finance Hub Backend"
echo "========================================="

# Environment info
echo "=� Environment: ${DJANGO_ENV:-production}"
echo "= Python version: $(python --version)"
echo "=' Django settings: ${DJANGO_SETTINGS_MODULE:-core.settings.production}"

# Check required environment variables
echo ""
echo "= Checking required environment variables..."

check_env_var() {
    if [ -z "${!1}" ]; then
        echo "L ERROR: $1 is not set!"
        exit 1
    else
        echo " $1 is configured"
    fi
}

check_env_var "DATABASE_URL"
check_env_var "DJANGO_SECRET_KEY"

# Optional but recommended checks (warnings only)
if [ -z "$STRIPE_TEST_SECRET_KEY" ] && [ -z "$STRIPE_LIVE_SECRET_KEY" ]; then
    echo "�  WARNING: Stripe keys not configured - payment features will not work"
fi

if [ -z "$PLUGGY_CLIENT_ID" ] || [ -z "$PLUGGY_CLIENT_SECRET" ]; then
    echo "�  WARNING: Pluggy credentials not configured - banking features will not work"
fi

# Test database connection
echo ""
echo "= Testing database connection..."
python manage.py check --database default || {
    echo "L Database connection failed!"
    echo "=� Check your DATABASE_URL configuration"
    exit 1
}
echo " Database connection successful"

# Run migrations
echo ""
echo "= Running database migrations..."
python manage.py migrate --noinput || {
    echo "L Migration failed!"
    exit 1
}
echo " Migrations completed"

# Collect static files
echo ""
echo "=� Collecting static files..."
python manage.py collectstatic --noinput --clear || {
    echo "L Static files collection failed!"
    exit 1
}
echo " Static files collected"

# Optional: Create superuser if needed (only first deploy)
if [ "$CREATE_SUPERUSER" = "true" ]; then
    echo ""
    echo "=d Creating superuser..."
    python manage.py createsuperuser --noinput || echo "9  Superuser already exists or skipped"
fi

# Determine number of workers based on available CPUs
WORKERS=${WEB_CONCURRENCY:-4}
TIMEOUT=${GUNICORN_TIMEOUT:-120}
PORT=${PORT:-8000}

echo ""
echo "========================================="
echo "< Starting Gunicorn server"
echo "========================================="
echo "=� Port: $PORT"
echo "=w Workers: $WORKERS"
echo "�  Timeout: ${TIMEOUT}s"
echo "========================================="

# Self-ping helper function (runs in background after Gunicorn starts)
self_ping() {
    echo "⏳ Waiting 5s for Gunicorn..."
    sleep 5
    echo "🏓 Self-ping to wake Railway networking..."
    curl -f http://localhost:$PORT/health/ 2>/dev/null && echo "✅ Self-ping successful!" || echo "⚠️  Self-ping failed"
}

# Start self-ping in background
self_ping &

# Start Gunicorn with production settings
exec gunicorn core.wsgi:application \
    --bind 0.0.0.0:$PORT \
    --workers $WORKERS \
    --worker-class sync \
    --timeout $TIMEOUT \
    --graceful-timeout 30 \
    --max-requests 1000 \
    --max-requests-jitter 100 \
    --access-logfile - \
    --error-logfile - \
    --log-level info \
    --capture-output \
    --enable-stdio-inheritance
