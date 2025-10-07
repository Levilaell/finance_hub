from django.core.management.base import BaseCommand
from djstripe.models import WebhookEndpoint, Account


class Command(BaseCommand):
    help = 'Link webhook endpoints to the Stripe account'

    def handle(self, *args, **options):
        # Get the synced account
        accounts = Account.objects.all()

        if not accounts.exists():
            self.stdout.write(self.style.ERROR('✗ No Stripe Account found. Run sync_stripe_account first.'))
            return

        account = accounts.first()
        self.stdout.write(f'Found Account: {account.id}')

        # Update all webhook endpoints
        endpoints = WebhookEndpoint.objects.filter(djstripe_owner_account__isnull=True)

        if not endpoints.exists():
            self.stdout.write(self.style.WARNING('No webhook endpoints need updating.'))
            return

        updated_count = endpoints.update(djstripe_owner_account=account)

        self.stdout.write(self.style.SUCCESS(f'✓ Updated {updated_count} webhook endpoint(s)'))

        for endpoint in WebhookEndpoint.objects.all():
            self.stdout.write(f'  - {endpoint.url} -> {endpoint.djstripe_owner_account_id}')
