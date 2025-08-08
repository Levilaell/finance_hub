"""
Simplified command to fix usage counters
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.companies.models import Company, ResourceUsage
from apps.banking.models import Transaction


class Command(BaseCommand):
    help = 'Fix and recalculate usage counters'

    def handle(self, *args, **options):
        now = timezone.now()
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        month_start_date = month_start.date()
        
        companies = Company.objects.filter(is_active=True)
        self.stdout.write(f'Processing {companies.count()} companies...')
        
        fixed_count = 0
        
        for company in companies:
            # Count actual transactions for current month
            actual_transactions = Transaction.objects.filter(
                company=company,
                date__gte=month_start
            ).count()
            
            # Get or create ResourceUsage record
            usage, created = ResourceUsage.objects.get_or_create(
                company=company,
                month=month_start_date,
                defaults={
                    'transactions_count': actual_transactions,
                    'ai_requests_count': company.current_month_ai_requests
                }
            )
            
            # Update if different
            updated = False
            
            if usage.transactions_count != actual_transactions:
                usage.transactions_count = actual_transactions
                updated = True
            
            if company.current_month_transactions != actual_transactions:
                company.current_month_transactions = actual_transactions
                company.save(update_fields=['current_month_transactions'])
                updated = True
            
            if updated:
                usage.save()
                fixed_count += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Fixed {company.name}: {actual_transactions} transactions'
                    )
                )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Fixed {fixed_count} companies with incorrect counters'
            )
        )