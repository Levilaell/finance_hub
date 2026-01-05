#!/bin/bash
set -e  # Exit on error

echo "========================================="
echo "📅 Starting Celery Beat Scheduler"
echo "========================================="

# Environment info
echo "🌍 Environment: ${DJANGO_ENV:-production}"
echo "🐍 Python version: $(python --version)"

# Check required environment variables
echo ""
echo "🔍 Checking required environment variables..."

check_env_var() {
    if [ -z "${!1}" ]; then
        echo "❌ ERROR: $1 is not set!"
        exit 1
    else
        echo "✅ $1 is configured"
    fi
}

check_env_var "DATABASE_URL"
check_env_var "REDIS_URL"

# Test Redis connection
echo ""
echo "🔍 Testing Redis connection..."
python -c "
import os
import redis
from urllib.parse import urlparse

redis_url = os.environ.get('REDIS_URL')
parsed = urlparse(redis_url)

# Extract connection details
host = parsed.hostname
port = parsed.port or 6379
password = parsed.password
db = int(parsed.path.lstrip('/')) if parsed.path and len(parsed.path) > 1 else 0

# Test connection
r = redis.Redis(host=host, port=port, password=password, db=db, socket_connect_timeout=5)
r.ping()
print('✅ Redis connection successful')
" || {
    echo "❌ Redis connection failed!"
    echo "⚠️  Check your REDIS_URL configuration"
    exit 1
}

echo ""
echo "========================================="
echo "📅 Starting Celery Beat"
echo "========================================="
echo "⏰ Scheduled tasks will run according to beat_schedule"
echo "📊 Check logs for task execution"
echo "========================================="

# Start Celery Beat
exec celery -A core beat \
    --loglevel=info \
    --scheduler django_celery_beat.schedulers:DatabaseScheduler
