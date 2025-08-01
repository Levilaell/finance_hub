"""
Populate ResourceUsage with current month data
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.companies.models import Company, ResourceUsage
from apps.banking.models import Transaction


class Command(BaseCommand):
    help = 'Populate ResourceUsage with current month data'

    def handle(self, *args, **options):
        # Get current month
        now = timezone.now()
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        # Process each company
        for company in Company.objects.filter(is_active=True):
            self.stdout.write(f'Processing {company.name}...')
            
            # Get or create usage record
            usage, created = ResourceUsage.objects.get_or_create(
                company=company,
                month=month_start.date(),
                defaults={
                    'transactions_count': 0,
                    'ai_requests_count': 0,
                    'reports_generated': 0
                }
            )
            
            # Count transactions for this month
            transaction_count = Transaction.objects.filter(
                bank_account__company=company,
                created_at__gte=month_start
            ).count()
            
            # Update usage record
            usage.transactions_count = transaction_count
            
            # Estimate AI usage (10% of transactions)
            usage.ai_requests_count = int(transaction_count * 0.1)
            
            usage.save()
            
            action = 'Created' if created else 'Updated'
            self.stdout.write(
                self.style.SUCCESS(
                    f'{action} usage for {company.name}: '
                    f'{transaction_count} transactions, '
                    f'{usage.ai_requests_count} AI requests'
                )
            )
        
        self.stdout.write(self.style.SUCCESS('Successfully populated usage data!'))