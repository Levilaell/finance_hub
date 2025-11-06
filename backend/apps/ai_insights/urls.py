"""
URLs for AI Insights API
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.ai_insights.views import AIInsightViewSet

router = DefaultRouter()
router.register(r'insights', AIInsightViewSet, basename='ai-insights')

urlpatterns = [
    path('', include(router.urls)),
]
