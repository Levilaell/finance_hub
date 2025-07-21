from django.core.management.base import BaseCommand
from django.db.models import Count, Q
from django.utils import timezone
from apps.companies.models import Company, ResourceUsage
from apps.banking.models import Transaction, BankAccount


class Command(BaseCommand):
    help = 'Quick fix for transaction counters'

    def handle(self, *args, **options):
        # Get current month
        now = timezone.now()
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        self.stdout.write("=== Quick Fix Transaction Counters ===")
        self.stdout.write(f"Current month start: {month_start}")
        
        # Get all companies with bank accounts
        companies_with_accounts = Company.objects.filter(
            bank_accounts__is_active=True
        ).distinct()
        
        fixed = 0
        
        for company in companies_with_accounts:
            # Count actual transactions
            actual_count = Transaction.objects.filter(
                bank_account__company=company,
                transaction_date__gte=month_start
            ).count()
            
            # Check if needs update
            needs_update = False
            
            if company.current_month_transactions != actual_count:
                self.stdout.write(f"\n{company.name} ({company.owner.email}):")
                self.stdout.write(f"  Old count: {company.current_month_transactions}")
                self.stdout.write(f"  New count: {actual_count}")
                
                # Update company
                company.current_month_transactions = actual_count
                company.save(update_fields=['current_month_transactions'])
                
                # Update ResourceUsage
                usage = ResourceUsage.get_or_create_current_month(company)
                usage.transactions_count = actual_count
                usage.save(update_fields=['transactions_count'])
                
                self.stdout.write("  ✅ Fixed!")
                fixed += 1
        
        self.stdout.write(f"\n=== Summary ===")
        self.stdout.write(f"Total companies checked: {companies_with_accounts.count()}")
        self.stdout.write(f"Companies fixed: {fixed}")
        self.stdout.write(self.style.SUCCESS("✅ Done!"))