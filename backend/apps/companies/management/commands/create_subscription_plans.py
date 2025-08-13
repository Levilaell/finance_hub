"""
Command to create or update subscription plans with Stripe integration
Syncs pricing with Stripe dashboard and frontend
"""
from decimal import Decimal
from django.core.management.base import BaseCommand
from apps.companies.models import SubscriptionPlan


class Command(BaseCommand):
    help = 'Create or update subscription plans with correct Stripe pricing'

    def handle(self, *args, **options):
        """
        Plans synchronized with:
        - Stripe Dashboard (price IDs from actual products)
        - Frontend pricing page
        - Backend models
        """
        plans = [
            {
                'name': 'Starter',
                'slug': 'starter',
                'plan_type': 'standard',
                'trial_days': 14,
                # Prices synced with Stripe and frontend
                'price_monthly': Decimal('49.00'),  # R$ 49/mês
                'price_yearly': Decimal('490.00'),   # R$ 490/ano
                # Stripe Price IDs from dashboard
                'stripe_price_id_monthly': 'price_1RkePtPFSVtvOaJKYbiX6TqQ',  # prod_Sg0QBa3Hbj97lf monthly
                'stripe_price_id_yearly': 'price_1RnPVfPFSVtvOaJKmwzNmUdz',   # prod_Sg0QBa3Hbj97lf yearly
                # Limits
                'max_transactions': 500,
                'max_bank_accounts': 1,  # Updated to match frontend
                'max_ai_requests_per_month': 0,  # Starter doesn't have AI
                # Features
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
                # Prices synced with Stripe and frontend
                'price_monthly': Decimal('149.00'),  # R$ 149/mês
                'price_yearly': Decimal('1490.00'),  # R$ 1490/ano
                # Stripe Price IDs from dashboard
                'stripe_price_id_monthly': 'price_1RkeQgPFSVtvOaJKgPQzW1SD',  # prod_Sg0RnnnAC68Di5R monthly
                'stripe_price_id_yearly': 'price_1RnPVRPFSVtvOaJKlWxiSHnn',   # prod_Sg0RnnnAC68Di5R yearly
                # Limits
                'max_transactions': 2500,  # Updated to match frontend
                'max_bank_accounts': 3,     # Updated to match frontend
                'max_ai_requests_per_month': 10,  # 10 AI interactions/month
                # Features
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
                # Prices synced with Stripe and frontend
                'price_monthly': Decimal('349.00'),  # R$ 349/mês
                'price_yearly': Decimal('3490.00'),  # R$ 3490/ano
                # Stripe Price IDs from dashboard
                'stripe_price_id_monthly': 'price_1RkeMJPFSVtvOaJKuIZxvjPa',  # prod_Sg0WMkmUeqiQUm monthly
                'stripe_price_id_yearly': 'price_1RnPV8PFSVtvOaJKuIZxvjPa',   # prod_Sg0WMkmUeqiQUm yearly
                # Limits (unlimited)
                'max_transactions': 99999,  # Effectively unlimited
                'max_bank_accounts': 99999,  # Effectively unlimited
                'max_ai_requests_per_month': 99999,  # Unlimited AI
                # Features (all enabled)
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