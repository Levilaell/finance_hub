"""
Core views for health checks and system status
"""
from django.http import JsonResponse, HttpResponse
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
    try:
        # Test database connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")

        response_data = {
            'status': 'healthy',
            'database': 'connected',
            'python_version': sys.version.split()[0],
        }

        return JsonResponse(response_data, status=200)
    except Exception as e:
        logger.error(f"Healthcheck failed: {e}")
        return JsonResponse({
            'status': 'unhealthy',
            'error': str(e),
        }, status=503)
