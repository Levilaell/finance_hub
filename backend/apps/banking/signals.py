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


@receiver(pre_delete, sender=BankAccount)
def cleanup_account_data(sender, instance, **kwargs):
    """
    Cleanup when account is deleted
    """
    logger.info(f"Deleting account {instance.id} and related data")