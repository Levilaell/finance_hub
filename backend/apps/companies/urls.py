"""
Simplified Companies URLs - Essential endpoints only
"""
from django.urls import path
from .views import (
    SubscriptionPlansView,
    CompanyDetailView,
    UsageLimitsView,
    SubscriptionStatusView,
)

app_name = 'companies'

urlpatterns = [
    # Subscription plans (works for both public and authenticated)
    path('public/plans/', SubscriptionPlansView.as_view(), name='public-plans'),
    path('plans/', SubscriptionPlansView.as_view(), name='plans'),

    # Authenticated endpoints
    path('detail/', CompanyDetailView.as_view(), name='detail'),
    path('usage-limits/', UsageLimitsView.as_view(), name='usage-limits'),
    path('subscription-status/', SubscriptionStatusView.as_view(), name='subscription-status'),
]