"""
Signal handlers for company-related events
"""
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone
from datetime import timedelta

from .models import Company

# Usage tracking simplified - no external ResourceUsage model needed
# Company.current_month_transactions is tracked directly in the Company model