"""
Consent renewal service for Open Finance connections
"""
import logging
from datetime import timedelta
from typing import Dict, Any, List, Optional
from django.utils import timezone
from django.db import models

from ...models import BankAccount
from .client import PluggyClient, PluggyError

logger = logging.getLogger(__name__)


class ConsentRenewalService:
    """
    Service to handle automatic consent renewal for Open Finance connections
    """
    
    def __init__(self):
        self.pluggy_client = PluggyClient()
        self.renewal_threshold_days = 7  # Renew consents expiring in 7 days
    
    async def check_and_renew_consents(self) -> Dict[str, Any]:
        """
        Check all Open Finance consents and renew those expiring soon
        """
        logger.info("Starting consent renewal check")
        
        # Get accounts with Open Finance connections
        accounts = BankAccount.objects.filter(
            metadata__is_open_finance=True,
            pluggy_item_id__isnull=False,
            is_active=True
        )
        
        results = {
            'checked': 0,
            'renewed': 0,
            'failed': 0,
            'requires_user_action': 0
        }
        
        for account in accounts:
            try:
                result = await self.check_and_renew_consent(account)
                results['checked'] += 1
                
                if result['status'] == 'renewed':
                    results['renewed'] += 1
                elif result['status'] == 'requires_user_action':
                    results['requires_user_action'] += 1
                elif result['status'] == 'failed':
                    results['failed'] += 1
                    
            except Exception as e:
                logger.error(f"Error checking consent for account {account.id}: {e}")
                results['failed'] += 1
        
        logger.info(f"Consent renewal check completed: {results}")
        return results
    
    async def check_and_renew_consent(self, account: BankAccount) -> Dict[str, Any]:
        """
        Check and renew consent for a specific account
        """
        try:
            # Get item details
            item = self.pluggy_client.get_item(account.pluggy_item_id)
            
            # Check consent status
            consent_expires_at = item.get('consentExpiresAt')
            if not consent_expires_at:
                logger.warning(f"No consent expiration found for account {account.id}")
                return {'status': 'skipped', 'reason': 'no_consent_expiration'}
            
            # Parse expiration date
            expires_at = timezone.datetime.fromisoformat(consent_expires_at.replace('Z', '+00:00'))
            days_until_expiry = (expires_at - timezone.now()).days
            
            logger.info(f"Account {account.id} consent expires in {days_until_expiry} days")
            
            # Check if renewal is needed
            if days_until_expiry > self.renewal_threshold_days:
                return {
                    'status': 'valid',
                    'days_until_expiry': days_until_expiry
                }
            
            # Attempt renewal
            return await self.renew_consent(account)
            
        except Exception as e:
            logger.error(f"Error checking consent for account {account.id}: {e}")
            return {'status': 'failed', 'error': str(e)}
    
    async def renew_consent(self, account: BankAccount) -> Dict[str, Any]:
        """
        Attempt to renew consent for an account
        """
        try:
            logger.info(f"Attempting to renew consent for account {account.id}")
            
            # Try automatic renewal through update_item
            try:
                result = self.pluggy_client.update_item(account.pluggy_item_id)
                
                # Check if update triggered consent renewal
                updated_item = self.pluggy_client.get_item(account.pluggy_item_id)
                new_consent_expires = updated_item.get('consentExpiresAt')
                
                if new_consent_expires:
                    new_expires_at = timezone.datetime.fromisoformat(new_consent_expires.replace('Z', '+00:00'))
                    days_extended = (new_expires_at - timezone.now()).days
                    
                    if days_extended > 30:  # Consent was renewed
                        logger.info(f"Successfully renewed consent for account {account.id}")
                        
                        # Update account metadata
                        account.metadata['last_consent_renewal'] = timezone.now().isoformat()
                        account.metadata['consent_expires_at'] = new_consent_expires
                        account.save()
                        
                        return {
                            'status': 'renewed',
                            'new_expiry': new_consent_expires,
                            'days_extended': days_extended
                        }
                
            except PluggyError as e:
                if e.error_code in ['CONSENT_EXPIRED', 'USER_AUTHORIZATION_REVOKED']:
                    # Consent requires user action
                    pass
                else:
                    raise
            
            # If automatic renewal failed, mark for user action
            logger.warning(f"Consent renewal requires user action for account {account.id}")
            
            account.status = 'consent_renewal_required'
            account.sync_error_message = 'Consentimento Open Finance precisa ser renovado'
            account.metadata['consent_renewal_required'] = True
            account.save()
            
            # Schedule notification
            from ...tasks import notify_consent_renewal_required
            notify_consent_renewal_required.delay(account.id)
            
            return {
                'status': 'requires_user_action',
                'message': 'User needs to reconnect account to renew consent'
            }
            
        except Exception as e:
            logger.error(f"Failed to renew consent for account {account.id}: {e}")
            return {
                'status': 'failed',
                'error': str(e)
            }
    
    def get_accounts_requiring_renewal(self, days_threshold: int = None) -> List[BankAccount]:
        """
        Get list of accounts that need consent renewal
        """
        if days_threshold is None:
            days_threshold = self.renewal_threshold_days
            
        threshold_date = timezone.now() + timedelta(days=days_threshold)
        
        # Query accounts with expiring consents
        accounts = BankAccount.objects.filter(
            metadata__is_open_finance=True,
            pluggy_item_id__isnull=False,
            is_active=True
        )
        
        expiring_accounts = []
        
        for account in accounts:
            consent_expires_at = account.metadata.get('consent_expires_at')
            if consent_expires_at:
                try:
                    expires_at = timezone.datetime.fromisoformat(consent_expires_at.replace('Z', '+00:00'))
                    if expires_at <= threshold_date:
                        expiring_accounts.append(account)
                except Exception as e:
                    logger.warning(f"Invalid consent expiration date for account {account.id}: {e}")
        
        return expiring_accounts


# Task functions for Celery
async def check_and_renew_consents_task():
    """Task to check and renew consents"""
    service = ConsentRenewalService()
    return await service.check_and_renew_consents()


async def renew_single_consent_task(account_id: int):
    """Task to renew consent for a single account"""
    try:
        account = BankAccount.objects.get(id=account_id)
        service = ConsentRenewalService()
        return await service.renew_consent(account)
    except BankAccount.DoesNotExist:
        logger.error(f"Account {account_id} not found")
        return {'status': 'failed', 'error': 'Account not found'}