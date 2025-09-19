"""
CaixaHub URL Configuration
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path, re_path
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import permissions
from apps.companies.health import health_check



def api_root(request):
    """API root endpoint"""
    return JsonResponse({
        'message': 'CaixaHub API',
        'version': '1.0',
        'status': 'running',
        'endpoints': {
            'auth': '/api/auth/',
            'companies': '/api/companies/',
            'banking': '/api/banking/',
            'reports': '/api/reports/',
            'notifications': '/api/notifications/',
            'payments': '/api/payments/',
            'ai_insights': '/api/ai-insights/',
            'documentation': '/swagger/',
            'admin': '/admin/'
        }
    })

# API Documentation
schema_view = get_schema_view(
    openapi.Info(
        title="CaixaHub API",
        default_version='v1',
        description="API for financial management SaaS platform",
        terms_of_service="https://www.caixahub.com.br/terms/",
        contact=openapi.Contact(email="api@caixahub.com.br"),
        license=openapi.License(name="Proprietary"),
    ),
    public=True,
    permission_classes=[permissions.AllowAny],
    patterns=[
        path('api/', include([
            path('auth/', include('apps.authentication.urls')),
            path('companies/', include('apps.companies.urls')),
            path('banking/', include('apps.banking.urls')),
            path('reports/', include('apps.reports.urls')),
            # path('payments/', include('apps.payments.urls')),
        ])),
    ],
)

urlpatterns = [
    path('', api_root, name='api-root'),
    path('admin/', admin.site.urls),

    # Health check for deployment platforms (multiple paths for compatibility)
    path('health/', health_check, name='health-check'),
    path('api/health/', health_check, name='api-health-check'),
    
    # API endpoints
    path('api/', api_root, name='api-root-detail'),
    path('api/auth/', include('apps.authentication.urls')),
    path('api/companies/', include('apps.companies.urls')),
    path('api/banking/', include('apps.banking.urls')),
    path('api/reports/', include('apps.reports.urls')),
    # path('api/payments/', include('apps.payments.urls')),
]

# Debug Toolbar (only in development)
if settings.DEBUG:
    import debug_toolbar
    urlpatterns = [
        path('__debug__/', include(debug_toolbar.urls)),
    ] + urlpatterns