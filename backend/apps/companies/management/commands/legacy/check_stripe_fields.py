"""
Check if Stripe price ID fields exist in database
"""
from django.core.management.base import BaseCommand
from django.db import connection
from apps.companies.models import SubscriptionPlan


class Command(BaseCommand):
    help = 'Check if Stripe price ID fields exist'

    def handle(self, *args, **options):
        self.stdout.write("=== CHECKING STRIPE FIELDS ===\n")
        
        # Check if columns exist in database
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'subscription_plans' 
                AND column_name IN ('stripe_price_id_monthly', 'stripe_price_id_yearly')
                ORDER BY column_name;
            """)
            columns = [row[0] for row in cursor.fetchall()]
        
        if len(columns) == 2:
            self.stdout.write(self.style.SUCCESS(
                "✓ Both Stripe price ID fields exist in database"
            ))
            
            # Check if they have data
            plans = SubscriptionPlan.objects.all()
            for plan in plans:
                self.stdout.write(f"\n{plan.name}:")
                if plan.stripe_price_id_monthly:
                    self.stdout.write(f"  Monthly: {plan.stripe_price_id_monthly}")
                else:
                    self.stdout.write(self.style.ERROR("  Monthly: NOT SET"))
                    
                if plan.stripe_price_id_yearly:
                    self.stdout.write(f"  Yearly: {plan.stripe_price_id_yearly}")
                else:
                    self.stdout.write(self.style.ERROR("  Yearly: NOT SET"))
        else:
            self.stdout.write(self.style.ERROR(
                "✗ Stripe price ID fields are missing!"
            ))
            self.stdout.write("\nRun these commands:")
            self.stdout.write("python manage.py makemigrations")
            self.stdout.write("python manage.py migrate")