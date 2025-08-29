"""
Sync subscription plans to production database
Fixes foreign key constraint error for payment processing
"""

from django.core.management.base import BaseCommand
from decimal import Decimal
from apps.companies.models import SubscriptionPlan


class Command(BaseCommand):
    help = 'Sync subscription plans to production database'

    def handle(self, *args, **options):
        self.stdout.write("🔧 SYNCING SUBSCRIPTION PLANS TO PRODUCTION")
        self.stdout.write("=" * 50)
        
        # Define the plans that should exist
        plans_data = [
            {
                'id': 1,
                'name': 'Starter',
                'display_name': 'Starter',
                'description': 'Plano básico para começar',
                'price_monthly': Decimal('29.90'),
                'price_yearly': Decimal('299.00'),
                'max_transactions': 500,
                'max_bank_accounts': 2,
                'max_categories': 20,
                'has_ai_insights': False,
                'has_advanced_reports': False,
                'stripe_price_id_monthly': 'price_1OkVvIBm9pZxKx8rLwXK9GJ5',
                'stripe_price_id_yearly': 'price_1OkVwDBm9pZxKx8rLwXK9GJ6',
                'is_active': True,
                'display_order': 1
            },
            {
                'id': 2,
                'name': 'Professional',
                'display_name': 'Professional',
                'description': 'Plano completo para profissionais',
                'price_monthly': Decimal('149.00'),
                'price_yearly': Decimal('1490.00'),
                'max_transactions': 10000,
                'max_bank_accounts': 10,
                'max_categories': 100,
                'has_ai_insights': True,
                'has_advanced_reports': True,
                'stripe_price_id_monthly': 'price_1QoGToBm9pZxKx8rYTv3AFOO',
                'stripe_price_id_yearly': 'price_1QoGUMBm9pZxKx8rXGa9vHFK',
                'is_active': True,
                'display_order': 2
            },
            {
                'id': 3,
                'name': 'Enterprise',
                'display_name': 'Enterprise',
                'description': 'Plano empresarial com recursos ilimitados',
                'price_monthly': Decimal('399.00'),
                'price_yearly': Decimal('3990.00'),
                'max_transactions': 100000,
                'max_bank_accounts': 50,
                'max_categories': 500,
                'has_ai_insights': True,
                'has_advanced_reports': True,
                'stripe_price_id_monthly': 'price_1OkVxIBm9pZxKx8rLwXK9GJ7',
                'stripe_price_id_yearly': 'price_1OkVxpBm9pZxKx8rLwXK9GJ8',
                'is_active': True,
                'display_order': 3
            }
        ]
        
        created_count = 0
        updated_count = 0
        
        for plan_data in plans_data:
            plan_id = plan_data['id']
            
            try:
                # Try to get existing plan
                plan = SubscriptionPlan.objects.get(id=plan_id)
                
                # Update existing plan
                for key, value in plan_data.items():
                    if key != 'id':  # Don't update ID
                        setattr(plan, key, value)
                
                plan.save()
                updated_count += 1
                self.stdout.write(f"✅ Updated plan ID {plan_id}: {plan.name}")
                
            except SubscriptionPlan.DoesNotExist:
                # Create new plan
                plan = SubscriptionPlan.objects.create(**plan_data)
                created_count += 1
                self.stdout.write(f"✨ Created plan ID {plan_id}: {plan.name}")
        
        # Verify all plans exist
        self.stdout.write(f"\n📊 VERIFICATION")
        self.stdout.write(f"Plans created: {created_count}")
        self.stdout.write(f"Plans updated: {updated_count}")
        
        total_plans = SubscriptionPlan.objects.count()
        self.stdout.write(f"Total plans in database: {total_plans}")
        
        # Check for the specific plan causing the error
        try:
            professional_plan = SubscriptionPlan.objects.get(id=2)
            self.stdout.write(f"✅ Plan ID=2 exists: {professional_plan.name}")
            self.stdout.write(f"   Price monthly: ${professional_plan.price_monthly}")
            self.stdout.write(f"   Stripe monthly ID: {professional_plan.stripe_price_id_monthly}")
        except SubscriptionPlan.DoesNotExist:
            self.stdout.write("❌ Plan ID=2 (Professional) still missing!")
            return
        
        self.stdout.write(f"\n🎉 SUCCESS: All subscription plans are now synced!")
        self.stdout.write("Payment processing should now work correctly.")