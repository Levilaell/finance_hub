"""
Banking app URLs - Clean version with only Pluggy official integration
"""
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views
from .pluggy_views import (
    PluggyBankProvidersView, PluggyConnectTokenView, PluggyItemCallbackView,
    PluggySyncAccountView, pluggy_webhook, PluggyDisconnectAccountView,
    PluggyAccountStatusView, PluggyReconnectAccountView
)

app_name = 'banking'

# DRF Router for standard CRUD endpoints
router = DefaultRouter()
router.register(r'accounts', views.BankAccountViewSet, basename='bank-account')
router.register(r'transactions', views.TransactionViewSet, basename='transaction')
router.register(r'categories', views.TransactionCategoryViewSet, basename='category')
router.register(r'providers', views.BankProviderViewSet, basename='bank-provider')
'''
router.register(r'goals', views.FinancialGoalViewSet, basename='financial-goal')
'''
urlpatterns = [
    # DRF Router URLs
    path('', include(router.urls)),
    
    # Dashboard endpoints (keep only the ones being used)
    path('dashboard/', views.DashboardView.as_view(), name='dashboard'),
    path('dashboard/enhanced/', views.EnhancedDashboardView.as_view(), name='enhanced-dashboard'),
    
    # ===== PLUGGY INTEGRATION (Official Sandbox + Production) =====
    
    # Bank discovery
    path('pluggy/banks/', PluggyBankProvidersView.as_view(), name='pluggy-banks'),
    
    # Connection flow
    path('pluggy/connect-token/', PluggyConnectTokenView.as_view(), name='pluggy-connect-token'),
    path('pluggy/callback/', PluggyItemCallbackView.as_view(), name='pluggy-callback'),
    
    # Account management
    path('pluggy/accounts/<int:account_id>/sync/', PluggySyncAccountView.as_view(), name='pluggy-sync'),
    path('pluggy/accounts/<int:account_id>/disconnect/', PluggyDisconnectAccountView.as_view(), name='pluggy-disconnect'),
    path('pluggy/accounts/<int:account_id>/status/', PluggyAccountStatusView.as_view(), name='pluggy-status'),
    path('pluggy/accounts/<int:account_id>/reconnect/', PluggyReconnectAccountView.as_view(), name='pluggy-reconnect'),
    
    # Webhooks
    path('pluggy/webhook/', pluggy_webhook, name='pluggy-webhook'),
]