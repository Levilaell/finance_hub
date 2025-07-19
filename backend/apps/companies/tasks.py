"""
Celery tasks for companies app
"""
import logging
from celery import shared_task
from django.utils import timezone
from django.db.models import Count
from django.core.management import call_command
from .models import Company, ResourceUsage
from apps.banking.models import Transaction
import calendar

logger = logging.getLogger(__name__)


@shared_task(bind=True)
def reset_monthly_usage(self):
    """
    Reset monthly usage counters for all companies on the 1st of each month
    """
    try:
        companies = Company.objects.filter(is_active=True)
        updated_count = 0
        
        for company in companies:
            company.reset_monthly_usage()
            updated_count += 1
            logger.info(f"Reset monthly usage for company {company.name} (ID: {company.id})")
        
        logger.info(f"Monthly usage reset completed for {updated_count} companies")
        return f"Reset completed for {updated_count} companies"
        
    except Exception as e:
        logger.error(f"Error resetting monthly usage: {str(e)}")
        raise self.retry(exc=e, countdown=60, max_retries=3)


@shared_task(bind=True)
def verify_usage_counters(self):
    """
    Verifica e corrige discrepâncias nos contadores de uso
    Executa diariamente para garantir precisão dos dados
    """
    try:
        # Data atual
        now = timezone.now()
        current_month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        last_day = calendar.monthrange(now.year, now.month)[1]
        current_month_end = now.replace(day=last_day, hour=23, minute=59, second=59, microsecond=999999)
        
        companies = Company.objects.filter(is_active=True)
        corrected_companies = []
        
        for company in companies:
            # Contar transações reais
            real_transactions = Transaction.objects.filter(
                bank_account__company=company,
                transaction_date__gte=current_month_start,
                transaction_date__lte=current_month_end
            ).count()
            
            current_counter = company.current_month_transactions or 0
            
            # Se houver discrepância, corrigir
            if real_transactions != current_counter:
                logger.warning(
                    f"Counter mismatch for {company.name}: "
                    f"real={real_transactions}, counter={current_counter}"
                )
                
                # Atualizar contador
                company.current_month_transactions = real_transactions
                company.save(update_fields=['current_month_transactions'])
                
                # Atualizar ResourceUsage
                resource_usage = ResourceUsage.get_or_create_current_month(company)
                resource_usage.transactions_count = real_transactions
                resource_usage.save(update_fields=['transactions_count'])
                
                corrected_companies.append({
                    'company': company.name,
                    'old_counter': current_counter,
                    'new_counter': real_transactions,
                    'difference': real_transactions - current_counter
                })
        
        if corrected_companies:
            logger.info(f"Corrected usage counters for {len(corrected_companies)} companies")
            for correction in corrected_companies:
                logger.info(
                    f"  {correction['company']}: "
                    f"{correction['old_counter']} → {correction['new_counter']} "
                    f"(diff: {correction['difference']})"
                )
        else:
            logger.info("All usage counters are accurate")
        
        return {
            'status': 'completed',
            'corrected_count': len(corrected_companies),
            'corrections': corrected_companies
        }
        
    except Exception as e:
        logger.error(f"Error verifying usage counters: {str(e)}")
        raise self.retry(exc=e, countdown=60, max_retries=3)


@shared_task(bind=True)
def send_usage_notifications(self):
    """
    Envia notificações de uso quando próximo dos limites
    """
    try:
        companies = Company.objects.filter(
            is_active=True,
            subscription_plan__isnull=False
        )
        
        notifications_sent = 0
        
        for company in companies:
            # Verificar transações
            usage_percentage = company.get_usage_percentage('transactions')
            
            # Notificação de 90%
            if usage_percentage >= 90 and not company.notified_90_percent:
                try:
                    from apps.notifications.email_service import EmailService
                    EmailService.send_usage_limit_warning(
                        email=company.owner.email,
                        company_name=company.name,
                        limit_type='transações',
                        percentage=90,
                        current=company.current_month_transactions,
                        limit=company.subscription_plan.max_transactions
                    )
                    company.notified_90_percent = True
                    company.save(update_fields=['notified_90_percent'])
                    notifications_sent += 1
                    logger.info(f"Sent 90% usage warning to {company.name}")
                except Exception as e:
                    logger.error(f"Error sending 90% notification to {company.name}: {e}")
            
            # Notificação de 80%
            elif usage_percentage >= 80 and not company.notified_80_percent:
                try:
                    from apps.notifications.email_service import EmailService
                    EmailService.send_usage_limit_warning(
                        email=company.owner.email,
                        company_name=company.name,
                        limit_type='transações',
                        percentage=80,
                        current=company.current_month_transactions,
                        limit=company.subscription_plan.max_transactions
                    )
                    company.notified_80_percent = True
                    company.save(update_fields=['notified_80_percent'])
                    notifications_sent += 1
                    logger.info(f"Sent 80% usage warning to {company.name}")
                except Exception as e:
                    logger.error(f"Error sending 80% notification to {company.name}: {e}")
        
        logger.info(f"Usage notifications completed. Sent {notifications_sent} notifications")
        return f"Sent {notifications_sent} notifications"
        
    except Exception as e:
        logger.error(f"Error sending usage notifications: {str(e)}")
        raise self.retry(exc=e, countdown=60, max_retries=3)