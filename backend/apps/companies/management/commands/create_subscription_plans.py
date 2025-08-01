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
                'price_monthly': Decimal('29.90'),
                'price_yearly': Decimal('299.00'),
                'max_transactions': 500,
                'max_bank_accounts': 2,
                'max_ai_requests': 50,
                'has_ai_insights': False,
                'has_advanced_reports': False,
                'display_order': 1,
            },
            {
                'name': 'Professional',
                'slug': 'professional',
                'price_monthly': Decimal('59.90'),
                'price_yearly': Decimal('599.00'),
                'max_transactions': 2000,
                'max_bank_accounts': 5,
                'max_ai_requests': 200,
                'has_ai_insights': True,
                'has_advanced_reports': True,
                'display_order': 2,
            },
            {
                'name': 'Enterprise',
                'slug': 'enterprise',
                'price_monthly': Decimal('199.90'),
                'price_yearly': Decimal('1999.00'),
                'max_transactions': 99999,  # Effectively unlimited
                'max_bank_accounts': 99999,  # Effectively unlimited
                'max_ai_requests': 99999,  # Effectively unlimited
                'has_ai_insights': True,
                'has_advanced_reports': True,
                'display_order': 3,
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