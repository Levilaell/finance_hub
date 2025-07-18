"""
Categories app views
AI categorization management and analytics
"""
from rest_framework import permissions
from rest_framework.views import APIView
from rest_framework.response import Response

# Views removidas: CategoryRuleViewSet, AITrainingDataViewSet, CategorySuggestionViewSet, CategorizationLogViewSet
# Categorização agora é feita automaticamente pela Pluggy via pluggy_category_mapper.py