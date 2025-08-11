#!/bin/bash
# Celery worker startup script with monitoring

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() {
    echo -e "${GREEN}[CELERY]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[CELERY]${NC} $1"
}

log_error() {
    echo -e "${RED}[CELERY]${NC} $1"
}

# Configuration
export DJANGO_SETTINGS_MODULE=${DJANGO_SETTINGS_MODULE:-core.settings.production}
export CELERY_WORKER_CONCURRENCY=${CELERY_WORKER_CONCURRENCY:-4}
export CELERY_WORKER_PREFETCH=${CELERY_WORKER_PREFETCH:-1}
export CELERY_WORKER_MAX_TASKS=${CELERY_WORKER_MAX_TASKS:-1000}
export CELERY_WORKER_MAX_MEMORY=${CELERY_WORKER_MAX_MEMORY:-1000000}  # 1GB in KB

log_info "Starting Celery Worker"
log_info "Configuration:"
log_info "  - Concurrency: $CELERY_WORKER_CONCURRENCY"
log_info "  - Prefetch: $CELERY_WORKER_PREFETCH"
log_info "  - Max Tasks: $CELERY_WORKER_MAX_TASKS"
log_info "  - Max Memory: $CELERY_WORKER_MAX_MEMORY KB"

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

# Main execution
main() {
    # Wait for dependencies
    if ! wait_for_redis; then
        log_error "Redis is not available, exiting..."
        exit 1
    fi
    
    if ! wait_for_db; then
        log_error "Database is not available, exiting..."
        exit 1
    fi
    
    # Start Celery worker with optimized settings
    log_info "Starting Celery worker..."
    exec celery -A core worker \
        --loglevel=info \
        --concurrency=$CELERY_WORKER_CONCURRENCY \
        --prefetch-multiplier=$CELERY_WORKER_PREFETCH \
        --max-tasks-per-child=$CELERY_WORKER_MAX_TASKS \
        --max-memory-per-child=$CELERY_WORKER_MAX_MEMORY \
        --time-limit=300 \
        --soft-time-limit=240 \
        --queues=celery,banking,billing,reports,notifications,high_priority,low_priority \
        --without-gossip \
        --without-mingle \
        --without-heartbeat \
        --pool=prefork
}

# Run main function
main