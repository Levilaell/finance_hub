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
from django.contrib.auth import get_user_model

def seed_plans_temp(request):
    if request.GET.get('secret') != 'temp-seed-2025':
        return JsonResponse({'error': 'Unauthorized'})
    
    from django.core.management import call_command
    from io import StringIO
    
    out = StringIO()
    try:
        call_command('seed_plans', stdout=out)
        return JsonResponse({
            'success': True,
            'output': out.getvalue()
        })
    except Exception as e:
        return JsonResponse({
            'error': str(e)
        }, status=500)



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
            'categories': '/api/categories/',
            'reports': '/api/reports/',
            'notifications': '/api/notifications/',
            'payments': '/api/payments/',
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
            path('categories/', include('apps.categories.urls')),
            path('reports/', include('apps.reports.urls')),
            path('notifications/', include('apps.notifications.urls')),
            path('payments/', include('apps.payments.urls')),
        ])),
    ],
)

urlpatterns = [
    path('', api_root, name='api-root'),
    path('admin/', admin.site.urls),
    path('seed-plans-temp/', seed_plans_temp),

    # Health check for deployment platforms
    path('api/health/', health_check, name='health-check'),
    
    # API endpoints
    path('api/', api_root, name='api-root-detail'),
    path('api/auth/', include('apps.authentication.urls')),
    path('api/companies/', include('apps.companies.urls')),
    path('api/banking/', include('apps.banking.urls')),
    path('api/categories/', include('apps.categories.urls')),
    path('api/reports/', include('apps.reports.urls')),
    path('api/notifications/', include('apps.notifications.urls')),
    path('api/payments/', include('apps.payments.urls')),
    
    # API Documentation
    re_path(r'^swagger(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    re_path(r'^swagger/$', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    re_path(r'^redoc/$', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    
    # Debug toolbar
    import debug_toolbar
    urlpatterns = [
        path('__debug__/', include(debug_toolbar.urls)),
    ] + urlpatterns