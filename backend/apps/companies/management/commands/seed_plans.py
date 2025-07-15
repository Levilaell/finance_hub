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
                'name': 'Starter',
                'slug': 'starter',
                'plan_type': 'starter',
                'price_monthly': 49,
                'price_yearly': 490,
                'max_transactions': 500,
                'max_bank_accounts': 2,
                'max_users': 3,
                'has_ai_categorization': False,  # Não é mais relevante (Pluggy faz)
                'enable_ai_insights': False,      # SEM IA
                'enable_ai_reports': False,       # SEM IA
                'max_ai_requests_per_month': 0,   # SEM IA
                'has_advanced_reports': True,
                'has_api_access': False,
                'has_priority_support': True,
                'display_order': 1,
            },
            {
                'name': 'Profissional',
                'slug': 'professional',
                'plan_type': 'professional',
                'price_monthly': 149,
                'price_yearly': 1490,
                'max_transactions': 2000,
                'max_bank_accounts': 5,
                'max_users': 10,
                'has_ai_categorization': False,  # Não é mais relevante
                'enable_ai_insights': True,       # COM IA
                'enable_ai_reports': True,        # COM IA
                'max_ai_requests_per_month': 1000,
                'has_advanced_reports': True,
                'has_api_access': False,
                'has_priority_support': True,
                'display_order': 2,
            },
            {
                'name': 'Empresarial',
                'slug': 'enterprise',
                'plan_type': 'enterprise',
                'price_monthly': 449,
                'price_yearly': 4490,
                'max_transactions': 999999,
                'max_bank_accounts': 999,
                'max_users': 999,
                'has_ai_categorization': False,  # Não é mais relevante
                'enable_ai_insights': True,       # COM IA
                'enable_ai_reports': True,        # COM IA
                'max_ai_requests_per_month': 999999,  # Ilimitado
                'has_advanced_reports': True,
                'has_api_access': True,
                'has_priority_support': True,
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
            self.style.SUCCESS('Successfully created/updated all subscription plans')
        )