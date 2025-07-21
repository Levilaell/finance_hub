"""
Reports app URLs
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    ReportViewSet,
    ReportTemplateViewSet,
    AIAnalysisViewSet,
    AIAnalysisTemplateViewSet,
    QuickReportsView,
    AnalyticsView,
    DashboardStatsView,
    CashFlowDataView,
    CategorySpendingView,
    IncomeVsExpensesView,
    AIInsightsView,
)

app_name = 'reports'

router = DefaultRouter()
router.register(r'reports', ReportViewSet, basename='report')
router.register(r'templates', ReportTemplateViewSet, basename='report-template')
router.register(r'ai-analyses', AIAnalysisViewSet, basename='ai-analysis')
router.register(r'ai-templates', AIAnalysisTemplateViewSet, basename='ai-analysis-template')

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
    
    # AI Insights
    path('ai-insights/', AIInsightsView.as_view(), name='ai-insights'),
]