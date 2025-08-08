"""Base classes for management commands to reduce code duplication."""
from django.core.management.base import BaseCommand
from apps.companies.models import Company
import logging


class BaseCompanyCommand(BaseCommand):
    """Base class for commands that operate on companies."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logger = logging.getLogger(f'management.{self.__class__.__name__}')
    
    def get_companies(self, company_filter=None):
        """Get companies with optional filtering."""
        queryset = Company.objects.all()
        if company_filter:
            queryset = queryset.filter(**company_filter)
        return queryset.select_related('subscription_plan')
    
    def log_action(self, company, action, result, level='info'):
        """Standardized logging for company actions."""
        msg = f"[{company.name}] {action}: {result}"
        getattr(self.logger, level)(msg)
        self.stdout.write(getattr(self.style, level.upper())(msg))
    
    def handle_error(self, company, operation, error):
        """Standardized error handling."""
        self.log_action(company, operation, f"Error: {str(error)}", 'error')
        return False
    
    def add_arguments(self, parser):
        """Common arguments for company commands."""
        parser.add_argument(
            '--company-id',
            type=int,
            help='Process specific company by ID'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Preview changes without applying them'
        )


class BaseUsageCommand(BaseCompanyCommand):
    """Base class for usage/counter related commands."""
    
    def recalculate_usage(self, company, dry_run=False):
        """Recalculate usage for a company."""
        from apps.ai_insights.models import (
            AICreditTransaction, AIConversation, AIInsight
        )
        from apps.banking.models import Transaction, BankAccount
        
        try:
            # Calculate metrics
            metrics = {
                'ai_conversations': AIConversation.objects.filter(company=company).count(),
                'ai_insights': AIInsight.objects.filter(company=company).count(),
                'ai_credits_used': AICreditTransaction.objects.filter(
                    company=company, 
                    transaction_type='debit'
                ).aggregate(total=models.Sum('amount'))['total'] or 0,
                'bank_accounts': BankAccount.objects.filter(company=company).count(),
                'transactions': Transaction.objects.filter(
                    bank_account__company=company
                ).count(),
            }
            
            if not dry_run:
                # Update company usage
                for key, value in metrics.items():
                    setattr(company, key, value)
                company.save()
            
            self.log_action(company, 'Usage recalculated', metrics)
            return True, metrics
            
        except Exception as e:
            return self.handle_error(company, 'recalculate_usage', e), None


class BaseStripeCommand(BaseCompanyCommand):
    """Base class for Stripe-related commands."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.stripe_service = None
    
    def get_stripe_service(self):
        """Lazy load Stripe service."""
        if not self.stripe_service:
            from apps.payments.services.stripe_service import StripeService
            self.stripe_service = StripeService()
        return self.stripe_service
    
    def sync_stripe_data(self, company, dry_run=False):
        """Sync company data with Stripe."""
        try:
            service = self.get_stripe_service()
            
            if not company.stripe_customer_id:
                self.log_action(company, 'Stripe sync', 'No customer ID', 'warning')
                return False
            
            # Get customer from Stripe
            customer = service.get_customer(company.stripe_customer_id)
            
            if dry_run:
                self.log_action(company, 'Stripe sync', f'Would sync: {customer.email}')
            else:
                # Sync data
                company.stripe_customer_email = customer.email
                company.save()
                self.log_action(company, 'Stripe sync', 'Success')
            
            return True
            
        except Exception as e:
            return self.handle_error(company, 'sync_stripe_data', e)