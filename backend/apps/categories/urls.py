"""
Categories app URLs
"""
from django.urls import path

app_name = 'categories'

# URLs removidas: CategoryRuleViewSet, CategorySuggestionViewSet, AITrainingDataViewSet
# Categorização agora é feita automaticamente pela Pluggy via pluggy_category_mapper.py

urlpatterns = [
    # Sem URLs - categorização automática via Pluggy
]