"""
URL configuration for Banking app.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    ConnectorViewSet,
    BankConnectionViewSet,
    BankAccountViewSet,
    TransactionViewSet,
    SyncLogViewSet
)
from .webhooks import pluggy_webhook_handler

app_name = 'banking'

# Create router for ViewSets
router = DefaultRouter()
router.register('connectors', ConnectorViewSet, basename='connector')
router.register('connections', BankConnectionViewSet, basename='connection')
router.register('accounts', BankAccountViewSet, basename='account')
router.register('transactions', TransactionViewSet, basename='transaction')
router.register('sync-logs', SyncLogViewSet, basename='synclog')

urlpatterns = [
    # API routes (no need for 'api/' prefix as it's already added in core/urls.py)
    path('', include(router.urls)),

    # Webhook endpoint
    path('webhooks/pluggy/', pluggy_webhook_handler, name='pluggy_webhook'),
]