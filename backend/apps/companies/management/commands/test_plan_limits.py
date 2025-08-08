from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.companies.models import Company, SubscriptionPlan, ResourceUsage
from apps.banking.models import BankAccount
from django.contrib.auth import get_user_model
import json

User = get_user_model()


class Command(BaseCommand):
    help = 'Test plan limits and upgrade messages'

    def add_arguments(self, parser):
        parser.add_argument(
            '--email',
            type=str,
            help='User email to test'
        )
        parser.add_argument(
            '--simulate',
            type=str,
            choices=['80', '90', '100'],
            help='Simulate usage percentage (80%, 90%, or 100%)'
        )

    def handle(self, *args, **options):
        email = options.get('email')
        simulate = options.get('simulate')
        
        # Get company
        if email:
            try:
                user = User.objects.get(email=email)
                company = user.company
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error finding user/company: {e}"))
                return
        else:
            company = Company.objects.filter(subscription_plan__isnull=False).first()
            if not company:
                self.stdout.write(self.style.ERROR("No companies with subscription plans found"))
                return
        
        self.stdout.write(self.style.SUCCESS(f"\n=== Testing Plan Limits for: {company.name} ==="))
        
        # Display current plan info
        plan = company.subscription_plan
        if plan:
            self.stdout.write(f"\nCurrent Plan: {plan.name} ({plan.plan_type})")
            self.stdout.write(f"- Max Transactions: {plan.max_transactions}")
            self.stdout.write(f"- Max Bank Accounts: {plan.max_bank_accounts}")
            self.stdout.write(f"- Max AI Requests: {plan.max_ai_requests_per_month}")
            self.stdout.write(f"- Has AI Insights: {'Yes' if plan.max_ai_requests_per_month > 0 else 'No'}")
        else:
            self.stdout.write(self.style.WARNING("No subscription plan found!"))
            return
        
        # Display current usage
        self.stdout.write(f"\nCurrent Usage:")
        self.stdout.write(f"- Transactions: {company.current_month_transactions}")
        self.stdout.write(f"- Bank Accounts: {company.bank_accounts.filter(is_active=True).count()}")
        
        usage = ResourceUsage.get_or_create_current_month(company)
        self.stdout.write(f"- AI Requests: {usage.total_ai_usage}")
        
        # Test each limit check
        self.stdout.write(f"\n=== Testing Limit Checks ===")
        
        # 1. Test transaction limits
        self.stdout.write(f"\n1. Transaction Limits:")
        limit_reached, usage_info = company.check_plan_limits('transactions')
        self.stdout.write(f"   - Limit reached: {limit_reached}")
        self.stdout.write(f"   - Usage info: {json.dumps(usage_info, indent=2)}")
        
        # 2. Test bank account limits
        self.stdout.write(f"\n2. Bank Account Limits:")
        can_add = company.can_add_bank_account()
        self.stdout.write(f"   - Can add bank account: {can_add}")
        
        # 3. Test AI limits
        self.stdout.write(f"\n3. AI Limits:")
        can_use_ai, message = company.can_use_ai_insight()
        self.stdout.write(f"   - Can use AI: {can_use_ai}")
        self.stdout.write(f"   - Message: {message}")
        
        # Simulate different usage levels if requested
        if simulate:
            self.stdout.write(f"\n=== Simulating {simulate}% Usage ===")
            
            # Save original values
            original_transactions = company.current_month_transactions
            original_usage_count = usage.transactions_count
            
            # Calculate simulated usage
            if plan.max_transactions != 999999:  # Not unlimited
                simulated_count = int(plan.max_transactions * int(simulate) / 100)
                
                # Update temporarily
                company.current_month_transactions = simulated_count
                company.save(update_fields=['current_month_transactions'])
                
                usage.transactions_count = simulated_count
                usage.save(update_fields=['transactions_count'])
                
                self.stdout.write(f"\nSimulated transaction count: {simulated_count}")
                
                # Test responses at this level
                self.stdout.write(f"\nChecking responses at {simulate}% usage:")
                
                # Check limit status
                limit_reached, usage_info = company.check_plan_limits('transactions')
                self.stdout.write(f"- Limit reached: {limit_reached}")
                self.stdout.write(f"- Usage percentage: {company.get_usage_percentage('transactions'):.1f}%")
                
                # Check what would happen if trying to create a transaction
                if limit_reached:
                    self.stdout.write(self.style.WARNING("\nTransaction creation would be BLOCKED with:"))
                    self.stdout.write("- Status: 429 Too Many Requests")
                    self.stdout.write("- Error: 'Limite de transações atingido para este mês'")
                    
                    if plan.plan_type == 'starter':
                        self.stdout.write("- Suggested upgrade: Professional")
                    elif plan.plan_type == 'professional':
                        self.stdout.write("- Suggested upgrade: Enterprise")
                else:
                    percentage = company.get_usage_percentage('transactions')
                    if percentage >= 90:
                        self.stdout.write(self.style.WARNING("\nTransaction would be created with 90% warning:"))
                        self.stdout.write("- upgrade_suggestion: true")
                        self.stdout.write("- message: 'Você está próximo do limite! Considere fazer upgrade do seu plano.'")
                    elif percentage >= 80:
                        self.stdout.write(self.style.WARNING("\nTransaction would be created with 80% warning:"))
                        self.stdout.write(f"- message: 'Atenção: Você já utilizou {percentage:.1f}% do seu limite mensal de transações.'")
                    else:
                        self.stdout.write(self.style.SUCCESS("\nTransaction would be created normally"))
                
                # Restore original values
                company.current_month_transactions = original_transactions
                company.save(update_fields=['current_month_transactions'])
                
                usage.transactions_count = original_usage_count
                usage.save(update_fields=['transactions_count'])
            else:
                self.stdout.write("Cannot simulate - plan has unlimited transactions")
        
        # Check notification flags
        self.stdout.write(f"\n=== Notification Flags ===")
        self.stdout.write(f"- 80% notified: {company.notified_80_percent}")
        self.stdout.write(f"- 90% notified: {company.notified_90_percent}")
        
        self.stdout.write(self.style.SUCCESS("\n=== Test complete ==="))