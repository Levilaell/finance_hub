"""
Banking app Celery tasks
Asynchronous tasks for bank synchronization and processing
"""
import logging
from datetime import timedelta

from celery import shared_task
from django.utils import timezone
from apps.companies.models import Company

from .models import BankAccount
# Removed unused imports: BankingSyncService, FinancialInsightsService

logger = logging.getLogger(__name__)


# REMOVED DEPRECATED TASKS:
# - sync_bank_account: Not used anywhere, replaced by sync_pluggy_account
# - sync_all_company_accounts: Not used anywhere, replaced by sync_all_pluggy_accounts
# - periodic_account_sync: Replaced by sync_all_pluggy_accounts in Celery Beat
# - generate_financial_insights: Not used anywhere in the codebase


@shared_task
def cleanup_old_sync_logs():
   """
   Clean up old bank sync logs (keep last 30 days)
   """
   from .models import BankSync
   
   cutoff_date = timezone.now() - timedelta(days=30)
   
   deleted_count = BankSync.objects.filter(
       started_at__lt=cutoff_date
   ).delete()[0]
   
   logger.info(f"Cleaned up {deleted_count} old sync logs")
   
   return {
       'status': 'success',
       'deleted_count': deleted_count,
       'cutoff_date': cutoff_date.isoformat()
   }


@shared_task(bind=True, max_retries=3)
def sync_pluggy_account(self, account_id):
    """
    Async task to sync Pluggy account transactions
    
    Args:
        account_id: BankAccount ID to sync
    """
    import asyncio
    from .integrations.pluggy.sync_service import pluggy_sync_service
    
    try:
        account = BankAccount.objects.get(
            id=account_id,
            external_id__isnull=False  # Only Pluggy accounts
        )
        
        logger.info(f"🔄 Starting Celery sync for Pluggy account {account_id}")
        
        async def run_sync():
            return await pluggy_sync_service.sync_account_transactions(account)
        
        # Run async sync
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(run_sync())
        finally:
            loop.close()
        
        if result.get('status') == 'success':
            logger.info(f"✅ Pluggy account sync completed: {account} - {result.get('transactions', 0)} transactions")
            
            return {
                'status': 'success',
                'account_id': account_id,
                'transactions_synced': result.get('transactions', 0)
            }
        else:
            raise Exception(f"Sync failed: {result.get('error', 'Unknown error')}")
        
    except BankAccount.DoesNotExist:
        logger.error(f"❌ Bank account {account_id} not found")
        return {'status': 'error', 'message': 'Account not found'}
        
    except Exception as exc:
        logger.error(f"❌ Error syncing Pluggy account {account_id}: {exc}")
        
        # Retry with exponential backoff
        if self.request.retries < self.max_retries:
            raise self.retry(countdown=60 * (2 ** self.request.retries))
        
        return {'status': 'error', 'message': str(exc)}


@shared_task
def sync_all_pluggy_accounts():
    """
    Periodic task to sync all Pluggy accounts
    """
    import asyncio
    from .integrations.pluggy.sync_service import pluggy_sync_service
    
    try:
        logger.info("🔄 Starting periodic sync of all Pluggy accounts")
        
        async def run_sync():
            return await pluggy_sync_service.sync_all_accounts()
        
        # Run async sync
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(run_sync())
        finally:
            loop.close()
        
        logger.info(f"✅ Periodic Pluggy sync completed: {result}")
        
        return result
        
    except Exception as exc:
        logger.error(f"❌ Error in periodic Pluggy sync: {exc}")
        return {'status': 'error', 'message': str(exc)}


@shared_task
def notify_consent_renewal_required(account_id):
    """
    Send notification for consent renewal required
    """
    from django.core.mail import send_mail
    from django.conf import settings
    
    try:
        account = BankAccount.objects.get(id=account_id)
        user = account.company.owner
        
        send_mail(
            subject=f'⚠️ Renovação de Consentimento Necessária - {account.display_name}',
            message=f'''
            Olá {user.first_name},
            
            O consentimento Open Finance para sua conta {account.display_name} está expirando e precisa ser renovado.
            
            Por favor, acesse o sistema e reconecte sua conta para continuar sincronizando suas transações.
            
            Atenciosamente,
            Equipe CaixaHub
            ''',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )
        
        logger.info(f"Consent renewal notification sent for account {account_id}")
        return {'status': 'success', 'account_id': account_id}
        
    except BankAccount.DoesNotExist:
        logger.error(f"Account {account_id} not found")
        return {'status': 'error', 'message': 'Account not found'}
    except Exception as e:
        logger.error(f"Error sending consent renewal notification: {e}")
        return {'status': 'error', 'message': str(e)}


@shared_task
def check_and_renew_consents():
    """
    Runs daily via Celery Beat to check and renew consents
    """
    import asyncio
    from .integrations.pluggy.consent_service import check_and_renew_consents_task
    
    try:
        logger.info("🔄 Starting consent renewal check")
        
        # Run async task
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(check_and_renew_consents_task())
        finally:
            loop.close()
        
        logger.info(f"✅ Consent renewal check completed: {result}")
        return result
        
    except Exception as exc:
        logger.error(f"❌ Error in consent renewal check: {exc}")
        return {'status': 'error', 'message': str(exc)}


@shared_task
# REMOVED: renew_single_consent_task - Not used anywhere in the codebase