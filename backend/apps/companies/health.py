"""
Health check endpoint for deployment monitoring
Improved version with better error handling and startup tolerance
"""
from django.http import JsonResponse
from django.db import connection
from django.conf import settings
import os
import logging
import traceback

logger = logging.getLogger(__name__)


def health_check(request):
    """
    Health check endpoint for Railway and other deployment platforms
    Designed to be resilient during startup
    """
    try:
        status = "healthy"
        checks = {}
        warnings = []
        
        # Basic environment check (always passes)
        checks["environment"] = os.environ.get("DJANGO_SETTINGS_MODULE", "unknown")
        checks["debug_mode"] = settings.DEBUG
        
        # Check for critical environment variables
        env_warnings = []
        if 'INSECURE-TEMPORARY-KEY' in getattr(settings, 'SECRET_KEY', ''):
            env_warnings.append("DJANGO_SECRET_KEY not set - using temporary key")
            warnings.append("DJANGO_SECRET_KEY environment variable must be set in Railway")
        
        db_url = os.environ.get('DATABASE_URL', '')
        if not db_url:
            env_warnings.append("DATABASE_URL not configured")
            warnings.append("DATABASE_URL environment variable must be set in Railway")
        elif '{{' in db_url:
            env_warnings.append("DATABASE_URL contains unresolved Railway template variables")
            warnings.append(f"DATABASE_URL has unresolved template: {db_url[:50]}...")
            warnings.append("Fix: In Railway dashboard, use the reference button to link to your database service")
        
        if env_warnings:
            checks["configuration"] = "incomplete"
            checks["missing_env_vars"] = env_warnings
        else:
            checks["configuration"] = "complete"
        
        # Database check with better error handling
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                checks["database"] = "healthy"
                
                # Check if critical tables exist
                cursor.execute("""
                    SELECT COUNT(*) FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name IN ('django_migrations', 'users', 'companies')
                """)
                table_count = cursor.fetchone()[0]
                
                if table_count < 3:
                    warnings.append(f"Only {table_count}/3 critical tables exist")
                    checks["database_tables"] = f"incomplete ({table_count}/3)"
                    # Don't fail health check during migrations
                    if os.environ.get("RAILWAY_ENVIRONMENT") == "production":
                        logger.warning(f"Missing critical tables during health check: {table_count}/3")
                else:
                    checks["database_tables"] = "complete"
                    
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Database health check failed: {error_msg}")
            
            # Check if this is a startup/migration issue
            if "does not exist" in error_msg or "no such table" in error_msg:
                checks["database"] = "initializing"
                warnings.append("Database tables being created")
                # Don't fail during initial setup
                if not os.environ.get("RAILWAY_DEPLOYMENT_ID"):
                    status = "unhealthy"
            else:
                checks["database"] = f"error: {error_msg[:100]}"
                status = "unhealthy"
        
        # Redis/Cache check (optional, don't fail if not configured)
        try:
            from django.core.cache import cache
            cache.set("health_check", "test", 1)
            test_value = cache.get("health_check")
            
            if test_value == "test":
                checks["cache"] = "healthy"
            else:
                checks["cache"] = "not configured"
                warnings.append("Cache not working but not required")
        except Exception as e:
            checks["cache"] = "not configured"
            # Cache is optional, don't fail health check
            if settings.DEBUG:
                warnings.append(f"Cache error (non-critical): {str(e)[:50]}")
        
        # Check for pending migrations (informational only)
        try:
            from django.core.management import call_command
            from io import StringIO
            
            out = StringIO()
            call_command('showmigrations', '--plan', '--verbosity', '0', stdout=out)
            output = out.getvalue()
            
            if '[ ]' in output:
                pending_count = output.count('[ ]')
                warnings.append(f"{pending_count} migrations pending")
                checks["migrations"] = f"{pending_count} pending"
            else:
                checks["migrations"] = "all applied"
        except Exception as e:
            # Don't fail on migration check errors
            checks["migrations"] = "unable to check"
            logger.warning(f"Could not check migrations: {e}")
        
        # Prepare response
        response_data = {
            "status": status,
            "checks": checks,
            "version": "1.1.0"
        }
        
        if warnings:
            response_data["warnings"] = warnings
        
        # Return appropriate status code
        if status == "healthy":
            return JsonResponse(response_data, status=200)
        else:
            # Return 503 Service Unavailable for unhealthy status
            return JsonResponse(response_data, status=503)
            
    except Exception as e:
        # Catch any unexpected errors in the health check itself
        logger.error(f"Health check unexpected error: {e}")
        logger.error(traceback.format_exc())
        
        return JsonResponse({
            "status": "error",
            "error": str(e),
            "error_type": type(e).__name__,
            "traceback": traceback.format_exc()[-500:],  # Last 500 chars of traceback
            "message": "Health check encountered an unexpected error"
        }, status=500)