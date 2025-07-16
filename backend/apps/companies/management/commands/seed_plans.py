"""
Management command to seed initial subscription plans
NO FREE PLAN - Only paid plans with 14-day trial
"""
from django.core.management.base import BaseCommand
from apps.companies.models import SubscriptionPlan


class Command(BaseCommand):
    help = 'Create initial subscription plans (Starter, Professional, Enterprise)'

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
                'has_ai_categorization': False,  # Pluggy handles categorization
                'enable_ai_insights': False,      # NO AI
                'enable_ai_reports': False,       # NO AI
                'max_ai_requests_per_month': 0,   # NO AI
                'has_advanced_reports': True,
                'has_api_access': False,
                'has_accountant_access': False,
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
                'has_ai_categorization': False,  # Pluggy handles categorization
                'enable_ai_insights': True,       # WITH AI
                'enable_ai_reports': True,        # WITH AI
                'max_ai_requests_per_month': 1000,
                'has_advanced_reports': True,
                'has_api_access': False,
                'has_accountant_access': True,
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
                'has_ai_categorization': False,  # Pluggy handles categorization
                'enable_ai_insights': True,       # WITH AI
                'enable_ai_reports': True,        # WITH AI
                'max_ai_requests_per_month': 999999,  # Unlimited
                'has_advanced_reports': True,
                'has_api_access': True,
                'has_accountant_access': True,
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

        # Ensure no free plan exists
        free_plans = SubscriptionPlan.objects.filter(slug='free')
        if free_plans.exists():
            free_plans.delete()
            self.stdout.write(
                self.style.WARNING('Removed free plan(s)')
            )

        self.stdout.write(
            self.style.SUCCESS('Successfully created/updated all subscription plans')
        )