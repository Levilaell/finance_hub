"""
Command to sync subscription plans with Stripe pricing
This ensures all plans have correct prices and Stripe IDs
Run with: python manage.py sync_subscription_plans
"""
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.db import transaction
from apps.companies.models import SubscriptionPlan
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Sync subscription plans with Stripe pricing and ensure consistency'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be updated without making changes',
        )

    @transaction.atomic
    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No changes will be made'))
        
        # Define the correct plan configuration
        # These values must match:
        # 1. Stripe Dashboard
        # 2. Frontend pricing page
        # 3. Backend models
        plan_configs = {
            'starter': {
                'name': 'Starter',
                'price_monthly': Decimal('49.00'),
                'price_yearly': Decimal('490.00'),
                'stripe_price_id_monthly': 'price_1RkePlPFSVtvOaJKYbiX6TqQ',
                'stripe_price_id_yearly': 'price_1RnPVfPFSVtvOaJKmwxNmUdz',
                'max_transactions': 500,
                'max_bank_accounts': 1,
                'max_ai_requests_per_month': 0,
                'has_ai_categorization': False,
                'enable_ai_insights': False,
                'enable_ai_reports': False,
            },
            'professional': {
                'name': 'Professional',
                'price_monthly': Decimal('149.00'),
                'price_yearly': Decimal('1490.00'),
                'stripe_price_id_monthly': 'price_1RkeQgPFSVtvOaJKgPOzW1SD',
                'stripe_price_id_yearly': 'price_1RnPVRPFSVtvOaJKIWxiSHfm',
                'max_transactions': 2500,
                'max_bank_accounts': 3,
                'max_ai_requests_per_month': 10,
                'has_ai_categorization': True,
                'enable_ai_insights': True,
                'enable_ai_reports': True,
            },
            'enterprise': {
                'name': 'Enterprise',
                'price_monthly': Decimal('349.00'),
                'price_yearly': Decimal('3490.00'),
                'stripe_price_id_monthly': 'price_1RkeVLPFSVtvOaJKY5efgwca',
                'stripe_price_id_yearly': 'price_1RnPV8PFSVtvOaJKoiZxvjPa',
                'max_transactions': 99999,
                'max_bank_accounts': 99999,
                'max_ai_requests_per_month': 99999,
                'has_ai_categorization': True,
                'enable_ai_insights': True,
                'enable_ai_reports': True,
            },
        }
        
        plans_updated = 0
        plans_created = 0
        
        for slug, config in plan_configs.items():
            try:
                plan = SubscriptionPlan.objects.get(slug=slug)
                
                # Check what needs updating
                updates_needed = []
                
                # Check prices
                if plan.price_monthly != config['price_monthly']:
                    updates_needed.append(f"Monthly price: {plan.price_monthly} -> {config['price_monthly']}")
                    if not dry_run:
                        plan.price_monthly = config['price_monthly']
                
                if plan.price_yearly != config['price_yearly']:
                    updates_needed.append(f"Yearly price: {plan.price_yearly} -> {config['price_yearly']}")
                    if not dry_run:
                        plan.price_yearly = config['price_yearly']
                
                # Check Stripe IDs
                if plan.stripe_price_id_monthly != config['stripe_price_id_monthly']:
                    updates_needed.append(f"Monthly Stripe ID: {plan.stripe_price_id_monthly or 'None'} -> {config['stripe_price_id_monthly']}")
                    if not dry_run:
                        plan.stripe_price_id_monthly = config['stripe_price_id_monthly']
                
                if plan.stripe_price_id_yearly != config['stripe_price_id_yearly']:
                    updates_needed.append(f"Yearly Stripe ID: {plan.stripe_price_id_yearly or 'None'} -> {config['stripe_price_id_yearly']}")
                    if not dry_run:
                        plan.stripe_price_id_yearly = config['stripe_price_id_yearly']
                
                # Check limits
                if plan.max_transactions != config['max_transactions']:
                    updates_needed.append(f"Max transactions: {plan.max_transactions} -> {config['max_transactions']}")
                    if not dry_run:
                        plan.max_transactions = config['max_transactions']
                
                if plan.max_bank_accounts != config['max_bank_accounts']:
                    updates_needed.append(f"Max bank accounts: {plan.max_bank_accounts} -> {config['max_bank_accounts']}")
                    if not dry_run:
                        plan.max_bank_accounts = config['max_bank_accounts']
                
                if plan.max_ai_requests_per_month != config['max_ai_requests_per_month']:
                    updates_needed.append(f"Max AI requests: {plan.max_ai_requests_per_month} -> {config['max_ai_requests_per_month']}")
                    if not dry_run:
                        plan.max_ai_requests_per_month = config['max_ai_requests_per_month']
                
                # Check features
                feature_fields = ['has_ai_categorization', 'enable_ai_insights', 'enable_ai_reports']
                for field in feature_fields:
                    if getattr(plan, field) != config.get(field):
                        updates_needed.append(f"{field}: {getattr(plan, field)} -> {config.get(field)}")
                        if not dry_run:
                            setattr(plan, field, config.get(field))
                
                if updates_needed:
                    self.stdout.write(self.style.WARNING(f"\nUpdating {config['name']} plan:"))
                    for update in updates_needed:
                        self.stdout.write(f"  - {update}")
                    
                    if not dry_run:
                        plan.save()
                        plans_updated += 1
                else:
                    self.stdout.write(self.style.SUCCESS(f"{config['name']} plan is already up to date"))
                
            except SubscriptionPlan.DoesNotExist:
                self.stdout.write(self.style.ERROR(f"Plan {slug} does not exist!"))
                self.stdout.write("Run 'python manage.py create_subscription_plans' first")
                plans_created += 1
        
        # Summary
        self.stdout.write("\n" + "="*50)
        if dry_run:
            self.stdout.write(self.style.WARNING(f"DRY RUN SUMMARY:"))
            self.stdout.write(f"  - Plans that would be updated: {plans_updated}")
            self.stdout.write(f"  - Plans that need to be created: {plans_created}")
            self.stdout.write("\nRun without --dry-run to apply changes")
        else:
            self.stdout.write(self.style.SUCCESS(f"SYNC COMPLETE:"))
            self.stdout.write(f"  - Plans updated: {plans_updated}")
            if plans_created > 0:
                self.stdout.write(f"  - Plans need creation: {plans_created}")
                self.stdout.write("  Run 'python manage.py create_subscription_plans' to create missing plans")
            
            # Show current status
            self.stdout.write("\nCurrent plan configuration:")
            for plan in SubscriptionPlan.objects.filter(slug__in=plan_configs.keys()).order_by('display_order'):
                self.stdout.write(f"\n{plan.name}:")
                self.stdout.write(f"  Monthly: R$ {plan.price_monthly} (Stripe: {plan.stripe_price_id_monthly[:20]}...)")
                self.stdout.write(f"  Yearly: R$ {plan.price_yearly} (Stripe: {plan.stripe_price_id_yearly[:20]}...)")
                self.stdout.write(f"  Limits: {plan.max_transactions} transactions, {plan.max_bank_accounts} accounts, {plan.max_ai_requests_per_month} AI requests")