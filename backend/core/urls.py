"""
CaixaHub URL Configuration
"""
from django.contrib import admin
from django.urls import include, path
from django.http import JsonResponse


def health_check(request):
    return JsonResponse({"status": "ok"})


urlpatterns = [
    path('admin/', admin.site.urls),
    path('health/', health_check, name='health'),

    # API endpoints
    path('api/auth/', include('apps.authentication.urls')),
    path('api/companies/', include('apps.companies.urls')),
    path('api/banking/', include('apps.banking.urls')),
    path('api/subscriptions/', include('apps.subscriptions.urls')),
]