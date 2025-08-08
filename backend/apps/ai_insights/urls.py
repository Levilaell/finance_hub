"""
AI Insights URL configuration
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    AICreditViewSet,
    AIConversationViewSet,
    AIMessageViewSet,
    AIInsightViewSet
)

app_name = 'ai_insights'

router = DefaultRouter()
router.register('credits', AICreditViewSet, basename='aicredit')
router.register('conversations', AIConversationViewSet, basename='aiconversation')
router.register('messages', AIMessageViewSet, basename='aimessage')
router.register('insights', AIInsightViewSet, basename='aiinsight')

urlpatterns = [
    path('', include(router.urls)),
]