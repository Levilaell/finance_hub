#!/bin/bash
# Pre-deployment validation and preparation script

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() {
    echo -e "${GREEN}[PRE-DEPLOY]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[PRE-DEPLOY]${NC} $1"
}

log_error() {
    echo -e "${RED}[PRE-DEPLOY]${NC} $1"
}

log_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

# Track validation results
VALIDATION_PASSED=true
WARNINGS=()
ERRORS=()

# Validate environment variables
validate_environment() {
    log_step "Validating environment variables..."
    
    # Required variables
    REQUIRED_VARS=(
        "DATABASE_URL"
        "DJANGO_SECRET_KEY"
        "REDIS_URL"
    )
    
    for var in "${REQUIRED_VARS[@]}"; do
        if [ -z "${!var}" ]; then
            ERRORS+=("Missing required environment variable: $var")
            VALIDATION_PASSED=false
        else
            log_info "✓ $var is set"
        fi
    done
    
    # Recommended variables
    RECOMMENDED_VARS=(
        "SENTRY_DSN"
        "ALLOWED_HOSTS"
        "CORS_ALLOWED_ORIGINS"
        "OPENAI_API_KEY"
        "STRIPE_SECRET_KEY"
        "PLUGGY_CLIENT_ID"
    )
    
    for var in "${RECOMMENDED_VARS[@]}"; do
        if [ -z "${!var}" ]; then
            WARNINGS+=("Missing recommended environment variable: $var")
        else
            log_info "✓ $var is set"
        fi
    done
}

# Check Python dependencies
check_dependencies() {
    log_step "Checking Python dependencies..."
    
    # Check for security vulnerabilities
    if command -v safety &> /dev/null; then
        log_info "Running security audit..."
        safety check --json 2>/dev/null || {
            WARNINGS+=("Security vulnerabilities found in dependencies")
        }
    else
        log_warning "Safety not installed, skipping security audit"
    fi
    
    # Check for outdated packages
    pip list --outdated --format=json | python -c "
import sys, json
outdated = json.load(sys.stdin)
if outdated:
    print(f'Found {len(outdated)} outdated packages')
    for pkg in outdated[:5]:  # Show first 5
        print(f'  - {pkg[\"name\"]}: {pkg[\"version\"]} → {pkg[\"latest_version\"]}')
" || true
}

# Validate Django configuration
validate_django() {
    log_step "Validating Django configuration..."
    
    # Check Django settings
    python manage.py check --deploy 2>&1 | while IFS= read -r line; do
        if [[ "$line" == *"CRITICAL"* ]] || [[ "$line" == *"ERROR"* ]]; then
            ERRORS+=("Django check: $line")
            VALIDATION_PASSED=false
        elif [[ "$line" == *"WARNING"* ]]; then
            WARNINGS+=("Django check: $line")
        fi
    done || true
    
    # Validate database connection
    python -c "
import django
django.setup()
from django.db import connection
with connection.cursor() as cursor:
    cursor.execute('SELECT 1')
print('Database connection successful')
" 2>/dev/null || {
        ERRORS+=("Database connection failed")
        VALIDATION_PASSED=false
    }
    
    # Check migrations
    python manage.py showmigrations --list | grep -q "\[ \]" && {
        WARNINGS+=("Unapplied migrations detected")
    } || {
        log_info "✓ All migrations applied"
    }
}

# Check static files
check_static_files() {
    log_step "Checking static files..."
    
    # Verify static files can be collected
    python manage.py collectstatic --check --dry-run --no-input 2>&1 | grep -q "0 static files" && {
        WARNINGS+=("No static files found")
    } || {
        log_info "✓ Static files ready"
    }
}

# Check disk space
check_disk_space() {
    log_step "Checking disk space..."
    
    # Get available space in MB
    AVAILABLE_SPACE=$(df /app 2>/dev/null | awk 'NR==2 {print int($4/1024)}' || echo "1000")
    
    if [ "$AVAILABLE_SPACE" -lt 100 ]; then
        ERRORS+=("Insufficient disk space: ${AVAILABLE_SPACE}MB available")
        VALIDATION_PASSED=false
    elif [ "$AVAILABLE_SPACE" -lt 500 ]; then
        WARNINGS+=("Low disk space: ${AVAILABLE_SPACE}MB available")
    else
        log_info "✓ Disk space: ${AVAILABLE_SPACE}MB available"
    fi
}

# Create backup point
create_backup_point() {
    log_step "Creating backup point..."
    
    # Store current deployment info
    cat > /tmp/deployment_info.json <<EOF
{
    "timestamp": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
    "git_commit": "${GIT_COMMIT:-unknown}",
    "railway_deployment_id": "${RAILWAY_DEPLOYMENT_ID:-unknown}",
    "environment": "${RAILWAY_ENVIRONMENT:-production}"
}
EOF
    
    log_info "✓ Backup point created"
}

# Generate deployment report
generate_report() {
    log_step "Generating pre-deployment report..."
    
    echo "======================================"
    echo "PRE-DEPLOYMENT VALIDATION REPORT"
    echo "======================================"
    echo "Timestamp: $(date -u +"%Y-%m-%d %H:%M:%S UTC")"
    echo "Environment: ${RAILWAY_ENVIRONMENT:-production}"
    echo "Deployment ID: ${RAILWAY_DEPLOYMENT_ID:-unknown}"
    echo ""
    
    if [ ${#ERRORS[@]} -gt 0 ]; then
        echo "ERRORS (${#ERRORS[@]}):"
        for error in "${ERRORS[@]}"; do
            echo "  ✗ $error"
        done
        echo ""
    fi
    
    if [ ${#WARNINGS[@]} -gt 0 ]; then
        echo "WARNINGS (${#WARNINGS[@]}):"
        for warning in "${WARNINGS[@]}"; do
            echo "  ⚠ $warning"
        done
        echo ""
    fi
    
    if [ "$VALIDATION_PASSED" = true ]; then
        echo "RESULT: ✅ VALIDATION PASSED"
        if [ ${#WARNINGS[@]} -gt 0 ]; then
            echo "Note: Deployment can proceed with warnings"
        fi
    else
        echo "RESULT: ❌ VALIDATION FAILED"
        echo "Deployment should not proceed"
    fi
    
    echo "======================================"
}

# Main execution
main() {
    log_info "Starting pre-deployment validation..."
    
    # Run all validation checks
    validate_environment
    check_dependencies
    validate_django
    check_static_files
    check_disk_space
    create_backup_point
    
    # Generate report
    generate_report
    
    # Exit with appropriate code
    if [ "$VALIDATION_PASSED" = false ]; then
        log_error "Pre-deployment validation failed!"
        exit 1
    else
        log_info "Pre-deployment validation completed successfully"
        exit 0
    fi
}

# Run main function
main