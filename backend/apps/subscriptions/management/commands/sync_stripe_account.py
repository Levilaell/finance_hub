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

            # Sync to djstripe database
            account, created = Account.objects.update_or_create(
                id=stripe_account.id,
                defaults={
                    'livemode': stripe_account.livemode,
                }
            )

            # Force sync to update all fields
            account.sync_from_stripe_data(stripe_account)

            if created:
                self.stdout.write(self.style.SUCCESS(f'✓ Created Account: {account.id}'))
            else:
                self.stdout.write(self.style.SUCCESS(f'✓ Updated Account: {account.id}'))

            self.stdout.write(self.style.SUCCESS(f'  Mode: {"LIVE" if account.livemode else "TEST"}'))
            self.stdout.write(self.style.SUCCESS(f'  Business Name: {account.business_profile.get("name", "N/A") if account.business_profile else "N/A"}'))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'✗ Error syncing account: {str(e)}'))
            raise
