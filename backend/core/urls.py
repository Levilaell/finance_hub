"""
CaixaHub URL Configuration
"""
from django.contrib import admin
from django.urls import include, path
from apps.companies.health import health_check


urlpatterns = [
    path('admin/', admin.site.urls),

    # Health check for deployment platforms (multiple paths for compatibility)
    path('health/', health_check, name='health-check'),
    path('api/health/', health_check, name='api-health-check'),
    
    # API endpoints
    path('api/auth/', include('apps.authentication.urls')),
    path('api/companies/', include('apps.companies.urls')),
    path('api/banking/', include('apps.banking.urls')),
    path('api/reports/', include('apps.reports.urls')),
]

