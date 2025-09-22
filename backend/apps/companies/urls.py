"""
Simplified Companies URLs - Essential endpoints only
"""
from django.urls import path
from .views import (
    CompanyDetailView,
)

app_name = 'companies'

urlpatterns = [
    # Authenticated endpoints
    path('detail/', CompanyDetailView.as_view(), name='detail'),
]