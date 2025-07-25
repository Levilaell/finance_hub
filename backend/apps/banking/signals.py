"""
Banking app signals
"""
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
import logging

from .models import PluggyItem, BankAccount, Transaction

logger = logging.getLogger(__name__)


@receiver(post_save, sender=PluggyItem)
def handle_item_status_change(sender, instance, created, **kwargs):
    """
    Handle item status changes
    """
    if not created and instance.status in ['LOGIN_ERROR', 'OUTDATED', 'ERROR']:
        logger.warning(
            f"Item {instance.pluggy_id} needs attention: {instance.status} - {instance.error_message}"
        )


@receiver(post_save, sender=Transaction)
def auto_categorize_transaction(sender, instance, created, **kwargs):
    """
    Auto-categorize new transactions
    """
    if created and not instance.category:
        # TODO: Implement auto-categorization logic
        pass


@receiver(pre_delete, sender=BankAccount)
def cleanup_account_data(sender, instance, **kwargs):
    """
    Cleanup when account is deleted
    """
    logger.info(f"Deleting account {instance.id} and related data")