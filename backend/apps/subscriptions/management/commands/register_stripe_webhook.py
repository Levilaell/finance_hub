"""
Management command to register Stripe webhook endpoint in djstripe database.

This command creates a WebhookEndpoint record in the database, which is required
for djstripe to accept incoming webhook requests.
"""
from django.core.management.base import BaseCommand
from django.conf import settings
from djstripe.models import WebhookEndpoint
import stripe


class Command(BaseCommand):
    help = 'Register Stripe webhook endpoint in djstripe database'

    def add_arguments(self, parser):
        parser.add_argument(
            '--url',
            type=str,
            help='Full webhook URL (e.g., https://your-domain.railway.app/stripe/webhook/)',
            required=False,
        )
        parser.add_argument(
            '--create-in-stripe',
            action='store_true',
            help='Also create the endpoint in Stripe Dashboard',
        )

    def handle(self, *args, **options):
        # Configure Stripe
        stripe.api_key = settings.STRIPE_SECRET_KEY

        webhook_url = options.get('url')
        create_in_stripe = options.get('create_in_stripe', False)

        self.stdout.write(self.style.WARNING('\n=== Stripe Webhook Registration ===\n'))

        # Check existing endpoints
        existing_endpoints = WebhookEndpoint.objects.all()

        if existing_endpoints.exists():
            self.stdout.write(self.style.WARNING('Existing webhook endpoints:'))
            for ep in existing_endpoints:
                self.stdout.write(f'  - ID: {ep.id}')
                self.stdout.write(f'    URL: {ep.url}')
                self.stdout.write(f'    Secret: {ep.secret[:20]}...' if ep.secret else '    Secret: None')
                self.stdout.write(f'    Status: {ep.status}\n')

        # Option 1: Sync from Stripe
        if create_in_stripe and webhook_url:
            self.stdout.write(self.style.SUCCESS('\n📡 Creating webhook endpoint in Stripe...'))

            try:
                # Create endpoint in Stripe
                stripe_endpoint = stripe.WebhookEndpoint.create(
                    url=webhook_url,
                    enabled_events=[
                        'customer.subscription.created',
                        'customer.subscription.updated',
                        'customer.subscription.deleted',
                        'invoice.payment_succeeded',
                        'invoice.payment_failed',
                        'customer.subscription.trial_will_end',
                    ],
                    api_version=stripe.api_version,
                )

                self.stdout.write(self.style.SUCCESS(f'✅ Created in Stripe: {stripe_endpoint.id}'))
                self.stdout.write(f'   Secret: {stripe_endpoint.secret}')

                # Sync to local database
                self.stdout.write(self.style.SUCCESS('\n📥 Syncing to local database...'))
                webhook_endpoint = WebhookEndpoint.sync_from_stripe_data(stripe_endpoint)

                self.stdout.write(self.style.SUCCESS(f'✅ Synced to database: {webhook_endpoint.id}'))
                self.stdout.write(f'\n🔗 Use this URL in Stripe Dashboard:')
                self.stdout.write(self.style.SUCCESS(f'   {webhook_endpoint.url}'))
                self.stdout.write(f'\n🔑 Webhook Secret for Django settings:')
                self.stdout.write(self.style.WARNING(f'   DJSTRIPE_WEBHOOK_SECRET={webhook_endpoint.secret}'))

            except stripe.error.StripeError as e:
                self.stdout.write(self.style.ERROR(f'❌ Stripe API Error: {str(e)}'))
                return

        # Option 2: Sync existing endpoints from Stripe
        else:
            self.stdout.write(self.style.SUCCESS('\n📥 Syncing webhook endpoints from Stripe...'))

            try:
                # Fetch all webhook endpoints from Stripe
                stripe_endpoints = stripe.WebhookEndpoint.list(limit=100)

                if not stripe_endpoints.data:
                    self.stdout.write(self.style.WARNING('⚠️  No webhook endpoints found in Stripe.'))
                    self.stdout.write('\nTo create one, run:')
                    self.stdout.write(self.style.SUCCESS(
                        '  python manage.py register_stripe_webhook '
                        '--url https://your-domain.railway.app/stripe/webhook/ '
                        '--create-in-stripe'
                    ))
                    return

                self.stdout.write(f'Found {len(stripe_endpoints.data)} endpoint(s) in Stripe:\n')

                for stripe_ep in stripe_endpoints.data:
                    self.stdout.write(f'  - {stripe_ep.id}: {stripe_ep.url}')

                    # Sync to local database
                    webhook_endpoint = WebhookEndpoint.sync_from_stripe_data(stripe_ep)
                    self.stdout.write(self.style.SUCCESS(f'    ✅ Synced to database: {webhook_endpoint.id}\n'))

                # Display usage instructions
                self.stdout.write(self.style.SUCCESS('\n✅ Webhook endpoints synced successfully!\n'))

                # Get first endpoint for instructions
                first_endpoint = WebhookEndpoint.objects.first()
                if first_endpoint:
                    self.stdout.write('📋 Configuration:')
                    self.stdout.write(f'\n1️⃣  Add to Railway environment variables:')
                    self.stdout.write(self.style.WARNING(f'   DJSTRIPE_WEBHOOK_SECRET={first_endpoint.secret}'))

                    self.stdout.write(f'\n2️⃣  Your webhook URL for Stripe Dashboard:')
                    self.stdout.write(self.style.SUCCESS(f'   {first_endpoint.url}'))

                    self.stdout.write(f'\n3️⃣  Redeploy your Railway app to apply the secret')

            except stripe.error.StripeError as e:
                self.stdout.write(self.style.ERROR(f'❌ Stripe API Error: {str(e)}'))
                return

        self.stdout.write(self.style.SUCCESS('\n✅ Done!\n'))
