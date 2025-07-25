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
from .services import BankingSyncService, FinancialInsightsService

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def sync_bank_account(self, account_id, days_back=7):
    """
    DEPRECATED: Use sync_pluggy_account instead
    This uses the deprecated BankingSyncService
    """
    logger.warning(f"sync_bank_account is deprecated. Use sync_pluggy_account for account {account_id}")
    # Redirect to Pluggy sync
    return sync_pluggy_account.apply_async(args=[account_id])


@shared_task
def sync_all_company_accounts(company_id):
    """
    DEPRECATED: Use sync_all_pluggy_accounts instead
    This uses the deprecated BankingSyncService
    """
    logger.warning(f"sync_all_company_accounts is deprecated. Use sync_all_pluggy_accounts for company {company_id}")
    # Queue individual Pluggy syncs for each account
    try:
        company = Company.objects.get(id=company_id)
        accounts = BankAccount.objects.filter(
            company=company,
            is_active=True,
            external_id__isnull=False  # Only Pluggy accounts
        )
        
        results = []
        for account in accounts:
            task = sync_pluggy_account.delay(account.id)
            results.append({
                'account_id': account.id,
                'task_id': task.id
            })
        
        return {
            'status': 'success',
            'company_id': company_id,
            'queued_count': len(results)
        }
        
    except Company.DoesNotExist:
        logger.error(f"Company {company_id} not found")
        return {'status': 'error', 'message': 'Company not found'}


@shared_task
def periodic_account_sync():
    """
    DEPRECATED: Use sync_all_pluggy_accounts instead
    This task is replaced by Pluggy-specific sync
    """
    logger.warning("periodic_account_sync is deprecated. Use sync_all_pluggy_accounts instead")
    # Redirect to Pluggy sync
    return sync_all_pluggy_accounts.apply_async()


@shared_task
def generate_financial_insights(company_id):
    """
    Generate financial insights for a company
    
    Args:
        company_id: Company ID
    """
    try:
        company = Company.objects.get(id=company_id)
        insights_service = FinancialInsightsService()
        
        insights = insights_service.generate_insights(company)
        
        # Store insights in cache or database for dashboard
        # Implementation depends on your caching strategy
        
        logger.info(f"Financial insights generated for company: {company}")
        
        return {
            'status': 'success',
            'company_id': company_id,
            'insights': insights
        }
        
    except Company.DoesNotExist:
        logger.error(f"Company {company_id} not found")
        return {'status': 'error', 'message': 'Company not found'}
    
    except Exception as exc:
        logger.error(f"Error generating insights for company {company_id}: {exc}")
        return {'status': 'error', 'message': str(exc)}


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
def renew_single_consent_task(account_id):
    """
    Renew consent for a single account
    """
    import asyncio
    from .integrations.pluggy.consent_service import renew_single_consent_task as async_renew
    
    try:
        logger.info(f"🔄 Starting consent renewal for account {account_id}")
        
        # Run async task
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(async_renew(account_id))
        finally:
            loop.close()
        
        logger.info(f"✅ Consent renewal completed for account {account_id}: {result}")
        return result
        
    except Exception as exc:
        logger.error(f"❌ Error renewing consent for account {account_id}: {exc}")
        return {'status': 'error', 'message': str(exc)}