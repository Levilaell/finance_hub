from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.companies.models import Company, ResourceUsage
from apps.banking.models import Transaction
from django.contrib.auth import get_user_model

User = get_user_model()


class Command(BaseCommand):
    help = 'Force update transaction counters for a specific user'

    def add_arguments(self, parser):
        parser.add_argument(
            '--email',
            type=str,
            help='User email to update'
        )

    def handle(self, *args, **options):
        email = options.get('email')
        
        if email:
            try:
                user = User.objects.get(email=email)
                companies = [user.company]
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error: {e}"))
                return
        else:
            companies = Company.objects.all()
        
        # Get current month start
        now = timezone.now()
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        for company in companies:
            self.stdout.write(f"\n=== Updating {company.name} ===")
            
            # Count ALL transactions for current month
            current_month_count = Transaction.objects.filter(
                bank_account__company=company,
                transaction_date__gte=month_start
            ).count()
            
            self.stdout.write(f"Found {current_month_count} transactions for current month")
            
            # Force update company counter
            old_count = company.current_month_transactions
            company.current_month_transactions = current_month_count
            company.save(update_fields=['current_month_transactions'])
            self.stdout.write(f"Company counter: {old_count} → {current_month_count}")
            
            # Force update ResourceUsage
            usage = ResourceUsage.get_or_create_current_month(company)
            old_usage = usage.transactions_count
            usage.transactions_count = current_month_count
            usage.save(update_fields=['transactions_count'])
            self.stdout.write(f"ResourceUsage counter: {old_usage} → {current_month_count}")
            
            # Show some transactions for debug
            recent_txs = Transaction.objects.filter(
                bank_account__company=company,
                transaction_date__gte=month_start
            ).order_by('-transaction_date')[:5]
            
            if recent_txs:
                self.stdout.write("\nRecent transactions this month:")
                for tx in recent_txs:
                    self.stdout.write(f"  - {tx.transaction_date}: {tx.description[:40]} R${tx.amount}")
            else:
                self.stdout.write("No transactions found for current month")
            
            self.stdout.write(self.style.SUCCESS("✅ Updated!"))