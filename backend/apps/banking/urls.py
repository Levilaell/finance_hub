"""
Banking app URLs - Pluggy Integration
API endpoints following RESTful patterns
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    PluggyConnectorViewSet,
    PluggyItemViewSet,
    BankAccountViewSet,
    TransactionViewSet,
    TransactionCategoryViewSet,
    PluggyConnectView,
    PluggyCallbackView,
    AccountSyncView,
    DashboardView,
    PluggyWebhookView,
    CeleryHealthCheckView
)
from .webhooks import pluggy_webhook

app_name = 'banking'

# Create router
router = DefaultRouter()
router.register(r'connectors', PluggyConnectorViewSet, basename='connector')
router.register(r'items', PluggyItemViewSet, basename='item')
router.register(r'accounts', BankAccountViewSet, basename='account')
router.register(r'transactions', TransactionViewSet, basename='transaction')
router.register(r'categories', TransactionCategoryViewSet, basename='category')

# URL patterns
urlpatterns = [
    # Router URLs
    path('', include(router.urls)),
    
    # Pluggy Connect
    path('pluggy/connect-token/', PluggyConnectView.as_view(), name='pluggy-connect-token'),
    path('pluggy/callback/', PluggyCallbackView.as_view(), name='pluggy-callback'),
    
    # Account sync
    path('accounts/<uuid:account_id>/sync/', AccountSyncView.as_view(), name='account-sync'),
    
    # Dashboard
    path('dashboard/', DashboardView.as_view(), name='dashboard'),
    
    # Webhooks
    path('webhooks/pluggy/', pluggy_webhook, name='pluggy-webhook'),
    # Alternative webhook endpoint (for backward compatibility)
    path('webhooks/pluggy/v2/', PluggyWebhookView.as_view(), name='pluggy-webhook-v2'),
    
    # Health check
    path('health/celery/', CeleryHealthCheckView.as_view(), name='celery-health'),
    
    # Legacy endpoints for compatibility
    path('pluggy/banks/',o PluggyConnectorViewSet.as_view({'get': 'list'}), name='pluggy-banks'),
]