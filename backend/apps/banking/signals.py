"""
Banking app signals for automatic processing - PRODUCTION READY
"""
import json
import logging
from decimal import Decimal
from django.db.models import F
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.db import transaction as db_transaction
from django.conf import settings

from .models import BankAccount, Transaction

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Transaction)
def process_new_transaction(sender, instance, created, **kwargs):
    """Process new transaction for notifications and cache invalidation"""
    if created:
        try:
            # Log transaction creation
            logger.info(f"✅ Transaction created: {instance.description} - R$ {instance.amount}")
            
            # Check if category was provided by Pluggy
            if instance.category:
                logger.info(f"🏷️ Transaction already categorized by Pluggy: {instance.category.name}")
            else:
                logger.info(f"❓ Transaction without category - manual categorization needed")
            
            # Send real-time notification (WebSocket)
            send_transaction_notification(instance, 'created')
            
            # Update account balance cache
            from .cache_service import cache_service
            cache_service.invalidate_account_cache(instance.bank_account.id)
            
            # Invalidate dashboard cache for the company
            cache_service.invalidate_company_cache(instance.bank_account.company.id)
            
        except Exception as e:
            logger.error(f"❌ Error processing new transaction {instance.id}: {e}")
            # Don't raise exception to avoid breaking transaction creation


@receiver(pre_save, sender=BankAccount)
def update_primary_account(sender, instance, **kwargs):
    """
    Ensure only one primary account per company
    """
    if instance.is_primary:
        # Use transaction to ensure atomicity
        with db_transaction.atomic():
            # Set all other accounts as non-primary
            BankAccount.objects.filter(
                company=instance.company,
                is_primary=True
            ).exclude(pk=instance.pk).update(is_primary=False)


@receiver(post_save, sender=BankAccount)
def handle_account_save(sender, instance, created, **kwargs):
    """
    Handle account creation and updates
    """
    try:
        if created:
            logger.info(f"🏦 New bank account created: {instance.display_name}")
            
            # Send welcome notification
            from .notifications import send_account_connected_notification
            send_account_connected_notification(instance)
            
        else:
            # Send balance update notification
            send_balance_notification(instance)
            
        # Invalidate account cache
        from .cache_service import cache_service
        cache_service.invalidate_account_cache(instance.id)
        
    except Exception as e:
        logger.error(f"❌ Error in handle_account_save: {e}")


def send_transaction_notification(transaction, action):
    """
    Send real-time transaction notification via WebSocket
    """
    try:
        # Check if channels is available
        try:
            from channels.layers import get_channel_layer
            from asgiref.sync import async_to_sync
            channel_layer = get_channel_layer()
            if not channel_layer:
                return
        except ImportError:
            # Channels not installed, skip WebSocket notifications
            return
        
        # Get the company owner
        company = transaction.bank_account.company
        user = company.owner
        
        # Prepare transaction data
        transaction_data = {
            'type': 'transaction_update',
            'message': {
                'action': action,
                'transaction': {
                    'id': str(transaction.id),
                    'external_id': transaction.external_id,
                    'description': transaction.description,
                    'amount': float(transaction.amount),
                    'transaction_date': transaction.transaction_date.isoformat() if transaction.transaction_date else None,
                    'balance_after': float(transaction.balance_after) if transaction.balance_after else None,
                    'transaction_type': transaction.transaction_type,
                    'category': transaction.category.name if transaction.category else None,
                    'bank_account': {
                        'id': str(transaction.bank_account.id),
                        'display_name': transaction.bank_account.display_name,
                        'account_number': transaction.bank_account.masked_account,
                    }
                }
            }
        }
        
        # Send to company owner
        try:
            group_name = f"transactions_{user.id}"
            async_to_sync(channel_layer.group_send)(
                group_name,
                transaction_data
            )
            logger.debug(f"📨 Sent transaction notification to user {user.id}")
        except Exception as e:
            logger.warning(f"⚠️ Failed to send WebSocket notification: {e}")
            
    except Exception as e:
        logger.error(f"❌ Error in send_transaction_notification: {e}")


def send_balance_notification(bank_account):
    """
    Send real-time balance update via WebSocket
    """
    try:
        # Check if channels is available
        try:
            from channels.layers import get_channel_layer
            from asgiref.sync import async_to_sync
            channel_layer = get_channel_layer()
            if not channel_layer:
                return
        except ImportError:
            # Channels not installed, skip WebSocket notifications
            return
        
        # Get the company owner
        company = bank_account.company
        user = company.owner
        
        # Prepare balance data
        balance_data = {
            'type': 'balance_update',
            'message': {
                'bank_account': {
                    'id': str(bank_account.id),
                    'display_name': bank_account.display_name,
                    'account_number': bank_account.masked_account,
                    'current_balance': float(bank_account.current_balance),
                    'available_balance': float(bank_account.available_balance),
                    'is_primary': bank_account.is_primary,
                }
            }
        }
        
        # Send to company owner
        try:
            group_name = f"balances_{user.id}"
            async_to_sync(channel_layer.group_send)(
                group_name,
                balance_data
            )
            logger.debug(f"📨 Sent balance notification to user {user.id}")
        except Exception as e:
            logger.warning(f"⚠️ Failed to send WebSocket notification: {e}")
            
    except Exception as e:
        logger.error(f"❌ Error in send_balance_notification: {e}")



# REMOVED: detect_recurring_patterns signal
# RecurringPatternDetector was not implemented and detect_recurring_pattern task does not exist