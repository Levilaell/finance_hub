"""
Categories app admin configuration
"""
from django.contrib import admin

# Admins removidos: CategoryRule, AITrainingData, CategorySuggestion, CategorizationLog
# Categorização agora é feita automaticamente pela Pluggy via pluggy_category_mapper.py