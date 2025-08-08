from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.companies.models import Company, ResourceUsage
from apps.banking.models import Transaction
from django.db.models import Count
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Fix transaction counters for all companies'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be fixed without making changes'
        )

    def handle(self, *args, **options):
        dry_run = options.get('dry_run', False)
        
        self.stdout.write(self.style.SUCCESS(f"\n=== Fixing Transaction Counters for All Companies ==="))
        if dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN MODE - No changes will be made"))
        
        # Get current month start
        now = timezone.now()
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        # Get all companies
        companies = Company.objects.all()
        total_companies = companies.count()
        
        self.stdout.write(f"\nProcessing {total_companies} companies...")
        
        fixed_count = 0
        
        for company in companies:
            # Count transactions for current month
            current_month_count = Transaction.objects.filter(
                bank_account__company=company,
                transaction_date__gte=month_start
            ).count()
            
            # Get or create ResourceUsage
            usage = ResourceUsage.get_or_create_current_month(company)
            
            # Check if update needed
            needs_update = False
            
            if company.current_month_transactions != current_month_count:
                self.stdout.write(f"\n{company.name}:")
                self.stdout.write(f"  Company counter: {company.current_month_transactions} → {current_month_count}")
                needs_update = True
                
                if not dry_run:
                    company.current_month_transactions = current_month_count
                    company.save(update_fields=['current_month_transactions'])
            
            if usage.transactions_count != current_month_count:
                if not needs_update:
                    self.stdout.write(f"\n{company.name}:")
                self.stdout.write(f"  ResourceUsage counter: {usage.transactions_count} → {current_month_count}")
                needs_update = True
                
                if not dry_run:
                    usage.transactions_count = current_month_count
                    usage.save(update_fields=['transactions_count'])
            
            if needs_update:
                fixed_count += 1
                if not dry_run:
                    self.stdout.write(self.style.SUCCESS("  ✅ Fixed!"))
                else:
                    self.stdout.write(self.style.WARNING("  Would be fixed"))
        
        # Summary
        self.stdout.write(f"\n=== Summary ===")
        self.stdout.write(f"Total companies: {total_companies}")
        self.stdout.write(f"Companies needing fixes: {fixed_count}")
        
        if dry_run:
            self.stdout.write(self.style.WARNING("\nDRY RUN completed. Run without --dry-run to apply fixes."))
        else:
            self.stdout.write(self.style.SUCCESS(f"\n✅ Fixed {fixed_count} companies"))
        
        # Show companies with highest usage
        if not dry_run:
            self.stdout.write(f"\n=== Top 5 Companies by Transaction Count ===")
            top_companies = Company.objects.filter(
                current_month_transactions__gt=0
            ).order_by('-current_month_transactions')[:5]
            
            for company in top_companies:
                plan_limit = company.subscription_plan.max_transactions if company.subscription_plan else 100
                percentage = (company.current_month_transactions / plan_limit * 100) if plan_limit != 999999 else 0
                
                self.stdout.write(
                    f"- {company.name}: {company.current_month_transactions}/{plan_limit} "
                    f"({percentage:.1f}%)"
                )