"""
Caixa Digital URL Configuration
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path, re_path
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import permissions


def api_root(request):
    """API root endpoint"""
    return JsonResponse({
        'message': 'Caixa Digital API',
        'version': '1.0',
        'status': 'running',
        'endpoints': {
            'auth': '/api/auth/',
            'companies': '/api/companies/',
            'banking': '/api/banking/',
            'categories': '/api/categories/',
            'reports': '/api/reports/',
            'notifications': '/api/notifications/',
            'documentation': '/swagger/',
            'admin': '/admin/'
        }
    })

# API Documentation
schema_view = get_schema_view(
    openapi.Info(
        title="Caixa Digital API",
        default_version='v1',
        description="API for financial management SaaS platform",
        terms_of_service="https://www.caixadigital.com.br/terms/",
        contact=openapi.Contact(email="api@caixadigital.com.br"),
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
        ])),
    ],
)

urlpatterns = [
    path('', api_root, name='api-root'),
    path('admin/', admin.site.urls),
    
    # API endpoints
    path('api/', api_root, name='api-root-detail'),
    path('api/auth/', include('apps.authentication.urls')),
    path('api/companies/', include('apps.companies.urls')),
    path('api/banking/', include('apps.banking.urls')),
    path('api/categories/', include('apps.categories.urls')),
    path('api/reports/', include('apps.reports.urls')),
    path('api/notifications/', include('apps.notifications.urls')),
    
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