"""Unified command for managing company usage counters."""
from django.core.management.base import CommandError
from .base import BaseUsageCommand


class Command(BaseUsageCommand):
    help = 'Manage company usage counters - check, fix, or recalculate'
    
    def add_arguments(self, parser):
        super().add_arguments(parser)
        parser.add_argument(
            'action',
            choices=['check', 'fix', 'recalculate', 'debug'],
            help='Action to perform on usage counters'
        )
        parser.add_argument(
            '--fix-discrepancies',
            action='store_true',
            help='Automatically fix discrepancies when checking'
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Show detailed output'
        )
    
    def handle(self, *args, **options):
        action = options['action']
        company_id = options.get('company_id')
        dry_run = options.get('dry_run', False)
        
        # Get companies to process
        filters = {'id': company_id} if company_id else {}
        companies = self.get_companies(filters)
        
        if not companies.exists():
            raise CommandError('No companies found to process')
        
        self.stdout.write(f"Processing {companies.count()} companies...")
        
        # Route to appropriate action
        if action == 'check':
            self.check_usage(companies, options)
        elif action == 'fix':
            self.fix_usage(companies, dry_run)
        elif action == 'recalculate':
            self.recalculate_all(companies, dry_run)
        elif action == 'debug':
            self.debug_usage(companies, options)
    
    def check_usage(self, companies, options):
        """Check usage counters for discrepancies."""
        discrepancies = []
        
        for company in companies:
            success, metrics = self.recalculate_usage(company, dry_run=True)
            if not success:
                continue
            
            # Check for discrepancies
            has_discrepancy = False
            for field, calculated in metrics.items():
                current = getattr(company, field, 0)
                if current != calculated:
                    has_discrepancy = True
                    discrepancies.append({
                        'company': company,
                        'field': field,
                        'current': current,
                        'calculated': calculated
                    })
                    
                    if options.get('verbose'):
                        self.stdout.write(
                            self.style.WARNING(
                                f"  {field}: current={current}, calculated={calculated}"
                            )
                        )
            
            if not has_discrepancy:
                self.log_action(company, 'Check', 'All counters correct', 'success')
        
        # Handle discrepancies
        if discrepancies:
            self.stdout.write(
                self.style.WARNING(
                    f"\nFound {len(discrepancies)} discrepancies"
                )
            )
            
            if options.get('fix_discrepancies'):
                self.stdout.write("Fixing discrepancies...")
                self.fix_usage(companies, dry_run=False)
        else:
            self.stdout.write(
                self.style.SUCCESS("All usage counters are correct!")
            )
    
    def fix_usage(self, companies, dry_run):
        """Fix usage counter discrepancies."""
        fixed_count = 0
        
        for company in companies:
            success, metrics = self.recalculate_usage(company, dry_run)
            if success and not dry_run:
                fixed_count += 1
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING(f"Would fix {companies.count()} companies")
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(f"Fixed {fixed_count} companies")
            )
    
    def recalculate_all(self, companies, dry_run):
        """Force recalculation of all usage counters."""
        self.stdout.write("Recalculating all usage counters...")
        self.fix_usage(companies, dry_run)
    
    def debug_usage(self, companies, options):
        """Debug usage counter issues with detailed output."""
        for company in companies:
            self.stdout.write(self.style.HTTP_INFO(f"\n=== {company.name} ==="))
            
            # Get current values
            self.stdout.write("Current values:")
            fields = [
                'ai_conversations', 'ai_insights', 'ai_credits_used',
                'bank_accounts', 'transactions'
            ]
            for field in fields:
                value = getattr(company, field, 'N/A')
                self.stdout.write(f"  {field}: {value}")
            
            # Calculate actual values
            success, metrics = self.recalculate_usage(company, dry_run=True)
            if success:
                self.stdout.write("\nCalculated values:")
                for field, value in metrics.items():
                    current = getattr(company, field, 0)
                    status = '✓' if current == value else '✗'
                    self.stdout.write(f"  {field}: {value} {status}")