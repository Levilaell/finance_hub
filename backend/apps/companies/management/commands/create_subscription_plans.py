"""
Create default subscription plans
"""
from decimal import Decimal

from django.core.management.base import BaseCommand

from apps.companies.models import SubscriptionPlan


class Command(BaseCommand):
    help = 'Create default subscription plans'

    def handle(self, *args, **options):
        plans = [
            {
                'name': 'Starter',
                'slug': 'starter',
                'plan_type': 'starter',
                'price_monthly': Decimal('29.90'),
                'price_yearly': Decimal('299.00'),
                'max_transactions': 500,
                'max_bank_accounts': 1,
                'max_users': 1,
                'has_ai_categorization': True,
                'has_advanced_reports': False,
                'has_api_access': False,
                'has_accountant_access': False,
            },
            {
                'name': 'Pro',
                'slug': 'pro',
                'plan_type': 'pro',
                'price_monthly': Decimal('79.90'),
                'price_yearly': Decimal('799.00'),
                'max_transactions': 2000,
                'max_bank_accounts': 3,
                'max_users': 3,
                'has_ai_categorization': True,
                'has_advanced_reports': True,
                'has_api_access': False,
                'has_accountant_access': True,
            },
            {
                'name': 'Enterprise',
                'slug': 'enterprise',
                'plan_type': 'enterprise',
                'price_monthly': Decimal('199.90'),
                'price_yearly': Decimal('1999.00'),
                'max_transactions': 10000,
                'max_bank_accounts': 10,
                'max_users': 10,
                'has_ai_categorization': True,
                'has_advanced_reports': True,
                'has_api_access': True,
                'has_accountant_access': True,
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
            self.style.SUCCESS('Successfully created/updated subscription plans')
        )