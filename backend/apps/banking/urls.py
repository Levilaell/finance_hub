"""
Banking app URLs
"""
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

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
]