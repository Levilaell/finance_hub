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
                'name': 'Grátis',
                'slug': 'free',
                'plan_type': 'free',  # Using starter as plan_type since free is not in choices
                'price_monthly': Decimal('0.00'),
                'price_yearly': Decimal('0.00'),
                'max_transactions': 100,
                'max_bank_accounts': 1,
                'max_users': 1,
                'has_ai_categorization': False,
                'has_advanced_reports': False,
                'has_api_access': False,
                'has_accountant_access': False,
            },
            {
                'name': 'Starter',
                'slug': 'starter',
                'plan_type': 'starter',
                'price_monthly': Decimal('49.00'),
                'price_yearly': Decimal('490.00'),
                'max_transactions': 500,
                'max_bank_accounts': 2,
                'max_users': 3,
                'has_ai_categorization': False,
                'has_advanced_reports': True,
                'has_api_access': False,
                'has_accountant_access': False,
            },
            {
                'name': 'Profissional',
                'slug': 'professional',
                'plan_type': 'professional',
                'price_monthly': Decimal('149.00'),
                'price_yearly': Decimal('1490.00'),
                'max_transactions': 2000,
                'max_bank_accounts': 5,
                'max_users': 10,
                'has_ai_categorization': True,
                'has_advanced_reports': True,
                'has_api_access': False,
                'has_accountant_access': True,
            },
            {
                'name': 'Empresarial',
                'slug': 'enterprise',
                'plan_type': 'enterprise',
                'price_monthly': Decimal('449.00'),
                'price_yearly': Decimal('4490.00'),
                'max_transactions': 999999,  # Using large number instead of -1
                'max_bank_accounts': 999,
                'max_users': 999,
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