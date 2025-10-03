"""
Core views for health checks and system status
"""
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.db import connection
import sys
import logging

logger = logging.getLogger(__name__)


@csrf_exempt
@require_http_methods(["GET", "HEAD"])
def health_check(request):
    """
    Health check endpoint for Railway deployment monitoring.
    Returns 200 OK when the application is healthy.
    """
    # Log every healthcheck request for debugging
    logger.info(f"Healthcheck requested from {request.META.get('REMOTE_ADDR')} - Host: {request.get_host()}")
    print(f"🏥 HEALTHCHECK: {request.method} /health/ from {request.META.get('REMOTE_ADDR')}")

    try:
        # Test database connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")

        response_data = {
            'status': 'healthy',
            'database': 'connected',
            'python_version': sys.version.split()[0],
        }

        print(f"✅ HEALTHCHECK OK: {response_data}")
        return JsonResponse(response_data, status=200)
    except Exception as e:
        error_data = {
            'status': 'unhealthy',
            'error': str(e),
        }
        print(f"❌ HEALTHCHECK FAILED: {error_data}")
        logger.error(f"Healthcheck failed: {e}")
        return JsonResponse(error_data, status=503)
