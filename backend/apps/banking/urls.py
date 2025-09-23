"""
Banking URLs
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    PluggyConnectorViewSet,
    PluggyItemViewSet,
    BankAccountViewSet,
    TransactionViewSet,
    TransactionCategoryViewSet,
    DashboardView,
    sync_categories,
    create_default_categories,
    banking_health,
    delete_item
)
from .webhooks import get_webhook_urls

app_name = 'banking'

# Create router for ViewSets
router = DefaultRouter()
router.register(r'connectors', PluggyConnectorViewSet, basename='connectors')
router.register(r'items', PluggyItemViewSet, basename='items')
router.register(r'accounts', BankAccountViewSet, basename='accounts')
router.register(r'transactions', TransactionViewSet, basename='transactions')
router.register(r'categories', TransactionCategoryViewSet, basename='categories')

urlpatterns = [
    # Router URLs
    path('', include(router.urls)),
    
    # Custom endpoints
    path('dashboard/', DashboardView.as_view(), name='dashboard'),
    path('sync/categories/', sync_categories, name='sync-categories'),
    path('categories/create-defaults/', create_default_categories, name='create-default-categories'),
    path('health/', banking_health, name='health'),
    path('items/<uuid:item_id>/delete/', delete_item, name='delete-item'),
    
    # Webhook endpoints
] + get_webhook_urls()