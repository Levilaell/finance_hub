from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.companies.models import Company, ResourceUsage
from apps.banking.models import BankAccount, Transaction
from django.utils import timezone
import json

User = get_user_model()


class Command(BaseCommand):
    help = 'Check what the usage-limits API endpoint returns'

    def add_arguments(self, parser):
        parser.add_argument(
            '--email',
            type=str,
            help='User email to check'
        )

    def handle(self, *args, **options):
        email = options.get('email')
        
        # Get company
        if email:
            try:
                user = User.objects.get(email=email)
                company = user.company
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error finding user/company: {e}"))
                return
        else:
            company = Company.objects.filter(bank_accounts__isnull=False).distinct().first()
            if not company:
                self.stdout.write(self.style.ERROR("No companies found"))
                return
        
        self.stdout.write(self.style.SUCCESS(f"\n=== Checking Usage API for: {company.name} ==="))
        
        # Simulate the API endpoint logic
        try:
            # Get or create current month usage record
            usage_record = ResourceUsage.get_or_create_current_month(company)
            
            self.stdout.write(f"\n1. ResourceUsage Record:")
            self.stdout.write(f"   - ID: {usage_record.id}")
            self.stdout.write(f"   - Month: {usage_record.month}")
            self.stdout.write(f"   - transactions_count: {usage_record.transactions_count}")
            self.stdout.write(f"   - ai_requests_count: {usage_record.ai_requests_count}")
            self.stdout.write(f"   - reports_generated: {usage_record.reports_generated}")
            self.stdout.write(f"   - total_ai_usage: {usage_record.total_ai_usage}")
            
            # Get actual counts
            month_start = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            
            # Count transactions by transaction_date (what should be counted)
            tx_by_date = Transaction.objects.filter(
                bank_account__company=company,
                transaction_date__gte=month_start
            ).count()
            
            # Count transactions by created_at (what might be miscounted)
            tx_by_created = Transaction.objects.filter(
                bank_account__company=company,
                created_at__gte=month_start
            ).count()
            
            self.stdout.write(f"\n2. Actual Transaction Counts:")
            self.stdout.write(f"   - By transaction_date (correct): {tx_by_date}")
            self.stdout.write(f"   - By created_at (incorrect): {tx_by_created}")
            self.stdout.write(f"   - Company.current_month_transactions: {company.current_month_transactions}")
            
            # Check bank accounts
            bank_account_count = BankAccount.objects.filter(company=company, is_active=True).count()
            self.stdout.write(f"\n3. Bank Accounts:")
            self.stdout.write(f"   - Active count: {bank_account_count}")
            
            # Simulate API response
            plan = company.subscription_plan
            if plan:
                api_response = {
                    'transactions': {
                        'limit': plan.max_transactions,
                        'used': usage_record.transactions_count,
                        'percentage': round((usage_record.transactions_count / plan.max_transactions * 100), 1) if plan.max_transactions != 999999 else 0
                    },
                    'bank_accounts': {
                        'limit': plan.max_bank_accounts,
                        'used': bank_account_count,
                        'percentage': round((bank_account_count / plan.max_bank_accounts * 100), 1) if plan.max_bank_accounts != 999 else 0
                    },
                    'ai_requests': {
                        'limit': plan.max_ai_requests_per_month,
                        'used': usage_record.total_ai_usage,
                        'percentage': round((usage_record.total_ai_usage / plan.max_ai_requests_per_month * 100), 1) if plan.max_ai_requests_per_month != 999999 else 0
                    }
                }
                
                self.stdout.write(f"\n4. API Response would be:")
                self.stdout.write(json.dumps(api_response, indent=2))
            
            # Check if there's a mismatch
            if usage_record.transactions_count != tx_by_date:
                self.stdout.write(self.style.WARNING(f"\n⚠️  MISMATCH DETECTED!"))
                self.stdout.write(f"ResourceUsage shows: {usage_record.transactions_count}")
                self.stdout.write(f"Actual count is: {tx_by_date}")
                self.stdout.write(f"\nFixing ResourceUsage...")
                
                usage_record.transactions_count = tx_by_date
                usage_record.save(update_fields=['transactions_count'])
                
                self.stdout.write(self.style.SUCCESS("✅ Fixed!"))
            
            if company.current_month_transactions != tx_by_date:
                self.stdout.write(self.style.WARNING(f"\n⚠️  Company counter MISMATCH!"))
                self.stdout.write(f"Company shows: {company.current_month_transactions}")
                self.stdout.write(f"Actual count is: {tx_by_date}")
                self.stdout.write(f"\nFixing Company counter...")
                
                company.current_month_transactions = tx_by_date
                company.save(update_fields=['current_month_transactions'])
                
                self.stdout.write(self.style.SUCCESS("✅ Fixed!"))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error: {str(e)}"))
            import traceback
            traceback.print_exc()
        
        self.stdout.write(self.style.SUCCESS("\n=== Check complete ==="))