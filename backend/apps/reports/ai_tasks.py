"""
AI-related Celery tasks for asynchronous processing
Add to: backend/apps/reports/ai_tasks.py
"""
from celery import shared_task
from django.utils import timezone
from django.core.cache import cache
from datetime import timedelta
import logging
from celery.schedules import crontab
from django.conf import settings



from apps.banking.models import Transaction, BankAccount
from apps.notifications.models import Notification
from .ai_service import enhanced_ai_service

logger = logging.getLogger(__name__)


@shared_task
def generate_daily_ai_insights():
    """
    Generate daily AI insights for all active companies
    Runs every day at 6 AM
    """
    from apps.companies.models import Company
    
    logger.info("Starting daily AI insights generation")
    
    active_companies = Company.objects.filter(
        is_active=True,
        subscription_plan__enable_ai_insights=True
    )
    
    for company in active_companies:
        try:
            generate_company_ai_insights.delay(company.id)
        except Exception as e:
            logger.error(f"Error queueing insights for company {company.id}: {e}")
    
    logger.info(f"Queued AI insights generation for {active_companies.count()} companies")


@shared_task
def generate_company_ai_insights(company_id: int, force_refresh: bool = False):
    """
    Generate AI insights for a specific company
    """
    from apps.companies.models import Company
    
    try:
        company = Company.objects.get(id=company_id)
        
        # Get company accounts
        accounts = BankAccount.objects.filter(company=company, is_active=True)
        
        if not accounts.exists():
            logger.info(f"No active accounts for company {company_id}")
            return
        
        # Get last 30 days of data
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=30)
        
        # Get transactions
        transactions = Transaction.objects.filter(
            bank_account__in=accounts,
            transaction_date__gte=start_date,
            transaction_date__lte=end_date
        )
        
        if not transactions.exists():
            logger.info(f"No transactions found for company {company_id}")
            return
        
        # Calculate financial metrics
        from apps.reports.views import AIInsightsView
        view = AIInsightsView()
        financial_data = view._calculate_financial_metrics(transactions, start_date, end_date)
        
        # Generate insights
        insights = enhanced_ai_service.generate_insights(
            financial_data,
            company_name=company.name,
            force_refresh=force_refresh
        )
        
        # Cache insights for quick access
        cache_key = f"ai_insights_latest_{company_id}"
        cache.set(cache_key, insights, 86400)  # 24 hours
        
        # Create notifications for important insights
        create_insight_notifications.delay(company_id, insights)
        
        logger.info(f"Successfully generated AI insights for company {company_id}")
        
        return insights
        
    except Exception as e:
        logger.error(f"Error generating insights for company {company_id}: {e}")
        raise


@shared_task
def create_insight_notifications(company_id: int, insights: dict):
    """
    Create notifications for important insights
    """
    from apps.companies.models import Company
    
    try:
        company = Company.objects.get(id=company_id)
        
        # Check for high priority alerts
        for alert in insights.get('alerts', []):
            if alert['severity'] == 'high':
                Notification.objects.create(
                    user=company.owner,
                    type='alert',
                    title=f"🚨 {alert['title']}",
                    message=alert['description'],
                    action_url='/reports?tab=insights',
                    metadata={'alert': alert}
                )
        
        # Check for high priority insights
        for insight in insights.get('insights', [])[:3]:  # Top 3 insights
            if insight.get('priority') == 'high' and insight.get('actionable'):
                Notification.objects.create(
                    user=company.owner,
                    type='insight',
                    title=f"💡 {insight['title']}",
                    message=insight['description'],
                    action_url='/reports?tab=insights',
                    metadata={'insight': insight}
                )
        
        # Weekly summary notification
        if timezone.now().weekday() == 0:  # Monday
            summary = insights.get('summary', {})
            Notification.objects.create(
                user=company.owner,
                type='summary',
                title="📊 Resumo Semanal com IA",
                message=f"Sua saúde financeira está {summary.get('overall_status', 'estável')}. {summary.get('key_message', '')}",
                action_url='/reports?tab=insights',
                metadata={'summary': summary}
            )
        
    except Exception as e:
        logger.error(f"Error creating notifications for company {company_id}: {e}")


@shared_task
def analyze_transaction_anomalies():
    """
    Analyze recent transactions for anomalies
    Runs every hour
    """
    from apps.banking.models import Transaction
    
    # Get transactions from last hour
    one_hour_ago = timezone.now() - timedelta(hours=1)
    
    recent_transactions = Transaction.objects.filter(
        created_at__gte=one_hour_ago,
        is_analyzed=False  # Assuming we add this field
    )
    
    for transaction in recent_transactions:
        try:
            analyze_single_transaction.delay(transaction.id)
        except Exception as e:
            logger.error(f"Error queueing transaction {transaction.id} for analysis: {e}")


@shared_task
def analyze_single_transaction(transaction_id: int):
    """
    Analyze a single transaction for anomalies
    """
    try:
        transaction = Transaction.objects.get(id=transaction_id)
        
        # Get account history for context
        account = transaction.bank_account
        historical_transactions = Transaction.objects.filter(
            bank_account=account,
            transaction_date__gte=timezone.now().date() - timedelta(days=90)
        ).exclude(id=transaction_id)
        
        # Prepare context
        avg_transaction = historical_transactions.aggregate(
            avg_amount=models.Avg('amount')
        )['avg_amount'] or 0
        
        context = {
            'average_transaction_amount': float(avg_transaction),
            'account_type': account.account_type,
            'company_name': account.company.name
        }
        
        transaction_data = {
            'amount': float(transaction.amount),
            'description': transaction.description,
            'category': transaction.category.name if transaction.category else None,
            'date': transaction.transaction_date.isoformat()
        }
        
        # Check if it's an anomaly
        is_anomaly = False
        
        # Simple rule: transaction is 3x larger than average
        if abs(transaction.amount) > abs(avg_transaction) * 3:
            is_anomaly = True
        
        # Large transactions (> R$ 10,000)
        if abs(transaction.amount) > 10000:
            is_anomaly = True
        
        if is_anomaly:
            # Get AI analysis
            analysis = enhanced_ai_service.analyze_anomaly(transaction_data, context)
            
            # Create alert if needed
            if analysis.get('risk_level') in ['high', 'medium']:
                Notification.objects.create(
                    user=account.company.owner,
                    type='anomaly',
                    title=f"⚠️ Transação Incomum Detectada",
                    message=f"{transaction.description}: {analysis.get('explanation', 'Verifique esta transação')}",
                    action_url=f'/transactions/{transaction.id}',
                    metadata={'analysis': analysis}
                )
        
        # Mark as analyzed
        transaction.is_analyzed = True
        transaction.save()
        
    except Exception as e:
        logger.error(f"Error analyzing transaction {transaction_id}: {e}")


@shared_task
def generate_weekly_ai_report():
    """
    Generate comprehensive weekly AI report for all companies
    Runs every Monday at 8 AM
    """
    from apps.companies.models import Company
    from apps.reports.models import Report
    
    logger.info("Starting weekly AI report generation")
    
    active_companies = Company.objects.filter(
        is_active=True,
        subscription_plan__enable_ai_reports=True
    )
    
    for company in active_companies:
        try:
            # Create report record
            report = Report.objects.create(
                company=company,
                report_type='ai_weekly_summary',
                title=f'Relatório Semanal com IA - {timezone.now().strftime("%d/%m/%Y")}',
                period_start=timezone.now().date() - timedelta(days=7),
                period_end=timezone.now().date(),
                created_by=company.owner
            )
            
            # Generate report content
            generate_ai_report_content.delay(report.id)
            
        except Exception as e:
            logger.error(f"Error creating weekly report for company {company.id}: {e}")


@shared_task
def generate_ai_report_content(report_id: int):
    """
    Generate AI-powered report content
    """
    from apps.reports.models import Report
    from apps.reports.report_generator import ReportGenerator
    
    try:
        report = Report.objects.get(id=report_id)
        
        # Get insights for the period
        insights = generate_company_ai_insights(
            report.company.id,
            force_refresh=True
        )
        
        # Generate enhanced report with AI insights
        generator = ReportGenerator(report.company)
        
        # This would be an enhanced version that includes AI insights
        # For now, using standard generator
        buffer = generator.generate_transaction_report(
            start_date=report.period_start,
            end_date=report.period_end,
            format=report.file_format or 'pdf',
            filters=report.parameters
        )
        
        # Save report
        filename = f"ai_report_{report.id}_{timezone.now().strftime('%Y%m%d')}.pdf"
        report.file.save(filename, ContentFile(buffer.getvalue()))
        report.is_generated = True
        report.save()
        
        # Send email notification
        send_ai_report_email.delay(report.id)
        
    except Exception as e:
        logger.error(f"Error generating AI report content for report {report_id}: {e}")
        report.error_message = str(e)
        report.save()


@shared_task
def send_ai_report_email(report_id: int):
    """
    Send AI report via email
    """
    from apps.reports.models import Report
    from apps.notifications.email_service import EmailService
    
    try:
        report = Report.objects.get(id=report_id)
        
        # Get latest insights
        cache_key = f"ai_insights_latest_{report.company.id}"
        insights = cache.get(cache_key, {})
        
        # Prepare email content
        summary = insights.get('summary', {})
        top_insights = insights.get('insights', [])[:3]
        
        EmailService.send_ai_report_email(
            user=report.company.owner,
            report=report,
            summary=summary,
            top_insights=top_insights
        )
        
    except Exception as e:
        logger.error(f"Error sending AI report email for report {report_id}: {e}")


@shared_task
def refresh_ai_insights_cache():
    """
    Refresh AI insights cache for all companies
    Runs every 6 hours
    """
    from apps.companies.models import Company
    
    companies = Company.objects.filter(
        is_active=True,
        subscription_plan__enable_ai_insights=True
    )
    
    for company in companies:
        # Check if cache is about to expire
        cache_key = f"ai_insights_latest_{company.id}"
        if not cache.get(cache_key):
            generate_company_ai_insights.delay(company.id, force_refresh=True)


# Add to Celery Beat Schedule
CELERY_BEAT_SCHEDULE = {
    'generate-daily-ai-insights': {
        'task': 'apps.reports.ai_tasks.generate_daily_ai_insights',
        'schedule': crontab(hour=6, minute=0),  # 6 AM daily
    },
    'analyze-transaction-anomalies': {
        'task': 'apps.reports.ai_tasks.analyze_transaction_anomalies',
        'schedule': crontab(minute=0),  # Every hour
    },
    'generate-weekly-ai-report': {
        'task': 'apps.reports.ai_tasks.generate_weekly_ai_report',
        'schedule': crontab(hour=8, minute=0, day_of_week=1),  # Monday 8 AM
    },
    'refresh-ai-insights-cache': {
        'task': 'apps.reports.ai_tasks.refresh_ai_insights_cache',
        'schedule': crontab(minute=0, hour='*/6'),  # Every 6 hours
    },
}