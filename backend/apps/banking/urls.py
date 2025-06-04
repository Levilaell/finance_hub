"""
Banking app URLs
"""
from django.urls import include, path
from rest_framework.routers import DefaultRouter
from django.conf import settings

from . import views
from .pluggy_views import (
    PluggyBankProvidersView, PluggyConnectTokenView, PluggyItemCallbackView,
    PluggySyncAccountView, pluggy_webhook, PluggyDisconnectAccountView,
    PluggyAccountStatusView
)
try:
    from . import belvo_views
    BELVO_ENABLED = True
except ImportError:
    BELVO_ENABLED = False

# Only import sandbox views in DEBUG mode
if settings.DEBUG:
    from .sandbox_views import (
        sandbox_status, sandbox_authorization_endpoint, 
        sandbox_token_endpoint, sandbox_accounts_endpoint, 
        sandbox_transactions_endpoint
    )

app_name = 'banking'

router = DefaultRouter()
router.register(r'accounts', views.BankAccountViewSet, basename='bank-account')
router.register(r'transactions', views.TransactionViewSet, basename='transaction')
router.register(r'categories', views.TransactionCategoryViewSet, basename='category')
router.register(r'providers', views.BankProviderViewSet, basename='bank-provider')
router.register(r'budgets', views.BudgetViewSet, basename='budget')
router.register(r'goals', views.FinancialGoalViewSet, basename='financial-goal')

urlpatterns = [
    path('', include(router.urls)),
    path('dashboard/', views.DashboardView.as_view(), name='dashboard'),
    path('dashboard/enhanced/', views.EnhancedDashboardView.as_view(), name='enhanced-dashboard'),
    path('analytics/time-series/', views.TimeSeriesAnalyticsView.as_view(), name='time-series'),
    path('analytics/expense-trends/', views.ExpenseTrendsView.as_view(), name='expense-trends'),
    path('sync/<int:account_id>/', views.SyncBankAccountView.as_view(), name='sync-account'),
    path('connect/', views.ConnectBankAccountView.as_view(), name='connect-account'),
    path('oauth/callback/', views.OpenBankingCallbackView.as_view(), name='oauth-callback'),
    path('refresh-token/<int:account_id>/', views.RefreshTokenView.as_view(), name='refresh-token'),
    
    # Pluggy integration endpoints
    path('pluggy/banks/', PluggyBankProvidersView.as_view(), name='pluggy-banks'),
    path('pluggy/connect-token/', PluggyConnectTokenView.as_view(), name='pluggy-connect-token'),
    path('pluggy/callback/', PluggyItemCallbackView.as_view(), name='pluggy-callback'),
    path('pluggy/accounts/<int:account_id>/sync/', PluggySyncAccountView.as_view(), name='pluggy-sync'),
    path('pluggy/accounts/<int:account_id>/disconnect/', PluggyDisconnectAccountView.as_view(), name='pluggy-disconnect'),
    path('pluggy/accounts/<int:account_id>/status/', PluggyAccountStatusView.as_view(), name='pluggy-status'),
    path('pluggy/webhook/', pluggy_webhook, name='pluggy-webhook'),
]

# Add sandbox endpoints only in DEBUG mode
if settings.DEBUG:
    urlpatterns += [
        # Sandbox endpoints for realistic testing
        path('sandbox/status/', sandbox_status, name='sandbox-status'),
        path('sandbox/<str:bank_code>/oauth/authorize/', sandbox_authorization_endpoint, name='sandbox-auth'),
        path('sandbox/<str:bank_code>/oauth/token/', sandbox_token_endpoint, name='sandbox-token'),
        path('sandbox/<str:bank_code>/accounts/', sandbox_accounts_endpoint, name='sandbox-accounts'),
        path('sandbox/<str:bank_code>/accounts/<str:account_id>/transactions/', sandbox_transactions_endpoint, name='sandbox-transactions'),
    ]

# Add Belvo URLs if available
if BELVO_ENABLED:
    urlpatterns += [
        # Belvo integration endpoints
        path('belvo/institutions/', belvo_views.belvo_institutions, name='belvo-institutions'),
        path('belvo/connections/', belvo_views.BelvoConnectionView.as_view(), name='belvo-connections'),
        path('belvo/connections/<uuid:connection_id>/', belvo_views.BelvoConnectionView.as_view(), name='belvo-connection-detail'),
        path('belvo/connections/<uuid:connection_id>/refresh/', belvo_views.belvo_refresh_connection, name='belvo-refresh'),
        path('belvo/accounts/', belvo_views.BelvoAccountsView.as_view(), name='belvo-accounts'),
        path('belvo/transactions/', belvo_views.BelvoTransactionsView.as_view(), name='belvo-transactions'),
    ]