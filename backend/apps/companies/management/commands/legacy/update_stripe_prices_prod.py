"""
Update Stripe price IDs in production
"""
from django.core.management.base import BaseCommand
from apps.companies.models import SubscriptionPlan


class Command(BaseCommand):
    help = 'Update Stripe price IDs in production database'

    def handle(self, *args, **options):
        self.stdout.write("=== UPDATING STRIPE PRICE IDs ===\n")
        
        updates = []
        errors = []
        
        # Starter
        try:
            plan = SubscriptionPlan.objects.get(slug='starter')
            plan.stripe_price_id_monthly = 'price_1RkePlPFSVtvOaJKYbiX6TqQ'
            plan.stripe_price_id_yearly = 'price_1RnPVfPFSVtvOaJKmwxNmUdz'
            plan.save()
            updates.append(f"✓ {plan.name} updated")
        except Exception as e:
            errors.append(f"✗ Starter: {str(e)}")
        
        # Professional
        try:
            plan = SubscriptionPlan.objects.get(slug='professional')
            plan.stripe_price_id_monthly = 'price_1RkeQgPFSVtvOaJKgPOzW1SD'
            plan.stripe_price_id_yearly = 'price_1RnPVRPFSVtvOaJKIWxiSHfm'
            plan.save()
            updates.append(f"✓ {plan.name} updated")
        except Exception as e:
            errors.append(f"✗ Professional: {str(e)}")
        
        # Enterprise
        try:
            plan = SubscriptionPlan.objects.get(slug='enterprise')
            plan.stripe_price_id_monthly = 'price_1RkeVLPFSVtvOaJKY5efgwca'
            plan.stripe_price_id_yearly = 'price_1RnPV8PFSVtvOaJKoiZxvjPa'
            plan.save()
            updates.append(f"✓ {plan.name} updated")
        except Exception as e:
            errors.append(f"✗ Enterprise: {str(e)}")
        
        # Show results
        if updates:
            self.stdout.write("\nSuccessful updates:")
            for update in updates:
                self.stdout.write(self.style.SUCCESS(update))
        
        if errors:
            self.stdout.write("\nErrors:")
            for error in errors:
                self.stdout.write(self.style.ERROR(error))
        
        # Verify final state
        self.stdout.write("\n" + "="*50)
        self.stdout.write("FINAL STATE:\n")
        
        for plan in SubscriptionPlan.objects.filter(is_active=True):
            self.stdout.write(f"\n{plan.name}:")
            self.stdout.write(f"  Monthly: {plan.stripe_price_id_monthly or 'NOT SET'}")
            self.stdout.write(f"  Yearly: {plan.stripe_price_id_yearly or 'NOT SET'}")