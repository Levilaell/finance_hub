"""
Test-specific URL Configuration (excludes ai_insights app)
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path
from apps.companies.health import health_check

def api_root(request):
    """API root endpoint for tests"""
    return JsonResponse({
        'message': 'CaixaHub API (Test)',
        'version': '1.0',
        'status': 'running',
        'endpoints': {
            'auth': '/api/auth/',
            'companies': '/api/companies/',
            'banking': '/api/banking/',
            'reports': '/api/reports/',
            'notifications': '/api/notifications/',
            'payments': '/api/payments/',
            'admin': '/admin/'
        }
    })

urlpatterns = [
    # Health check
    path('health/', health_check, name='health_check'),
    
    # API root
    path('api/', api_root, name='api_root'),
    
    # Main API endpoints (excluding ai_insights)
    path('api/auth/', include('apps.authentication.urls')),
    path('api/companies/', include('apps.companies.urls')),
    path('api/banking/', include('apps.banking.urls')),
    path('api/reports/', include('apps.reports.urls')),
    path('api/notifications/', include('apps.notifications.urls')),
    path('api/payments/', include('apps.payments.urls')),
    
    # Admin
    path('admin/', admin.site.urls),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)