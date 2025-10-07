from django.core.management.base import BaseCommand
from django.conf import settings
import stripe
from djstripe.models import Account


class Command(BaseCommand):
    help = 'Sync Stripe Account to fix webhook errors'

    def handle(self, *args, **options):
        stripe.api_key = settings.STRIPE_SECRET_KEY

        self.stdout.write(self.style.WARNING('Syncing Stripe Account...'))

        try:
            # Fetch account from Stripe
            stripe_account = stripe.Account.retrieve()

            self.stdout.write(f'Retrieved Stripe Account: {stripe_account.id}')

            # Sync using djstripe's built-in method
            account = Account.sync_from_stripe_data(stripe_account)

            self.stdout.write(self.style.SUCCESS(f'✓ Synced Account: {account.id}'))
            self.stdout.write(self.style.SUCCESS(f'  Mode: {"LIVE" if settings.STRIPE_LIVE_MODE else "TEST"}'))

            if hasattr(account, 'business_profile') and account.business_profile:
                business_name = account.business_profile.get("name", "N/A")
                self.stdout.write(self.style.SUCCESS(f'  Business Name: {business_name}'))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'✗ Error syncing account: {str(e)}'))
            raise
