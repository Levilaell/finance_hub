"""
Management command to create test performance data for development
This command creates realistic categorization logs and performance metrics for testing
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import date, timedelta
from apps.categories.models import CategoryPerformance, CategorizationLog, CategoryRule
from apps.companies.models import Company
from apps.banking.models import TransactionCategory, Transaction, BankAccount
import random


class Command(BaseCommand):
    help = 'Create test performance data for development and testing'

    def add_arguments(self, parser):
        parser.add_argument(
            '--company-id',
            type=int,
            help='Create data for specific company only'
        )
        parser.add_argument(
            '--logs-count',
            type=int,
            default=100,
            help='Number of categorization logs to create (default: 100)'
        )

    def handle(self, *args, **options):
        company_id = options.get('company_id')
        logs_count = options['logs_count']
        
        self.stdout.write("Creating test performance data...")
        
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
        
        if not companies.exists():
            self.stdout.write(
                self.style.ERROR("No companies found. Create a company first.")
            )
            return
        
        # Get categories
        categories = list(TransactionCategory.objects.filter(is_active=True))
        if not categories:
            self.stdout.write(
                self.style.ERROR("No categories found. Create some categories first.")
            )
            return
        
        total_logs_created = 0
        
        for company in companies:
            self.stdout.write(f"Creating data for company: {company.name}")
            
            # Get bank accounts for this company
            bank_accounts = list(BankAccount.objects.filter(company=company))
            if not bank_accounts:
                self.stdout.write(f"  No bank accounts found for {company.name}, skipping...")
                continue
            
            # Get transactions for this company
            transactions = list(Transaction.objects.filter(
                bank_account__company=company
            ).order_by('-transaction_date')[:logs_count])
            
            if not transactions:
                self.stdout.write(f"  No transactions found for {company.name}, skipping...")
                continue
            
            # Create categorization logs
            logs_for_company = min(logs_count, len(transactions))
            self.stdout.write(f"  Creating {logs_for_company} categorization logs...")
            
            for i, transaction in enumerate(transactions[:logs_for_company]):
                # Randomly select method (AI vs Rules with realistic distribution)
                method = random.choices(
                    ['ai', 'rule', 'manual'], 
                    weights=[0.6, 0.3, 0.1]  # 60% AI, 30% rules, 10% manual
                )[0]
                
                # Select a category (with some bias towards certain categories)
                suggested_category = random.choice(categories)
                
                # Determine if categorization was correct (realistic accuracy rates)
                if method == 'ai':
                    accuracy_rate = 0.85  # 85% accuracy for AI
                elif method == 'rule':
                    accuracy_rate = 0.92  # 92% accuracy for rules
                else:
                    accuracy_rate = 0.98  # 98% accuracy for manual
                
                was_accepted = random.random() < accuracy_rate
                
                # Select final category if correction was needed
                final_category = suggested_category if was_accepted else random.choice(categories)
                
                # Calculate confidence score based on method
                if method == 'ai':
                    confidence_score = random.uniform(0.6, 0.95)
                elif method == 'rule':
                    confidence_score = random.uniform(0.85, 1.0)
                else:
                    confidence_score = 1.0
                
                # Random processing time
                processing_time_ms = random.randint(50, 300)
                
                # Create log with date in the last 30 days
                created_at = timezone.now() - timedelta(
                    days=random.randint(0, 29),
                    hours=random.randint(0, 23),
                    minutes=random.randint(0, 59)
                )
                
                # Get or create a rule if method is 'rule'
                rule_used = None
                if method == 'rule':
                    # Try to get existing rule for this category
                    rule_used = CategoryRule.objects.filter(
                        company=company,
                        category=suggested_category,
                        is_active=True
                    ).first()
                    
                    # Create a rule if none exists
                    if not rule_used:
                        rule_used = CategoryRule.objects.create(
                            company=company,
                            category=suggested_category,
                            name=f"Auto Rule for {suggested_category.name}",
                            rule_type='keyword',
                            conditions={'keywords': [suggested_category.name.lower()]},
                            priority=random.randint(1, 10),
                            created_by_id=1  # Assuming user with ID 1 exists
                        )
                
                log = CategorizationLog.objects.create(
                    transaction=transaction,
                    method=method,
                    suggested_category=suggested_category,
                    confidence_score=confidence_score,
                    processing_time_ms=processing_time_ms,
                    rule_used=rule_used,
                    ai_model_version='gpt-4o-mini' if method == 'ai' else '',
                    was_accepted=was_accepted,
                    final_category=final_category
                )
                
                # Update the transaction's actual category occasionally
                if random.random() < 0.8:  # 80% of transactions get categorized
                    transaction.category = final_category
                    transaction.is_ai_categorized = (method == 'ai')
                    transaction.ai_category_confidence = confidence_score if method == 'ai' else None
                    transaction.save()
                
                # Manually set the created_at to spread logs over time
                log.created_at = created_at
                log.save()
                
                total_logs_created += 1
            
            self.stdout.write(f"  Created {logs_for_company} logs for {company.name}")
        
        # Now create/update performance metrics
        self.stdout.write("Creating performance metrics...")
        
        period_start = date.today() - timedelta(days=30)
        period_end = date.today()
        
        total_metrics_created = 0
        
        for company in companies:
            # Get categories that have logs
            category_ids = CategorizationLog.objects.filter(
                transaction__bank_account__company=company,
                created_at__date__gte=period_start
            ).values_list('suggested_category_id', flat=True).distinct()
            
            for category_id in category_ids:
                if not category_id:
                    continue
                
                try:
                    category = TransactionCategory.objects.get(id=category_id)
                except TransactionCategory.DoesNotExist:
                    continue
                
                # Create performance record
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
                    total_metrics_created += 1
                
                # Calculate metrics from logs
                category_logs = CategorizationLog.objects.filter(
                    transaction__bank_account__company=company,
                    suggested_category=category,
                    created_at__date__gte=period_start
                )
                
                performance.total_predictions = category_logs.count()
                performance.correct_predictions = category_logs.filter(was_accepted=True).count()
                
                # Calculate false positives and negatives
                performance.false_positives = category_logs.filter(
                    was_accepted=False,
                    final_category__isnull=False
                ).exclude(final_category=category).count()
                
                false_negative_logs = CategorizationLog.objects.filter(
                    transaction__bank_account__company=company,
                    final_category=category,
                    created_at__date__gte=period_start
                ).exclude(suggested_category=category)
                
                performance.false_negatives = false_negative_logs.count()
                
                # Update calculated metrics
                performance.update_metrics()
        
        # Update rule match counts
        self.stdout.write("Updating rule statistics...")
        updated_rules = 0
        
        for company in companies:
            rules = CategoryRule.objects.filter(company=company)
            for rule in rules:
                rule_logs = CategorizationLog.objects.filter(
                    transaction__bank_account__company=company,
                    rule_used=rule,
                    created_at__date__gte=period_start
                )
                
                rule.match_count = rule_logs.count()
                
                if rule.match_count > 0:
                    correct_count = rule_logs.filter(was_accepted=True).count()
                    rule.accuracy_rate = correct_count / rule.match_count
                    updated_rules += 1
                
                rule.save()
        
        self.stdout.write(
            self.style.SUCCESS(
                f"Test data creation completed!\n"
                f"  Categorization logs created: {total_logs_created}\n"
                f"  Performance metrics created: {total_metrics_created}\n"
                f"  Rules updated: {updated_rules}"
            )
        )