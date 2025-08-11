#!/bin/bash
# Automated rollback script for Railway deployments

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

# Track rollback state
ROLLBACK_SUCCESSFUL=false
HEALTH_CHECK_PASSED=false

# Check Railway CLI
check_railway_cli() {
    if ! command -v railway &> /dev/null; then
        log_error "Railway CLI is not installed!"
        echo "Install it with: npm install -g @railway/cli"
        exit 1
    fi
}

# Get deployment history
get_deployment_history() {
    log_step "Fetching deployment history..."
    
    railway deployments list --json > deployments.json 2>/dev/null || {
        log_error "Failed to fetch deployment history"
        exit 1
    }
    
    # Parse and display recent deployments
    python3 -c "
import json
import sys
from datetime import datetime

try:
    with open('deployments.json', 'r') as f:
        deployments = json.load(f)
    
    print('\nRecent Deployments:')
    print('-' * 80)
    print(f'{'#':<3} {'ID':<12} {'Status':<10} {'Service':<15} {'Time':<20} {'Commit':<8}')
    print('-' * 80)
    
    for i, deploy in enumerate(deployments[:10]):
        deploy_id = deploy.get('id', 'N/A')[:12]
        status = deploy.get('status', 'unknown')
        service = deploy.get('service', 'unknown')[:15]
        timestamp = deploy.get('createdAt', '')
        commit = deploy.get('commitHash', 'N/A')[:8]
        
        # Format timestamp
        if timestamp:
            try:
                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                time_str = dt.strftime('%Y-%m-%d %H:%M')
            except:
                time_str = timestamp[:19]
        else:
            time_str = 'N/A'
        
        # Color code status
        if status == 'success':
            status_str = '\033[32m' + status + '\033[0m'
        elif status == 'failed':
            status_str = '\033[31m' + status + '\033[0m'
        else:
            status_str = '\033[33m' + status + '\033[0m'
        
        print(f'{i+1:<3} {deploy_id:<12} {status_str:<19} {service:<15} {time_str:<20} {commit:<8}')
    
    print('-' * 80)
except Exception as e:
    print(f'Error parsing deployments: {e}')
    sys.exit(1)
"
}

# Select deployment to rollback to
select_deployment() {
    echo ""
    read -p "Enter deployment number to rollback to (or 'p' for previous): " selection
    
    if [ "$selection" = "p" ]; then
        DEPLOYMENT_ID="previous"
    elif [[ "$selection" =~ ^[0-9]+$ ]]; then
        # Extract deployment ID from the list
        DEPLOYMENT_ID=$(python3 -c "
import json
with open('deployments.json', 'r') as f:
    deployments = json.load(f)
index = int('$selection') - 1
if 0 <= index < len(deployments):
    print(deployments[index].get('id', ''))
")
        if [ -z "$DEPLOYMENT_ID" ]; then
            log_error "Invalid deployment selection"
            exit 1
        fi
    else
        log_error "Invalid selection"
        exit 1
    fi
    
    log_info "Selected deployment: $DEPLOYMENT_ID"
}

# Get rollback reason
get_rollback_reason() {
    echo ""
    echo "Common rollback reasons:"
    echo "1) Critical bug in production"
    echo "2) Performance degradation"
    echo "3) Breaking API changes"
    echo "4) Database migration issues"
    echo "5) Security vulnerability"
    echo "6) Other"
    
    read -p "Select reason (1-6): " reason_num
    
    case $reason_num in
        1) ROLLBACK_REASON="Critical bug in production" ;;
        2) ROLLBACK_REASON="Performance degradation" ;;
        3) ROLLBACK_REASON="Breaking API changes" ;;
        4) ROLLBACK_REASON="Database migration issues" ;;
        5) ROLLBACK_REASON="Security vulnerability" ;;
        6) 
            read -p "Enter custom reason: " ROLLBACK_REASON
            ;;
        *)
            log_error "Invalid selection"
            exit 1
            ;;
    esac
    
    log_info "Rollback reason: $ROLLBACK_REASON"
}

# Create backup before rollback
create_backup() {
    log_step "Creating backup of current state..."
    
    # Save current configuration
    railway variables > current_variables.txt 2>/dev/null || true
    railway status > current_status.txt 2>/dev/null || true
    
    # Create backup metadata
    cat > rollback_backup.json <<EOF
{
    "timestamp": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
    "reason": "$ROLLBACK_REASON",
    "initiated_by": "$USER",
    "from_deployment": "current",
    "to_deployment": "$DEPLOYMENT_ID"
}
EOF
    
    log_info "Backup created: rollback_backup.json"
}

# Perform the rollback
perform_rollback() {
    log_step "Performing rollback..."
    
    if [ "$DEPLOYMENT_ID" = "previous" ]; then
        log_info "Rolling back to previous deployment..."
        railway rollback || {
            log_error "Rollback failed!"
            return 1
        }
    else
        log_info "Rolling back to deployment: $DEPLOYMENT_ID"
        railway rollback --deployment-id "$DEPLOYMENT_ID" || {
            log_error "Rollback failed!"
            return 1
        }
    fi
    
    ROLLBACK_SUCCESSFUL=true
    log_info "Rollback command executed successfully"
}

# Wait for services to stabilize
wait_for_stabilization() {
    log_step "Waiting for services to stabilize..."
    
    local wait_time=60
    log_info "Waiting ${wait_time} seconds for deployment to complete..."
    
    for i in $(seq $wait_time -1 1); do
        echo -ne "\r${CYAN}[WAIT]${NC} Time remaining: ${i}s  "
        sleep 1
    done
    echo ""
}

# Perform health checks
perform_health_checks() {
    log_step "Performing health checks..."
    
    # Get service URLs from environment or ask user
    if [ -z "$BACKEND_URL" ]; then
        read -p "Enter backend URL: " BACKEND_URL
    fi
    
    if [ -z "$FRONTEND_URL" ]; then
        read -p "Enter frontend URL: " FRONTEND_URL
    fi
    
    # Check backend health
    log_info "Checking backend health..."
    if curl -f -s -o /dev/null -w "%{http_code}" "$BACKEND_URL/api/health/" | grep -q "200"; then
        log_info "✅ Backend health check passed"
    else
        log_error "❌ Backend health check failed"
        HEALTH_CHECK_PASSED=false
        return 1
    fi
    
    # Check frontend health
    log_info "Checking frontend health..."
    if curl -f -s -o /dev/null -w "%{http_code}" "$FRONTEND_URL" | grep -qE "200|304"; then
        log_info "✅ Frontend health check passed"
    else
        log_error "❌ Frontend health check failed"
        HEALTH_CHECK_PASSED=false
        return 1
    fi
    
    # Check critical endpoints
    log_info "Checking critical endpoints..."
    local endpoints=(
        "$BACKEND_URL/api/auth/login/"
        "$BACKEND_URL/api/subscriptions/plans/"
    )
    
    for endpoint in "${endpoints[@]}"; do
        if curl -f -s -o /dev/null -w "%{http_code}" "$endpoint" | grep -qE "200|401|405"; then
            log_info "✅ Endpoint check passed: $endpoint"
        else
            log_warning "⚠️  Endpoint check failed: $endpoint"
        fi
    done
    
    HEALTH_CHECK_PASSED=true
}

# Generate rollback report
generate_report() {
    log_step "Generating rollback report..."
    
    local report_file="rollback_report_$(date +%Y%m%d_%H%M%S).md"
    
    cat > "$report_file" <<EOF
# Rollback Report

## Summary
- **Date**: $(date -u +"%Y-%m-%d %H:%M:%S UTC")
- **Initiated By**: $USER
- **Environment**: Production
- **Reason**: $ROLLBACK_REASON
- **Target Deployment**: $DEPLOYMENT_ID
- **Status**: $([ "$ROLLBACK_SUCCESSFUL" = true ] && echo "✅ Success" || echo "❌ Failed")
- **Health Checks**: $([ "$HEALTH_CHECK_PASSED" = true ] && echo "✅ Passed" || echo "❌ Failed")

## Actions Taken
1. Created backup of current state
2. Initiated rollback to $DEPLOYMENT_ID
3. Waited for service stabilization
4. Performed health checks

## Health Check Results
- Backend: $([ "$HEALTH_CHECK_PASSED" = true ] && echo "✅ Operational" || echo "❌ Issues detected")
- Frontend: $([ "$HEALTH_CHECK_PASSED" = true ] && echo "✅ Operational" || echo "❌ Issues detected")

## Next Steps
$(if [ "$ROLLBACK_SUCCESSFUL" = true ] && [ "$HEALTH_CHECK_PASSED" = true ]; then
    echo "1. Monitor application metrics for stability"
    echo "2. Investigate root cause of the issue"
    echo "3. Prepare fix for the identified problem"
    echo "4. Plan forward deployment with fixes"
else
    echo "1. **URGENT**: Manual intervention required"
    echo "2. Check Railway dashboard for deployment status"
    echo "3. Review application logs for errors"
    echo "4. Consider emergency procedures if service is down"
fi)

## Files Generated
- rollback_backup.json
- current_variables.txt
- current_status.txt
- deployments.json

---
*Generated by rollback.sh*
EOF
    
    log_info "Report generated: $report_file"
    cat "$report_file"
}

# Cleanup temporary files
cleanup() {
    log_step "Cleaning up temporary files..."
    rm -f deployments.json 2>/dev/null || true
    log_info "Cleanup completed"
}

# Main execution
main() {
    echo "======================================"
    echo "   Railway Deployment Rollback Tool   "
    echo "======================================"
    echo ""
    
    # Check prerequisites
    check_railway_cli
    
    # Authenticate with Railway
    log_step "Authenticating with Railway..."
    railway link || {
        log_error "Failed to link Railway project"
        exit 1
    }
    
    # Get and display deployment history
    get_deployment_history
    
    # Select deployment to rollback to
    select_deployment
    
    # Get rollback reason
    get_rollback_reason
    
    # Confirm rollback
    echo ""
    echo -e "${YELLOW}⚠️  WARNING: You are about to rollback the production deployment${NC}"
    echo "Target: $DEPLOYMENT_ID"
    echo "Reason: $ROLLBACK_REASON"
    echo ""
    read -p "Are you sure you want to proceed? (yes/no): " confirm
    
    if [ "$confirm" != "yes" ]; then
        log_info "Rollback cancelled"
        exit 0
    fi
    
    # Perform rollback steps
    create_backup
    perform_rollback
    wait_for_stabilization
    perform_health_checks
    
    # Generate report
    generate_report
    
    # Cleanup
    cleanup
    
    # Final status
    echo ""
    echo "======================================"
    if [ "$ROLLBACK_SUCCESSFUL" = true ] && [ "$HEALTH_CHECK_PASSED" = true ]; then
        echo -e "${GREEN}✅ ROLLBACK COMPLETED SUCCESSFULLY${NC}"
    else
        echo -e "${RED}❌ ROLLBACK COMPLETED WITH ISSUES${NC}"
        echo "Please check the report and take necessary actions"
    fi
    echo "======================================"
}

# Run main function
main