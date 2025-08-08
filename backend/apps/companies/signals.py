"""
Signal handlers for company-related events
"""
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone
from datetime import timedelta

from .models import Company, ResourceUsage


@receiver(post_save, sender=Company)
def ensure_resource_usage_exists(sender, instance, created, **kwargs):
    """
    Ensure ResourceUsage record exists for the current month when a company is created
    """
    if created or not hasattr(instance, '_skip_signal'):
        # Create ResourceUsage for current month
        ResourceUsage.get_or_create_current_month(instance)


@receiver(pre_save, sender=Company)
def sync_resource_usage_on_save(sender, instance, **kwargs):
    """
    Sync ResourceUsage when Company counters are updated
    """
    if instance.pk:  # Only for existing companies
        try:
            old_instance = Company.objects.get(pk=instance.pk)
            
            # Check if counters have changed
            if (old_instance.current_month_transactions != instance.current_month_transactions or
                old_instance.current_month_ai_requests != instance.current_month_ai_requests):
                
                # Get or create current month usage
                usage = ResourceUsage.get_or_create_current_month(instance)
                
                # Update counters in ResourceUsage
                usage.transactions_count = instance.current_month_transactions
                usage.ai_requests_count = instance.current_month_ai_requests
                usage.save(update_fields=['transactions_count', 'ai_requests_count'])
                
        except Company.DoesNotExist:
            pass


def reset_monthly_usage_for_all_companies():
    """
    Reset monthly usage counters for all companies
    Should be called by a scheduled task at the beginning of each month
    """
    now = timezone.now()
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    # Get companies that need reset
    companies_to_reset = Company.objects.filter(
        last_usage_reset__lt=month_start,
        is_active=True
    )
    
    for company in companies_to_reset:
        # Reset company counters
        company.reset_monthly_usage()
        
        # Create new ResourceUsage record for the new month
        ResourceUsage.get_or_create_current_month(company)