"""
Celery tasks for AI Insights async processing
"""
import logging
from typing import List, Dict, Any
from datetime import datetime, timedelta
from decimal import Decimal

from celery import shared_task
from django.utils import timezone
from django.db.models import Q, Sum
from django.db import models
from django.core.mail import send_mail
from django.conf import settings

from apps.companies.models import Company
from .models import AIInsight, AICredit, AICreditTransaction
from .services.ai_service import AIService
from .services.credit_service import CreditService
from .services.anomaly_detection import AnomalyDetectionService
from .services.cache_service import CacheService

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def generate_daily_insights(self, company_id: str):
    """
    Generate daily AI insights for a company
    Runs daily to analyze financial data and create actionable insights
    """
    try:
        logger.info(f"Starting daily insights generation for company {company_id}")
        
        company = Company.objects.get(id=company_id)
        ai_service = AIService()
        
        # Check if company has sufficient credits
        credit_service = CreditService()
        if not credit_service.has_sufficient_credits(company, 'analysis_basic'):
            logger.warning(f"Company {company_id} has insufficient credits for daily insights")
            return {
                'status': 'skipped',
                'reason': 'insufficient_credits',
                'company_id': str(company_id)
            }
        
        # Generate insights
        insights = ai_service.generate_automated_insights(company)
        
        # Debit credits
        credits_used = len(insights) * 3  # 3 credits per insight
        credit_service.debit_credits(
            company=company,
            amount=credits_used,
            description=f"Daily insights generation - {len(insights)} insights",
            metadata={
                'task': 'generate_daily_insights',
                'insights_count': len(insights)
            }
        )
        
        logger.info(f"Generated {len(insights)} insights for company {company_id}")
        
        # Send notification if high priority insights
        high_priority_insights = [i for i in insights if i.get('priority') in ['critical', 'high']]
        if high_priority_insights:
            send_insights_notification.delay(company_id, len(high_priority_insights))
        
        return {
            'status': 'success',
            'company_id': str(company_id),
            'insights_generated': len(insights),
            'credits_used': credits_used
        }
        
    except Company.DoesNotExist:
        logger.error(f"Company {company_id} not found")
        return {
            'status': 'error',
            'reason': 'company_not_found',
            'company_id': str(company_id)
        }
    except Exception as e:
        logger.error(f"Error generating insights for company {company_id}: {str(e)}", exc_info=True)
        self.retry(countdown=60 * 5)  # Retry in 5 minutes


@shared_task
def generate_all_company_insights():
    """
    Generate insights for all active companies
    Scheduled to run daily
    """
    logger.info("Starting insights generation for all companies")
    
    # Get all active companies with active subscriptions
    companies = Company.objects.filter(
        is_active=True,
        subscription__status='active'
    ).values_list('id', flat=True)
    
    results = []
    for company_id in companies:
        result = generate_daily_insights.delay(str(company_id))
        results.append(result.id)
    
    logger.info(f"Queued insights generation for {len(companies)} companies")
    return {
        'companies_processed': len(companies),
        'task_ids': results
    }


@shared_task
def reset_monthly_credits():
    """
    Reset monthly credits for all companies
    Runs on the 1st of each month
    """
    logger.info("Starting monthly credits reset")
    
    credit_service = CreditService()
    reset_count = 0
    
    # Get all companies with active subscriptions
    companies = Company.objects.filter(
        is_active=True,
        subscription__status='active'
    )
    
    for company in companies:
        try:
            # Check if it's time to reset (30 days since last reset)
            credit = AICredit.objects.filter(company=company).first()
            if credit and (timezone.now() - credit.last_reset).days >= 30:
                credit_service.add_monthly_credits(company)
                reset_count += 1
                logger.info(f"Reset credits for company {company.id}")
        except Exception as e:
            logger.error(f"Error resetting credits for company {company.id}: {str(e)}")
    
    logger.info(f"Monthly credits reset completed. Reset {reset_count} companies")
    return {
        'companies_reset': reset_count,
        'timestamp': timezone.now().isoformat()
    }


@shared_task
def cleanup_old_insights():
    """
    Clean up old insights that have expired or been dismissed
    Runs weekly
    """
    logger.info("Starting old insights cleanup")
    
    # Delete dismissed insights older than 30 days
    thirty_days_ago = timezone.now() - timedelta(days=30)
    dismissed_count = AIInsight.objects.filter(
        status='dismissed',
        created_at__lt=thirty_days_ago
    ).delete()[0]
    
    # Delete expired insights
    expired_count = AIInsight.objects.filter(
        expires_at__lt=timezone.now()
    ).delete()[0]
    
    # Archive completed insights older than 90 days
    ninety_days_ago = timezone.now() - timedelta(days=90)
    archived_count = AIInsight.objects.filter(
        status='completed',
        created_at__lt=ninety_days_ago
    ).update(status='archived')
    
    logger.info(f"Cleanup completed: {dismissed_count} dismissed, {expired_count} expired, {archived_count} archived")
    
    return {
        'dismissed_deleted': dismissed_count,
        'expired_deleted': expired_count,
        'completed_archived': archived_count
    }


@shared_task
def send_insights_notification(company_id: str, high_priority_count: int):
    """
    Send email notification about high priority insights
    """
    try:
        company = Company.objects.get(id=company_id)
        
        # Get company admins
        admins = company.users.filter(
            company_users__role__in=['admin', 'owner'],
            company_users__is_active=True
        )
        
        if not admins.exists():
            logger.warning(f"No admins found for company {company_id}")
            return
        
        # Prepare email
        subject = f"[CaixaHub] {high_priority_count} insights importantes para {company.name}"
        message = f"""
Olá,

O CaixaHub AI identificou {high_priority_count} insights de alta prioridade para sua empresa.

Estes insights podem ajudar você a:
- Economizar dinheiro
- Identificar riscos financeiros
- Melhorar o fluxo de caixa
- Otimizar suas operações

Acesse o painel de AI Insights para ver os detalhes e tomar ações:
{settings.FRONTEND_URL}/dashboard/ai-insights

Atenciosamente,
Equipe CaixaHub
        """
        
        # Send to all admins
        recipient_list = list(admins.values_list('email', flat=True))
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=recipient_list,
            fail_silently=False
        )
        
        logger.info(f"Sent insights notification to {len(recipient_list)} admins of company {company_id}")
        
    except Company.DoesNotExist:
        logger.error(f"Company {company_id} not found")
    except Exception as e:
        logger.error(f"Error sending notification: {str(e)}", exc_info=True)


@shared_task
def analyze_financial_anomalies(company_id: str):
    """
    Analyze financial transactions for anomalies using ML
    """
    try:
        logger.info(f"Starting anomaly analysis for company {company_id}")
        
        company = Company.objects.get(id=company_id)
        anomaly_service = AnomalyDetectionService()
        
        # Run advanced anomaly detection
        anomalies = anomaly_service.generate_automated_insights(company_id)
        
        if anomalies:
            # Create insights for anomalies
            created_insights = []
            for anomaly in anomalies[:5]:  # Top 5 anomalies
                insight = AIInsight.objects.create(
                    company=company,
                    type=anomaly.get('type', 'anomaly'),
                    priority=anomaly.get('priority', 'medium'),
                    title=anomaly.get('title', 'Anomalia detectada'),
                    description=anomaly.get('description', ''),
                    data_context=anomaly.get('data_context', {}),
                    potential_impact=anomaly.get('potential_impact'),
                    action_items=anomaly.get('action_items', [
                        'Verificar a transação nos detalhes bancários',
                        'Confirmar se foi autorizada',
                        'Investigar possível fraude se não reconhecida'
                    ]),
                    is_automated=True,
                    expires_at=timezone.now() + timedelta(days=30)
                )
                created_insights.append(insight)
            
            # Invalidate cache after creating new insights
            CacheService.invalidate_company_cache(company_id)
            
            logger.info(f"Created {len(created_insights)} anomaly insights for company {company_id}")
        
        return {
            'status': 'success',
            'company_id': str(company_id),
            'anomalies_found': len(anomalies),
            'insights_created': len(created_insights) if anomalies else 0
        }
        
    except Exception as e:
        logger.error(f"Error in anomaly analysis: {str(e)}", exc_info=True)
        return {
            'status': 'error',
            'company_id': str(company_id),
            'error': str(e)
        }


@shared_task
def generate_monthly_report_insights(company_id: str):
    """
    Generate comprehensive monthly insights report
    """
    try:
        logger.info(f"Generating monthly insights report for company {company_id}")
        
        company = Company.objects.get(id=company_id)
        ai_service = AIService()
        credit_service = CreditService()
        
        # Check credits (monthly report costs more)
        if not credit_service.has_sufficient_credits(company, 'report_generation'):
            logger.warning(f"Insufficient credits for monthly report - company {company_id}")
            return {
                'status': 'insufficient_credits',
                'company_id': str(company_id)
            }
        
        # Generate comprehensive monthly analysis
        report_data = ai_service.generate_monthly_report(company)
        
        # Create a special insight for the monthly report
        insight = AIInsight.objects.create(
            company=company,
            type='report',
            priority='medium',
            title=f"Relatório Mensal - {timezone.now().strftime('%B %Y')}",
            description="Análise completa do desempenho financeiro do mês",
            data_context=report_data,
            is_automated=True,
            action_items=report_data.get('recommendations', [])
        )
        
        # Debit credits
        credit_service.debit_credits(
            company=company,
            amount=10,  # Monthly report costs 10 credits
            description="Monthly insights report generation",
            metadata={
                'task': 'generate_monthly_report',
                'insight_id': str(insight.id)
            }
        )
        
        logger.info(f"Monthly report generated for company {company_id}")
        
        return {
            'status': 'success',
            'company_id': str(company_id),
            'insight_id': str(insight.id)
        }
        
    except Exception as e:
        logger.error(f"Error generating monthly report: {str(e)}", exc_info=True)
        return {
            'status': 'error',
            'company_id': str(company_id),
            'error': str(e)
        }


@shared_task
def sync_credit_usage_metrics():
    """
    Sync credit usage metrics for analytics
    Runs hourly
    """
    logger.info("Syncing credit usage metrics")
    
    # Calculate metrics for the last hour
    one_hour_ago = timezone.now() - timedelta(hours=1)
    
    # Get usage stats
    transactions = AICreditTransaction.objects.filter(
        created_at__gte=one_hour_ago,
        type='usage'
    )
    
    metrics = {
        'hourly_usage': transactions.count(),
        'credits_consumed': abs(transactions.aggregate(total=models.Sum('amount'))['total'] or 0),
        'unique_companies': transactions.values('company').distinct().count(),
        'timestamp': timezone.now().isoformat()
    }
    
    # Here you could send to monitoring service, cache, etc.
    logger.info(f"Credit usage metrics: {metrics}")
    
    return metrics


@shared_task
def warm_company_cache(company_id: str):
    """
    Pre-warm cache for company financial data
    Runs daily to improve response times
    """
    try:
        logger.info(f"Warming cache for company {company_id}")
        
        # Pre-warm main cache entries
        CacheService.warm_cache(company_id)
        
        logger.info(f"Cache warmed successfully for company {company_id}")
        
        return {
            'status': 'success',
            'company_id': str(company_id),
            'timestamp': timezone.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error warming cache for company {company_id}: {str(e)}", exc_info=True)
        return {
            'status': 'error',
            'company_id': str(company_id),
            'error': str(e)
        }


@shared_task
def warm_all_companies_cache():
    """
    Warm cache for all active companies
    Runs daily in off-peak hours
    """
    logger.info("Starting cache warming for all companies")
    
    companies = Company.objects.filter(
        is_active=True,
        subscription__status='active'
    ).values_list('id', flat=True)
    
    results = []
    for company_id in companies:
        result = warm_company_cache.delay(str(company_id))
        results.append(result.id)
    
    logger.info(f"Queued cache warming for {len(companies)} companies")
    return {
        'companies_processed': len(companies),
        'task_ids': results
    }