"""
Health check endpoint for deployment monitoring
"""
from django.http import JsonResponse
from django.db import connection
from django.conf import settings
import os


def health_check(request):
    """
    Health check endpoint for Railway and other deployment platforms
    """
    status = "healthy"
    checks = {}
    
    # Database check
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            checks["database"] = "healthy"
    except Exception as e:
        checks["database"] = f"error: {str(e)}"
        status = "unhealthy"
    
    # Redis check (if configured)
    try:
        from django.core.cache import cache
        cache.set("health_check", "test", 1)
        test_value = cache.get("health_check")
        if test_value == "test":
            checks["cache"] = "healthy"
        else:
            checks["cache"] = "error: cache test failed"
            status = "unhealthy"
    except Exception as e:
        checks["cache"] = f"error: {str(e)}"
        # Don't mark as unhealthy for cache issues in development
        if not settings.DEBUG:
            status = "unhealthy"
    
    # Environment checks
    checks["debug_mode"] = settings.DEBUG
    checks["environment"] = os.environ.get("DJANGO_SETTINGS_MODULE", "unknown")
    
    response_data = {
        "status": status,
        "checks": checks,
        "version": "1.0.0"
    }
    
    if status == "healthy":
        return JsonResponse(response_data, status=200)
    else:
        return JsonResponse(response_data, status=503)