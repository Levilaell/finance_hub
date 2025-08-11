#!/bin/bash
# Post-deployment validation and monitoring script

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() {
    echo -e "${GREEN}[POST-DEPLOY]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[POST-DEPLOY]${NC} $1"
}

log_error() {
    echo -e "${RED}[POST-DEPLOY]${NC} $1"
}

log_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

# Track validation results
VALIDATION_PASSED=true
HEALTH_CHECKS_PASSED=0
HEALTH_CHECKS_FAILED=0

# Check application health
check_app_health() {
    log_step "Checking application health..."
    
    local health_endpoint="${BACKEND_URL:-http://localhost:8000}/api/health/"
    local max_attempts=10
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if curl -f -s -o /dev/null -w "%{http_code}" "$health_endpoint" | grep -q "200"; then
            log_info "✓ Application health check passed"
            HEALTH_CHECKS_PASSED=$((HEALTH_CHECKS_PASSED + 1))
            return 0
        fi
        
        log_warning "Health check failed (attempt $attempt/$max_attempts), waiting 5s..."
        sleep 5
        attempt=$((attempt + 1))
    done
    
    log_error "Application health check failed after $max_attempts attempts"
    HEALTH_CHECKS_FAILED=$((HEALTH_CHECKS_FAILED + 1))
    VALIDATION_PASSED=false
    return 1
}

# Check database connectivity
check_database() {
    log_step "Checking database connectivity..."
    
    python -c "
import django
django.setup()
from django.db import connection
from django.contrib.auth import get_user_model

# Test connection
with connection.cursor() as cursor:
    cursor.execute('SELECT COUNT(*) FROM django_migrations')
    migration_count = cursor.fetchone()[0]
    print(f'Database connected: {migration_count} migrations')

# Test models
User = get_user_model()
user_count = User.objects.count()
print(f'User count: {user_count}')
" 2>/dev/null && {
        log_info "✓ Database connectivity verified"
        HEALTH_CHECKS_PASSED=$((HEALTH_CHECKS_PASSED + 1))
    } || {
        log_error "Database connectivity check failed"
        HEALTH_CHECKS_FAILED=$((HEALTH_CHECKS_FAILED + 1))
        VALIDATION_PASSED=false
    }
}

# Check Redis connectivity
check_redis() {
    log_step "Checking Redis connectivity..."
    
    python -c "
import redis
import os
r = redis.from_url(os.environ.get('REDIS_URL', 'redis://localhost:6379'))
r.ping()
print('Redis connected successfully')

# Test cache operations
r.set('deployment_test', 'success', ex=60)
value = r.get('deployment_test')
assert value == b'success', 'Cache test failed'
print('Cache operations working')
" 2>/dev/null && {
        log_info "✓ Redis connectivity verified"
        HEALTH_CHECKS_PASSED=$((HEALTH_CHECKS_PASSED + 1))
    } || {
        log_warning "Redis connectivity check failed (non-critical)"
        HEALTH_CHECKS_FAILED=$((HEALTH_CHECKS_FAILED + 1))
    }
}

# Check Celery workers
check_celery() {
    log_step "Checking Celery workers..."
    
    python -c "
from celery import Celery
import os

app = Celery('core')
app.config_from_object('django.conf:settings', namespace='CELERY')

# Check if workers are responding
from core.celery import app as celery_app
inspector = celery_app.control.inspect()
stats = inspector.stats()

if stats:
    worker_count = len(stats)
    print(f'Celery workers active: {worker_count}')
else:
    print('No Celery workers detected (may be normal in some deployments)')
" 2>/dev/null && {
        log_info "✓ Celery check completed"
        HEALTH_CHECKS_PASSED=$((HEALTH_CHECKS_PASSED + 1))
    } || {
        log_warning "Celery check failed (non-critical)"
    }
}

# Check critical endpoints
check_endpoints() {
    log_step "Checking critical endpoints..."
    
    local base_url="${BACKEND_URL:-http://localhost:8000}"
    local endpoints=(
        "/api/auth/login/"
        "/api/auth/register/"
        "/api/companies/"
        "/api/subscriptions/plans/"
    )
    
    for endpoint in "${endpoints[@]}"; do
        local url="${base_url}${endpoint}"
        local status_code=$(curl -s -o /dev/null -w "%{http_code}" "$url" 2>/dev/null || echo "000")
        
        if [[ "$status_code" == "200" ]] || [[ "$status_code" == "401" ]] || [[ "$status_code" == "405" ]]; then
            log_info "✓ Endpoint $endpoint is responding (HTTP $status_code)"
            HEALTH_CHECKS_PASSED=$((HEALTH_CHECKS_PASSED + 1))
        else
            log_warning "✗ Endpoint $endpoint returned HTTP $status_code"
            HEALTH_CHECKS_FAILED=$((HEALTH_CHECKS_FAILED + 1))
        fi
    done
}

# Send deployment notification
send_notification() {
    log_step "Sending deployment notification..."
    
    python -c "
import os
import json
from datetime import datetime

deployment_info = {
    'timestamp': datetime.utcnow().isoformat(),
    'environment': os.environ.get('RAILWAY_ENVIRONMENT', 'production'),
    'deployment_id': os.environ.get('RAILWAY_DEPLOYMENT_ID', 'unknown'),
    'git_commit': os.environ.get('GIT_COMMIT', 'unknown'),
    'health_checks_passed': $HEALTH_CHECKS_PASSED,
    'health_checks_failed': $HEALTH_CHECKS_FAILED,
    'status': 'success' if $VALIDATION_PASSED else 'failed'
}

# Log deployment info
print('Deployment Info:')
print(json.dumps(deployment_info, indent=2))

# Send to monitoring service if configured
if os.environ.get('SENTRY_DSN'):
    try:
        import sentry_sdk
        sentry_sdk.capture_message(
            f'Deployment completed: {deployment_info[\"status\"]}',
            level='info',
            extras=deployment_info
        )
        print('Notification sent to Sentry')
    except:
        pass

# Send webhook if configured
webhook_url = os.environ.get('DEPLOYMENT_WEBHOOK_URL')
if webhook_url:
    try:
        import requests
        response = requests.post(webhook_url, json=deployment_info, timeout=5)
        print(f'Webhook notification sent: {response.status_code}')
    except:
        pass
" || log_warning "Could not send deployment notification"
}

# Run smoke tests
run_smoke_tests() {
    log_step "Running smoke tests..."
    
    python -c "
import django
django.setup()

# Test user creation
from django.contrib.auth import get_user_model
User = get_user_model()
test_user = User.objects.create_user(
    username=f'smoketest_{os.urandom(4).hex()}',
    email='smoketest@example.com',
    password='testpass123'
)
print(f'✓ User creation test passed')

# Test basic queries
from apps.companies.models import Company
company_count = Company.objects.count()
print(f'✓ Database queries working ({company_count} companies)')

# Cleanup
test_user.delete()
print('✓ Smoke tests completed')
" 2>/dev/null && {
        log_info "✓ Smoke tests passed"
        HEALTH_CHECKS_PASSED=$((HEALTH_CHECKS_PASSED + 1))
    } || {
        log_warning "Smoke tests failed (non-critical)"
        HEALTH_CHECKS_FAILED=$((HEALTH_CHECKS_FAILED + 1))
    }
}

# Clean up old data
cleanup_old_data() {
    log_step "Cleaning up old data..."
    
    python -c "
import django
django.setup()
from datetime import datetime, timedelta

# Clean old sessions
from django.contrib.sessions.models import Session
old_sessions = Session.objects.filter(
    expire_date__lt=datetime.now()
).delete()
print(f'Cleaned {old_sessions[0]} old sessions')

# Clean old notifications
from apps.notifications.models import Notification
old_date = datetime.now() - timedelta(days=30)
old_notifications = Notification.objects.filter(
    created_at__lt=old_date,
    is_read=True
).delete()
print(f'Cleaned {old_notifications[0]} old notifications')
" 2>/dev/null || log_warning "Could not clean old data"
}

# Generate deployment report
generate_report() {
    log_step "Generating post-deployment report..."
    
    echo "======================================"
    echo "POST-DEPLOYMENT VALIDATION REPORT"
    echo "======================================"
    echo "Timestamp: $(date -u +"%Y-%m-%d %H:%M:%S UTC")"
    echo "Environment: ${RAILWAY_ENVIRONMENT:-production}"
    echo "Deployment ID: ${RAILWAY_DEPLOYMENT_ID:-unknown}"
    echo ""
    echo "HEALTH CHECKS:"
    echo "  Passed: $HEALTH_CHECKS_PASSED"
    echo "  Failed: $HEALTH_CHECKS_FAILED"
    echo ""
    
    if [ "$VALIDATION_PASSED" = true ]; then
        echo "RESULT: ✅ DEPLOYMENT SUCCESSFUL"
        echo ""
        echo "Next Steps:"
        echo "  1. Monitor application logs for any errors"
        echo "  2. Check key metrics in monitoring dashboard"
        echo "  3. Verify user-facing functionality"
        echo "  4. Review performance metrics"
    else
        echo "RESULT: ⚠️ DEPLOYMENT COMPLETED WITH ISSUES"
        echo ""
        echo "Action Required:"
        echo "  1. Review failed health checks"
        echo "  2. Check application logs for errors"
        echo "  3. Consider rollback if critical issues persist"
    fi
    
    echo "======================================"
}

# Main execution
main() {
    log_info "Starting post-deployment validation..."
    
    # Allow services to stabilize
    sleep 10
    
    # Run all checks
    check_app_health
    check_database
    check_redis
    check_celery
    check_endpoints
    run_smoke_tests
    cleanup_old_data
    send_notification
    
    # Generate report
    generate_report
    
    # Exit with appropriate code
    if [ "$VALIDATION_PASSED" = false ]; then
        log_warning "Post-deployment validation completed with issues"
        exit 1
    else
        log_info "Post-deployment validation completed successfully"
        exit 0
    fi
}

# Run main function
main