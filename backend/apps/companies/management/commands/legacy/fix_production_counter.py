from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from apps.companies.models import Company, ResourceUsage
from apps.banking.models import Transaction
import logging

User = get_user_model()
logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Fix production counter issue for specific email'

    def add_arguments(self, parser):
        parser.add_argument(
            'email',
            type=str,
            help='User email to fix'
        )

    def handle(self, *args, **options):
        email = options['email']
        
        self.stdout.write(f"\n=== Fixing counter for {email} ===")
        
        try:
            # Get user and company
            user = User.objects.get(email=email)
            company = user.company
            
            self.stdout.write(f"Found company: {company.name} (ID: {company.id})")
            
            # Get current month start with timezone
            now = timezone.now()
            month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            
            # Count transactions for current month
            transactions = Transaction.objects.filter(
                bank_account__company=company,
                transaction_date__gte=month_start
            )
            
            current_month_count = transactions.count()
            
            self.stdout.write(f"\nCurrent state:")
            self.stdout.write(f"- Company.current_month_transactions: {company.current_month_transactions}")
            self.stdout.write(f"- Actual transactions this month: {current_month_count}")
            
            # Show some transactions
            if current_month_count > 0:
                self.stdout.write(f"\nSample transactions:")
                for tx in transactions[:5]:
                    self.stdout.write(f"  - {tx.transaction_date}: {tx.description[:40]}")
            
            # Update company counter
            old_company_count = company.current_month_transactions
            company.current_month_transactions = current_month_count
            company.save(update_fields=['current_month_transactions'])
            
            # Get or create ResourceUsage for current month
            usage = ResourceUsage.get_or_create_current_month(company)
            old_usage_count = usage.transactions_count
            usage.transactions_count = current_month_count
            usage.save(update_fields=['transactions_count'])
            
            self.stdout.write(f"\n✅ FIXED!")
            self.stdout.write(f"- Company counter: {old_company_count} → {current_month_count}")
            self.stdout.write(f"- ResourceUsage: {old_usage_count} → {current_month_count}")
            
            # Test API response
            plan = company.subscription_plan
            if plan:
                percentage = (current_month_count / plan.max_transactions * 100) if plan.max_transactions != 999999 else 0
                self.stdout.write(f"\nPlan info:")
                self.stdout.write(f"- Plan: {plan.name}")
                self.stdout.write(f"- Limit: {plan.max_transactions}")
                self.stdout.write(f"- Usage: {percentage:.1f}%")
            
            self.stdout.write(self.style.SUCCESS(f"\n✅ Counter fixed successfully!"))
            
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"User not found: {email}"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error: {str(e)}"))
            import traceback
            traceback.print_exc()