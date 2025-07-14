"""
Management command to seed initial subscription plans
"""
from django.core.management.base import BaseCommand
from apps.companies.models import SubscriptionPlan


class Command(BaseCommand):
    help = 'Create initial subscription plans'

    def handle(self, *args, **options):
        plans = [
            {
                'name': 'Grátis',
                'slug': 'free',
                'plan_type': 'free',
                'price_monthly': 0,
                'price_yearly': 0,
                'max_transactions': 100,
                'max_bank_accounts': 1,
                'max_users': 1,
                'has_ai_categorization': False,
                'enable_ai_insights': False,
                'enable_ai_reports': False,
                'max_ai_requests_per_month': 0,
                'has_advanced_reports': False,
                'has_api_access': False,
                'has_accountant_access': False,
                'has_priority_support': False,
                'display_order': 1,
            },
            {
                'name': 'Starter',
                'slug': 'starter',
                'plan_type': 'starter',
                'price_monthly': 49,
                'price_yearly': 490,  # ~17% de desconto
                'max_transactions': 500,
                'max_bank_accounts': 2,
                'max_users': 3,
                'has_ai_categorization': False,
                'enable_ai_insights': False,
                'enable_ai_reports': False,
                'max_ai_requests_per_month': 0,
                'has_advanced_reports': True,
                'has_api_access': False,
                'has_accountant_access': False,
                'has_priority_support': True,
                'display_order': 2,
            },
            {
                'name': 'Profissional',
                'slug': 'professional',
                'plan_type': 'professional',
                'price_monthly': 149,
                'price_yearly': 1490,  # ~17% de desconto
                'max_transactions': 2000,
                'max_bank_accounts': 5,
                'max_users': 10,
                'has_ai_categorization': True,
                'enable_ai_insights': True,
                'enable_ai_reports': True,
                'max_ai_requests_per_month': 1000,
                'has_advanced_reports': True,
                'has_api_access': False,
                'has_accountant_access': True,
                'has_priority_support': True,
                'display_order': 3,
            },
            {
                'name': 'Empresarial',
                'slug': 'enterprise',
                'plan_type': 'enterprise',
                'price_monthly': 449,
                'price_yearly': 4490,  # ~17% de desconto
                'max_transactions': 999999,  # Praticamente ilimitado
                'max_bank_accounts': 999,    # Praticamente ilimitado
                'max_users': 999,            # Praticamente ilimitado
                'has_ai_categorization': True,
                'enable_ai_insights': True,
                'enable_ai_reports': True,
                'max_ai_requests_per_month': 999999,  # Praticamente ilimitado
                'has_advanced_reports': True,
                'has_api_access': True,
                'has_accountant_access': True,
                'has_priority_support': True,
                'display_order': 4,
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
            self.style.SUCCESS('Successfully created/updated all subscription plans')
        )