"""
Categories app URLs
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    CategoryRuleViewSet,
    CategorySuggestionViewSet,
    AITrainingDataViewSet,
    CategorizationAnalyticsView,
    BulkCategorizationView,
    RuleSuggestionsView,
    CategoryTrainingView,
)

app_name = 'categories'

router = DefaultRouter()
router.register(r'rules', CategoryRuleViewSet, basename='category-rule')
router.register(r'suggestions', CategorySuggestionViewSet, basename='category-suggestion')
router.register(r'training-data', AITrainingDataViewSet, basename='training-data')

urlpatterns = [
    path('', include(router.urls)),
    
    # Analytics and insights
    path('analytics/', CategorizationAnalyticsView.as_view(), name='categorization-analytics'),
    
    # Bulk operations
    path('bulk/', BulkCategorizationView.as_view(), name='bulk-categorization'),
    
    # Rule suggestions
    path('rule-suggestions/', RuleSuggestionsView.as_view(), name='rule-suggestions'),
    
    # AI training
    path('train/', CategoryTrainingView.as_view(), name='category-training'),
]