"""
Custom managers for banking models
"""
from django.db import models
from django.db.models import Q


class ActiveTransactionManager(models.Manager):
    """
    Manager that filters out transactions from deleted or inactive accounts
    """
    
    def get_queryset(self):
        """Return only transactions from active accounts"""
        return super().get_queryset().filter(
            account__is_active=True,
            is_deleted=False
        ).exclude(
            account__item__status='DELETED'
        )
    
    def for_company(self, company):
        """Get active transactions for a specific company"""
        return self.get_queryset().filter(
            account__company=company
        )