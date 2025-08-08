"""
Simplified command to check usage and limits
"""
from django.core.management.base import BaseCommand
from django.db.models import Count
from apps.companies.models import Company
from apps.banking.models import BankAccount


class Command(BaseCommand):
    help = 'Check usage against plan limits'

    def add_arguments(self, parser):
        parser.add_argument(
            '--company',
            type=str,
            help='Check specific company by name or ID'
        )

    def handle(self, *args, **options):
        company_filter = options.get('company')
        
        if company_filter:
            try:
                # Try by ID first
                companies = Company.objects.filter(id=company_filter)
                if not companies.exists():
                    # Try by name
                    companies = Company.objects.filter(name__icontains=company_filter)
            except ValueError:
                # Not a valid ID, search by name
                companies = Company.objects.filter(name__icontains=company_filter)
        else:
            companies = Company.objects.filter(is_active=True)
        
        if not companies.exists():
            self.stdout.write(self.style.ERROR('No companies found'))
            return
        
        for company in companies:
            self.stdout.write(f'\n{self.style.WARNING("="*50)}')
            self.stdout.write(f'Company: {company.name} (ID: {company.id})')
            self.stdout.write(f'Owner: {company.owner.email}')
            self.stdout.write(f'Status: {company.subscription_status}')
            
            if company.subscription_plan:
                plan = company.subscription_plan
                self.stdout.write(f'Plan: {plan.name}')
                
                # Check transactions
                trans_limit = plan.max_transactions
                trans_used = company.current_month_transactions
                trans_percent = (trans_used / trans_limit * 100) if trans_limit > 0 else 0
                
                self.stdout.write(
                    self._format_usage('Transactions', trans_used, trans_limit, trans_percent)
                )
                
                # Check bank accounts
                bank_limit = plan.max_bank_accounts
                bank_used = BankAccount.objects.filter(
                    company=company, 
                    is_active=True
                ).count()
                bank_percent = (bank_used / bank_limit * 100) if bank_limit > 0 else 0
                
                self.stdout.write(
                    self._format_usage('Bank Accounts', bank_used, bank_limit, bank_percent)
                )
                
                # Check AI requests
                ai_limit = plan.max_ai_requests
                ai_used = company.current_month_ai_requests
                ai_percent = (ai_used / ai_limit * 100) if ai_limit > 0 else 0
                
                self.stdout.write(
                    self._format_usage('AI Requests', ai_used, ai_limit, ai_percent)
                )
            else:
                self.stdout.write(self.style.ERROR('No subscription plan'))
    
    def _format_usage(self, name, used, limit, percent):
        """Format usage display with color coding"""
        if percent >= 100:
            style = self.style.ERROR
            status = 'LIMIT REACHED'
        elif percent >= 80:
            style = self.style.WARNING
            status = 'NEAR LIMIT'
        else:
            style = self.style.SUCCESS
            status = 'OK'
        
        return style(f'{name}: {used}/{limit} ({percent:.1f}%) - {status}')