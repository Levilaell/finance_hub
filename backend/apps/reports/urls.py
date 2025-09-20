"""
Reports app URLs
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    ReportViewSet,
    ReportTemplateViewSet,
    QuickReportsView,
    AnalyticsView,
    DashboardStatsView,
    CashFlowDataView,
    CategorySpendingView,
    IncomeVsExpensesView,
    SecureReportDownloadView,
)

app_name = 'reports'

router = DefaultRouter()
router.register(r'reports', ReportViewSet, basename='report')
router.register(r'templates', ReportTemplateViewSet, basename='report-template')

urlpatterns = [
    # ViewSet routes
    path('', include(router.urls)),
    
    # Quick reports
    path('quick/', QuickReportsView.as_view(), name='quick-reports'),
    
    # Analytics
    path('analytics/', AnalyticsView.as_view(), name='analytics'),
    
    # Dashboard endpoints
    path('dashboard/stats/', DashboardStatsView.as_view(), name='dashboard-stats'),
    path('dashboard/cash-flow/', CashFlowDataView.as_view(), name='cash-flow-data'),
    path('dashboard/category-spending/', CategorySpendingView.as_view(), name='category-spending'),
    path('dashboard/income-vs-expenses/', IncomeVsExpensesView.as_view(), name='income-vs-expenses'),
    
    # Secure download endpoint
    path('secure-download/<str:signed_id>/', SecureReportDownloadView.as_view(), name='secure-download'),
    
    # AI Insights
]