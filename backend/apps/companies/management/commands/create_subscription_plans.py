"""
Simplified command to create subscription plans
"""
from decimal import Decimal
from django.core.management.base import BaseCommand
from apps.companies.models import SubscriptionPlan


class Command(BaseCommand):
    help = 'Create or update subscription plans'

    def handle(self, *args, **options):
        plans = [
            {
                'name': 'Starter',
                'slug': 'starter',
                'plan_type': 'standard',
                'trial_days': 14,
                'price_monthly': Decimal('29.90'),
                'price_yearly': Decimal('299.00'),
                'max_transactions': 500,
                'max_bank_accounts': 2,
                'max_ai_requests_per_month': 50,
                'has_ai_categorization': False,
                'enable_ai_insights': False,
                'enable_ai_reports': False,
                'has_advanced_reports': False,
                'has_api_access': False,
                'has_accountant_access': False,
                'has_priority_support': False,
                'display_order': 1,
                'is_active': True,
            },
            {
                'name': 'Professional',
                'slug': 'professional',
                'plan_type': 'standard',
                'trial_days': 14,
                'price_monthly': Decimal('59.90'),
                'price_yearly': Decimal('599.00'),
                'max_transactions': 2000,
                'max_bank_accounts': 5,
                'max_ai_requests_per_month': 200,
                'has_ai_categorization': True,
                'enable_ai_insights': True,
                'enable_ai_reports': True,
                'has_advanced_reports': True,
                'has_api_access': False,
                'has_accountant_access': True,
                'has_priority_support': True,
                'display_order': 2,
                'is_active': True,
            },
            {
                'name': 'Enterprise',
                'slug': 'enterprise',
                'plan_type': 'enterprise',
                'trial_days': 30,
                'price_monthly': Decimal('199.90'),
                'price_yearly': Decimal('1999.00'),
                'max_transactions': 99999,  # Effectively unlimited
                'max_bank_accounts': 99999,  # Effectively unlimited
                'max_ai_requests_per_month': 99999,  # Effectively unlimited
                'has_ai_categorization': True,
                'enable_ai_insights': True,
                'enable_ai_reports': True,
                'has_advanced_reports': True,
                'has_api_access': True,
                'has_accountant_access': True,
                'has_priority_support': True,
                'display_order': 3,
                'is_active': True,
            },
        ]

        for plan_data in plans:
            plan, created = SubscriptionPlan.objects.update_or_create(
                slug=plan_data['slug'],
                defaults=plan_data
            )
            
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'Created plan: {plan.name}')
                )
            else:
                self.stdout.write(
                    self.style.SUCCESS(f'Updated plan: {plan.name}')
                )

        self.stdout.write(
            self.style.SUCCESS('Successfully created/updated all plans')
        )