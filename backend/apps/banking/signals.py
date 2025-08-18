"""
Banking app signals with notification integration
"""
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from django.conf import settings
from django.contrib.auth import get_user_model
from decimal import Decimal
import logging

User = get_user_model()

from .models import PluggyItem, BankAccount, Transaction

logger = logging.getLogger(__name__)


@receiver(post_save, sender=PluggyItem)
def handle_item_status_change(sender, instance, created, **kwargs):
    """
    Handle item status changes and trigger notifications
    """
    try:
        from apps.notifications.services import handle_account_connected
        
        if created:
            # New account connected
            connector_name = instance.connector.name if hasattr(instance, 'connector') else 'Financial Institution'
            handle_account_connected(
                company=instance.company,
                account_name=connector_name
            )
            logger.info(f"Account connected notification sent for item {instance.pluggy_item_id}")
            
        elif not created and instance.status in ['LOGIN_ERROR', 'OUTDATED', 'ERROR']:
            # Account sync error
            from apps.notifications.services import handle_account_sync_failed
            
            connector_name = instance.connector.name if hasattr(instance, 'connector') else 'Financial Institution'
            error_message = instance.error_message or f'Connection error: {instance.status}'
            
            handle_account_sync_failed(
                company=instance.company,
                account_name=connector_name,
                error=error_message
            )
            logger.warning(
                f"Item {instance.pluggy_item_id} needs attention: {instance.status} - {instance.error_message}"
            )
    except Exception as e:
        logger.error(f"Failed to send notification for item status change: {e}")


@receiver(post_save, sender=Transaction)
def handle_transaction_events(sender, instance, created, **kwargs):
    """
    Handle transaction-related events including categorization and notifications
    """
    if created:
        # Auto-categorization is handled by the pluggy_category mapping
        # Category assignment happens during transaction sync
        
        # NOTE: Transaction usage counter is already incremented in Transaction.create_safe()
        # Do NOT increment here to avoid double counting
        # The signal was causing duplicate increments (issue fixed on 2025-08-12)
        
        # Check for large transaction notification
        try:
            from apps.notifications.services import handle_large_transaction
            
            # Get threshold from settings or use default
            large_transaction_threshold = getattr(
                settings, 
                'LARGE_TRANSACTION_THRESHOLD', 
                Decimal('5000.00')
            )
            
            if abs(instance.amount) >= large_transaction_threshold:
                handle_large_transaction(
                    company=instance.company,
                    user=None,  # Will broadcast to all users
                    amount=instance.amount,
                    description=instance.description or 'Transaction',
                    account_name=instance.account.name if instance.account else 'Account'
                )
                logger.info(f"Large transaction notification sent for transaction {instance.id}")
        except Exception as e:
            logger.error(f"Failed to send large transaction notification: {e}")


@receiver(post_save, sender=BankAccount)
def handle_account_balance_change(sender, instance, created, **kwargs):
    """
    Monitor account balance changes and trigger low balance notifications
    """
    if not created:
        try:
            from apps.notifications.services import NotificationService
            
            # Get threshold from settings or use default
            low_balance_threshold = getattr(
                settings,
                'LOW_BALANCE_THRESHOLD',
                Decimal('1000.00')
            )
            
            # Check if balance data is available and below threshold
            if (hasattr(instance, 'balance') and 
                instance.balance is not None and 
                instance.balance < low_balance_threshold):
                
                # Check if we should send notification (avoid spam)
                # Only send if balance just went below threshold
                old_balance = None
                if hasattr(instance, '_old_balance'):
                    old_balance = instance._old_balance
                
                if old_balance is None or (old_balance >= low_balance_threshold and instance.balance < low_balance_threshold):
                    from apps.notifications.services import handle_low_balance
                    
                    # Get all users for the company to notify them individually
                    users = User.objects.filter(company=instance.company, is_active=True)
                    for user in users:
                        handle_low_balance(
                            company=instance.company,
                            user=user,
                            account_name=instance.name,
                            balance=instance.balance,
                            threshold=low_balance_threshold
                        )
                    logger.info(f"Low balance notification sent for account {instance.id}")
        except Exception as e:
            logger.error(f"Failed to send low balance notification: {e}")


@receiver(pre_delete, sender=BankAccount)
def cleanup_account_data(sender, instance, **kwargs):
    """
    Cleanup when account is deleted
    """
    logger.info(f"Deleting account {instance.id} and related data")