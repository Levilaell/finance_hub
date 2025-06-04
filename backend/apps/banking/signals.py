"""
Banking app signals for automatic processing
"""
import json
from decimal import Decimal
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from apps.categories.services import AICategorizationService
from django.db.models import F
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from .models import BankAccount, Transaction


@receiver(post_save, sender=Transaction)
def process_new_transaction(sender, instance, created, **kwargs):
    """
    Process new transactions: categorize with AI and update account balance
    """
    if created:
        # Auto-categorize with AI if enabled
        if (instance.bank_account.company.enable_ai_categorization and 
            not instance.category and 
            not instance.is_ai_categorized):
            
            ai_service = AICategorizationService()
            ai_service.categorize_transaction(instance)
        
        # Update account balance if needed
        if instance.balance_after is None:
            # This would typically be handled by the banking sync
            pass
        
        # Send real-time notification to user
        send_transaction_notification(instance, 'created')
    else:
        # Transaction updated
        send_transaction_notification(instance, 'updated')


@receiver(pre_save, sender=BankAccount)
def update_primary_account(sender, instance, **kwargs):
    """
    Ensure only one primary account per company
    """
    if instance.is_primary:
        # Set all other accounts as non-primary
        BankAccount.objects.filter(
            company=instance.company,
            is_primary=True
        ).exclude(pk=instance.pk).update(is_primary=False)


@receiver(post_save, sender=BankAccount)
def send_balance_update(sender, instance, created, **kwargs):
    """
    Send real-time balance updates
    """
    if not created:  # Only for updates, not new accounts
        send_balance_notification(instance)


def send_transaction_notification(transaction, action):
    """
    Send real-time transaction notification via WebSocket
    """
    try:
        channel_layer = get_channel_layer()
        if not channel_layer:
            return
    except Exception:
        # Skip WebSocket notifications if Redis is not available
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
                    'account_number': transaction.bank_account.account_number[-4:],  # Last 4 digits only
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
    except Exception:
        # Skip if WebSocket/Redis is not available
        pass


def send_balance_notification(bank_account):
    """
    Send real-time balance update via WebSocket
    """
    try:
        channel_layer = get_channel_layer()
        if not channel_layer:
            return
    except Exception:
        # Skip WebSocket notifications if Redis is not available
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
                'account_number': bank_account.account_number[-4:],  # Last 4 digits only
                'current_balance': float(bank_account.current_balance),
                'is_primary': bank_account.is_primary,
            }
        }
    }
    
    # Send to company owner
    try:
        group_name = f"transactions_{user.id}"
        async_to_sync(channel_layer.group_send)(
            group_name,
            balance_data
        )
    except Exception:
        # Skip if WebSocket/Redis is not available
        pass