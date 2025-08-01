"""
Companies app URLs
"""
from django.urls import path

# Import main views from views.py
from .views import (
    SubscriptionPlansView,
    UpgradeSubscriptionView,
    CancelSubscriptionView,
    PaymentMethodsView,
    PaymentMethodDetailView,
    PaymentHistoryView,
    InvoiceDownloadView,
    UsageLimitsView,
)

# Import public views from views_package
from .views_package.public import PublicSubscriptionPlansView

app_name = 'companies'

urlpatterns = [
    # Public endpoints (no auth required)
    path('public/plans/', PublicSubscriptionPlansView.as_view(), name='public-subscription-plans'),
    
    # Subscription management
    path('subscription/plans/', SubscriptionPlansView.as_view(), name='subscription-plans'),
    path('subscription/upgrade/', UpgradeSubscriptionView.as_view(), name='subscription-upgrade'),
    path('subscription/cancel/', CancelSubscriptionView.as_view(), name='subscription-cancel'),
    
    # Billing and payment methods
    path('billing/payment-methods/', PaymentMethodsView.as_view(), name='payment-methods'),
    path('billing/payment-methods/<int:payment_method_id>/', PaymentMethodDetailView.as_view(), name='payment-method-detail'),
    path('billing/history/', PaymentHistoryView.as_view(), name='payment-history'),
    path('billing/invoices/<int:payment_id>/', InvoiceDownloadView.as_view(), name='invoice-download'),
    
    # Usage limits
    path('usage-limits/', UsageLimitsView.as_view(), name='usage-limits'),
]