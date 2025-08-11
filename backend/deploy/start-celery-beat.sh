#!/bin/bash
# Celery Beat scheduler startup script

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() {
    echo -e "${GREEN}[BEAT]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[BEAT]${NC} $1"
}

log_error() {
    echo -e "${RED}[BEAT]${NC} $1"
}

# Configuration
export DJANGO_SETTINGS_MODULE=${DJANGO_SETTINGS_MODULE:-core.settings.production}

log_info "Starting Celery Beat Scheduler"

# Wait for Redis
wait_for_redis() {
    local max_attempts=30
    local attempt=1
    
    log_info "Waiting for Redis connection..."
    
    while [ $attempt -le $max_attempts ]; do
        if python -c "
import redis
import os
r = redis.from_url(os.environ.get('REDIS_URL', 'redis://localhost:6379'))
r.ping()
print('Redis is ready')
" 2>/dev/null; then
            log_info "Redis connection established!"
            return 0
        fi
        
        log_warning "Redis not ready (attempt $attempt/$max_attempts), waiting 2s..."
        sleep 2
        attempt=$((attempt + 1))
    done
    
    log_error "Redis connection failed after $max_attempts attempts"
    return 1
}

# Wait for database
wait_for_db() {
    local max_attempts=30
    local attempt=1
    
    log_info "Waiting for database connection..."
    
    while [ $attempt -le $max_attempts ]; do
        if python -c "
import django
django.setup()
from django.db import connection
with connection.cursor() as cursor:
    cursor.execute('SELECT 1')
" 2>/dev/null; then
            log_info "Database connection established!"
            return 0
        fi
        
        log_warning "Database not ready (attempt $attempt/$max_attempts), waiting 2s..."
        sleep 2
        attempt=$((attempt + 1))
    done
    
    log_error "Database connection failed after $max_attempts attempts"
    return 1
}

# Clean up old beat schedule
cleanup_beat_schedule() {
    log_info "Cleaning up old beat schedule..."
    rm -f /app/celerybeat-schedule.db 2>/dev/null || true
    rm -f /app/celerybeat.pid 2>/dev/null || true
}

# Initialize periodic tasks
initialize_periodic_tasks() {
    log_info "Initializing periodic tasks..."
    python -c "
import django
django.setup()
from django_celery_beat.models import PeriodicTask, IntervalSchedule, CrontabSchedule
from datetime import datetime

# Create interval schedules
intervals = [
    (1, 'minutes'),
    (5, 'minutes'),
    (15, 'minutes'),
    (30, 'minutes'),
    (1, 'hours'),
    (6, 'hours'),
    (12, 'hours'),
    (1, 'days'),
]

for every, period in intervals:
    IntervalSchedule.objects.get_or_create(
        every=every,
        period=period
    )

# Create crontab schedules
crontabs = [
    {'minute': '0', 'hour': '0'},  # Daily at midnight
    {'minute': '0', 'hour': '*/6'},  # Every 6 hours
    {'minute': '0', 'hour': '9'},  # Daily at 9 AM
    {'minute': '0', 'hour': '18'},  # Daily at 6 PM
    {'minute': '0', 'hour': '0', 'day_of_week': '1'},  # Weekly on Monday
    {'minute': '0', 'hour': '0', 'day_of_month': '1'},  # Monthly on 1st
]

for crontab_data in crontabs:
    CrontabSchedule.objects.get_or_create(**crontab_data)

# Default periodic tasks
tasks = [
    {
        'name': 'sync-all-bank-accounts',
        'task': 'apps.banking.tasks.sync_all_accounts',
        'interval': IntervalSchedule.objects.get(every=6, period='hours'),
        'enabled': True
    },
    {
        'name': 'process-pending-payments',
        'task': 'apps.billing.tasks.process_pending_payments',
        'interval': IntervalSchedule.objects.get(every=15, period='minutes'),
        'enabled': True
    },
    {
        'name': 'send-trial-expiration-warnings',
        'task': 'apps.subscriptions.tasks.send_trial_expiration_warnings',
        'crontab': CrontabSchedule.objects.get(hour='9', minute='0'),
        'enabled': True
    },
    {
        'name': 'cleanup-old-sessions',
        'task': 'apps.core.tasks.cleanup_sessions',
        'crontab': CrontabSchedule.objects.get(hour='0', minute='0'),
        'enabled': True
    },
    {
        'name': 'generate-monthly-reports',
        'task': 'apps.reports.tasks.generate_monthly_reports',
        'crontab': CrontabSchedule.objects.get(day_of_month='1', hour='0', minute='0'),
        'enabled': True
    },
    {
        'name': 'update-ai-insights',
        'task': 'apps.ai_insights.tasks.update_insights',
        'interval': IntervalSchedule.objects.get(every=12, period='hours'),
        'enabled': True
    },
]

for task_data in tasks:
    task_name = task_data.pop('name')
    PeriodicTask.objects.get_or_create(
        name=task_name,
        defaults=task_data
    )

print('Periodic tasks initialized successfully')
" || log_warning "Could not initialize periodic tasks"
}

# Main execution
main() {
    # Clean up old schedules
    cleanup_beat_schedule
    
    # Wait for dependencies
    if ! wait_for_redis; then
        log_error "Redis is not available, exiting..."
        exit 1
    fi
    
    if ! wait_for_db; then
        log_error "Database is not available, exiting..."
        exit 1
    fi
    
    # Initialize periodic tasks
    initialize_periodic_tasks
    
    # Start Celery Beat
    log_info "Starting Celery Beat scheduler..."
    exec celery -A core beat \
        --loglevel=info \
        --scheduler django_celery_beat.schedulers:DatabaseScheduler \
        --pidfile=/app/celerybeat.pid
}

# Run main function
main