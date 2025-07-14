"""
Celery tasks for subscription and billing maintenance
"""
from celery import shared_task
from django.utils import timezone
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)


@shared_task
def check_trial_expirations():
    """
    Check for trial expirations and send notifications
    Runs daily at 9 AM
    """
    from apps.payments.payment_service import PaymentService
    
    payment_service = PaymentService()
    payment_service.check_trial_expiration()
    
    logger.info("Trial expiration check completed")


@shared_task
def reset_monthly_usage_counters():
    """
    Reset monthly usage counters for all companies
    Runs on the 1st of each month at midnight
    """
    from apps.companies.models import Company
    
    companies = Company.objects.filter(
        is_active=True,
        subscription_status__in=['active', 'trial']
    )
    
    for company in companies:
        company.reset_monthly_usage()
    
    logger.info(f"Reset usage counters for {companies.count()} companies")


@shared_task
def process_subscription_renewals():
    """
    Process subscription renewals and charge customers
    Runs daily at 2 AM
    """
    from apps.companies.models import Company
    from apps.payments.payment_service import PaymentService
    
    today = timezone.now().date()
    
    # Find companies with renewals due today
    companies_to_renew = Company.objects.filter(
        subscription_status='active',
        next_billing_date=today
    )
    
    for company in companies_to_renew:
        try:
            payment_service = PaymentService(
                gateway_name=company.owner.payment_gateway
            )
            
            # Process renewal
            amount = (company.subscription_plan.price_yearly 
                     if company.billing_cycle == 'yearly' 
                     else company.subscription_plan.price_monthly)
            
            result = payment_service.gateway.charge_customer(
                customer_id=company.owner.payment_customer_id,
                amount=amount,
                description=f"Renovação {company.subscription_plan.name} - {company.billing_cycle}"
            )
            
            if result['status'] == 'succeeded':
                # Update next billing date
                if company.billing_cycle == 'yearly':
                    company.next_billing_date = today + timedelta(days=365)
                else:
                    # Add one month
                    next_month = today.replace(day=1) + timedelta(days=32)
                    company.next_billing_date = next_month.replace(day=1)
                
                company.save()
                
                # Log successful payment
                from apps.companies.models import PaymentHistory
                PaymentHistory.objects.create(
                    company=company,
                    subscription_plan=company.subscription_plan,
                    transaction_type='subscription',
                    amount=amount,
                    currency='BRL',
                    status='paid',
                    description=f"Renovação automática - {company.subscription_plan.name}",
                    transaction_date=timezone.now(),
                    paid_at=timezone.now(),
                    stripe_payment_intent_id=result.get('charge_id', '')
                )
            else:
                # Payment failed
                company.subscription_status = 'past_due'
                company.save()
                
                # Send notification
                from apps.notifications.email_service import EmailService
                EmailService.send_payment_failed_email(
                    email=company.owner.email,
                    company_name=company.name,
                    owner_name=company.owner.get_full_name()
                )
                
        except Exception as e:
            logger.error(f"Error processing renewal for company {company.id}: {e}")


@shared_task
def check_usage_limits():
    """
    Check if companies are approaching their usage limits
    Runs every 6 hours
    """
    from apps.companies.models import Company
    from apps.notifications.email_service import EmailService
    
    companies = Company.objects.filter(
        is_active=True,
        subscription_status__in=['active', 'trial']
    ).select_related('subscription_plan')
    
    for company in companies:
        # Check transaction limit
        if company.subscription_plan:
            tx_ratio = company.current_month_transactions / company.subscription_plan.max_transactions
            
            if tx_ratio >= 0.9 and not company.notified_90_percent:
                # 90% usage warning
                EmailService.send_usage_limit_warning(
                    email=company.owner.email,
                    company_name=company.name,
                    limit_type='transações',
                    percentage=90,
                    current=company.current_month_transactions,
                    limit=company.subscription_plan.max_transactions
                )
                company.notified_90_percent = True
                company.save()
            
            elif tx_ratio >= 0.8 and not company.notified_80_percent:
                # 80% usage warning
                EmailService.send_usage_limit_warning(
                    email=company.owner.email,
                    company_name=company.name,
                    limit_type='transações',
                    percentage=80,
                    current=company.current_month_transactions,
                    limit=company.subscription_plan.max_transactions
                )
                company.notified_80_percent = True
                company.save()


@shared_task
def cleanup_expired_subscriptions():
    """
    Clean up expired subscriptions and free resources
    Runs weekly
    """
    from apps.companies.models import Company
    
    # Find companies with expired subscriptions older than 30 days
    cutoff_date = timezone.now() - timedelta(days=30)
    
    expired_companies = Company.objects.filter(
        subscription_status='expired',
        subscription_end_date__lt=cutoff_date
    )
    
    for company in expired_companies:
        # Deactivate bank connections
        company.bank_accounts.update(is_active=False)
        
        # Deactivate additional users
        company.company_users.update(is_active=False)
        
        logger.info(f"Cleaned up resources for expired company {company.id}")