from django.core.management.base import BaseCommand
from django.conf import settings
from djstripe.models import WebhookEndpoint, Account


class Command(BaseCommand):
    help = 'Link webhook endpoints to the correct Stripe account'

    def handle(self, *args, **options):
        # Get the correct account (the one with livemode matching settings)
        correct_account = Account.objects.filter(
            livemode=settings.STRIPE_LIVE_MODE
        ).first()

        if not correct_account:
            self.stdout.write(self.style.ERROR(
                f'✗ No Account found with livemode={settings.STRIPE_LIVE_MODE}. '
                f'Run sync_stripe_account first.'
            ))
            return

        self.stdout.write(f'Using Account: {correct_account.id} (livemode={correct_account.livemode})')

        # Show all accounts for clarity
        self.stdout.write('\nAll Accounts in database:')
        for acc in Account.objects.all():
            self.stdout.write(f'  - {acc.id}: livemode={acc.livemode}')

        # Update ALL webhook endpoints to use the correct account
        endpoints = WebhookEndpoint.objects.all()

        if not endpoints.exists():
            self.stdout.write(self.style.WARNING('No webhook endpoints found.'))
            return

        self.stdout.write(f'\nUpdating {endpoints.count()} webhook endpoint(s)...')

        for endpoint in endpoints:
            old_account = endpoint.djstripe_owner_account_id
            endpoint.djstripe_owner_account = correct_account
            endpoint.save()
            self.stdout.write(
                f'  ✓ {endpoint.url}\n'
                f'    OLD: {old_account} -> NEW: {correct_account.id}'
            )

        self.stdout.write(self.style.SUCCESS('\n✓ All webhook endpoints updated successfully!'))
