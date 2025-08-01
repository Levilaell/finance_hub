"""
Simplified Companies URLs - Essential endpoints only
"""
from django.urls import path
from .views import (
    PublicSubscriptionPlansView,
    SubscriptionPlansView,
    CompanyDetailView,
    UsageLimitsView,
    SubscriptionStatusView,
)

app_name = 'companies'

urlpatterns = [
    # Public endpoints
    path('public/plans/', PublicSubscriptionPlansView.as_view(), name='public-plans'),
    
    # Authenticated endpoints
    path('plans/', SubscriptionPlansView.as_view(), name='plans'),
    path('detail/', CompanyDetailView.as_view(), name='detail'),
    path('usage-limits/', UsageLimitsView.as_view(), name='usage-limits'),
    path('subscription-status/', SubscriptionStatusView.as_view(), name='subscription-status'),
]