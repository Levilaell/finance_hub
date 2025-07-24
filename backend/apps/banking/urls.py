"""
Banking app URLs
"""
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views
from . import pluggy_views

app_name = 'banking'

# DRF Router for standard CRUD endpoints
router = DefaultRouter()
router.register(r'accounts', views.BankAccountViewSet, basename='bank-account')
router.register(r'transactions', views.TransactionViewSet, basename='transaction')
router.register(r'categories', views.TransactionCategoryViewSet, basename='category')
router.register(r'providers', views.BankProviderViewSet, basename='bank-provider')

urlpatterns = [
    # DRF Router URLs
    path('', include(router.urls)),
    
    # Dashboard endpoints
    path('dashboard/', views.DashboardView.as_view(), name='dashboard'),
    path('dashboard/enhanced/', views.EnhancedDashboardView.as_view(), name='enhanced-dashboard'),
    
    # Pluggy integration endpoints
    path('pluggy/connect-token/', pluggy_views.PluggyConnectTokenView.as_view(), name='pluggy-connect-token'),
    path('pluggy/banks/', pluggy_views.PluggyBanksView.as_view(), name='pluggy-banks'),
    path('pluggy/connectors/', pluggy_views.PluggyConnectorsView.as_view(), name='pluggy-connectors'),
    path('pluggy/callback/', pluggy_views.PluggyCallbackView.as_view(), name='pluggy-callback'),
    path('pluggy/accounts/<int:account_id>/status/', pluggy_views.PluggyAccountStatusView.as_view(), name='pluggy-account-status'),
    path('pluggy/accounts/<int:account_id>/sync/', pluggy_views.PluggyAccountSyncView.as_view(), name='pluggy-account-sync'),
    path('pluggy/webhook/', pluggy_views.PluggyWebhookView.as_view(), name='pluggy-webhook'),
]