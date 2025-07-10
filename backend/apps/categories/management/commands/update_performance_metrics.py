"""
Management command to update performance metrics retroactively
This command will analyze existing categorization logs and create/update CategoryPerformance records
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import date, timedelta
from apps.categories.models import CategoryPerformance, CategorizationLog
from apps.companies.models import Company
from apps.banking.models import TransactionCategory


class Command(BaseCommand):
    help = 'Update performance metrics retroactively from existing categorization logs'

    def add_arguments(self, parser):
        parser.add_argument(
            '--period-days',
            type=int,
            default=30,
            help='Number of days to look back for performance calculation (default: 30)'
        )
        parser.add_argument(
            '--company-id',
            type=int,
            help='Update metrics for specific company only'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force update existing performance records'
        )

    def handle(self, *args, **options):
        period_days = options['period_days']
        company_id = options.get('company_id')
        force = options['force']
        
        self.stdout.write(f"Updating performance metrics for the last {period_days} days...")
        
        # Get companies to process
        if company_id:
            companies = Company.objects.filter(id=company_id)
            if not companies.exists():
                self.stdout.write(
                    self.style.ERROR(f"Company with ID {company_id} not found")
                )
                return
        else:
            companies = Company.objects.all()
        
        period_start = date.today() - timedelta(days=period_days)
        period_end = date.today()
        
        total_updated = 0
        total_created = 0
        
        for company in companies:
            self.stdout.write(f"Processing company: {company.name}")
            
            # Get all categories that have logs in this period
            category_ids = CategorizationLog.objects.filter(
                transaction__bank_account__company=company,
                created_at__date__gte=period_start,
                created_at__date__lte=period_end
            ).values_list('suggested_category_id', flat=True).distinct()
            
            for category_id in category_ids:
                if not category_id:
                    continue
                    
                try:
                    category = TransactionCategory.objects.get(id=category_id)
                except TransactionCategory.DoesNotExist:
                    continue
                
                # Get or create performance record
                performance, created = CategoryPerformance.objects.get_or_create(
                    company=company,
                    category=category,
                    period_start=period_start,
                    period_end=period_end,
                    defaults={
                        'total_predictions': 0,
                        'correct_predictions': 0,
                        'false_positives': 0,
                        'false_negatives': 0
                    }
                )
                
                if created:
                    total_created += 1
                    self.stdout.write(f"  Created performance record for {category.name}")
                elif not force:
                    self.stdout.write(f"  Skipping existing record for {category.name} (use --force to update)")
                    continue
                else:
                    total_updated += 1
                    self.stdout.write(f"  Updating performance record for {category.name}")
                
                # Calculate metrics from logs
                category_logs = CategorizationLog.objects.filter(
                    transaction__bank_account__company=company,
                    suggested_category=category,
                    created_at__date__gte=period_start,
                    created_at__date__lte=period_end
                )
                
                # Reset metrics
                performance.total_predictions = category_logs.count()
                performance.correct_predictions = category_logs.filter(was_accepted=True).count()
                
                # Calculate false positives and false negatives
                # False positives: when this category was suggested but rejected
                performance.false_positives = category_logs.filter(
                    was_accepted=False,
                    final_category__isnull=False
                ).exclude(final_category=category).count()
                
                # False negatives: when other categories were suggested but this was the correct one
                false_negative_logs = CategorizationLog.objects.filter(
                    transaction__bank_account__company=company,
                    final_category=category,
                    created_at__date__gte=period_start,
                    created_at__date__lte=period_end
                ).exclude(suggested_category=category)
                
                performance.false_negatives = false_negative_logs.count()
                
                # Update calculated metrics
                performance.update_metrics()
                
                self.stdout.write(
                    f"    Total predictions: {performance.total_predictions}, "
                    f"Correct: {performance.correct_predictions}, "
                    f"Accuracy: {performance.accuracy:.2%}"
                )
        
        self.stdout.write(
            self.style.SUCCESS(
                f"Performance metrics update completed! "
                f"Created: {total_created}, Updated: {total_updated}"
            )
        )
        
        # Also update rule match counts
        self.stdout.write("Updating rule match counts...")
        self._update_rule_match_counts(companies, period_start, period_end)
    
    def _update_rule_match_counts(self, companies, period_start, period_end):
        """Update match counts for rules based on logs"""
        from apps.categories.models import CategoryRule
        
        updated_rules = 0
        
        for company in companies:
            rules = CategoryRule.objects.filter(company=company)
            
            for rule in rules:
                # Count how many times this rule was used
                rule_applications = CategorizationLog.objects.filter(
                    transaction__bank_account__company=company,
                    method='rule',
                    rule_used=rule,
                    created_at__date__gte=period_start,
                    created_at__date__lte=period_end
                ).count()
                
                if rule_applications > 0:
                    # Update match count (this is cumulative, so we add to existing)
                    rule.match_count += rule_applications
                    
                    # Calculate accuracy rate for this rule
                    correct_applications = CategorizationLog.objects.filter(
                        transaction__bank_account__company=company,
                        method='rule',
                        rule_used=rule,
                        was_accepted=True,
                        created_at__date__gte=period_start,
                        created_at__date__lte=period_end
                    ).count()
                    
                    # Update accuracy rate (weighted average with existing data)
                    if rule_applications > 0:
                        new_accuracy = correct_applications / rule_applications
                        if rule.accuracy_rate > 0:
                            # Weighted average with existing accuracy
                            rule.accuracy_rate = (rule.accuracy_rate + new_accuracy) / 2
                        else:
                            rule.accuracy_rate = new_accuracy
                    
                    rule.save()
                    updated_rules += 1
                    
                    self.stdout.write(
                        f"  Updated rule '{rule.name}': "
                        f"applications: {rule_applications}, "
                        f"accuracy: {rule.accuracy_rate:.2%}"
                    )
        
        self.stdout.write(
            self.style.SUCCESS(f"Updated {updated_rules} rules")
        )