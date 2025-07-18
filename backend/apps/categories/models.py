"""
Categories app models
AI-powered transaction categorization system
"""

from django.contrib.auth import get_user_model
from django.db import models
from django.utils.translation import gettext_lazy as _

User = get_user_model()

# Models removidos: CategoryRule, AITrainingData, CategorySuggestion, CategorizationLog
# Categorização agora é feita automaticamente pela Pluggy via pluggy_category_mapper.py