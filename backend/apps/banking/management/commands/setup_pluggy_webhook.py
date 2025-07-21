"""
Django management command to setup Pluggy webhook
"""
import logging
import asyncio
from django.core.management.base import BaseCommand
from django.conf import settings
from django.urls import reverse
from apps.banking.pluggy_client import PluggyClient

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Setup Pluggy webhook for real-time updates'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force update webhook even if already configured',
        )

    def handle(self, *args, **options):
        """Setup webhook configuration in Pluggy"""
        try:
            # Run async function
            asyncio.run(self._setup_webhook(options['force']))
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Failed to setup webhook: {str(e)}')
            )
            raise

    async def _setup_webhook(self, force=False):
        """Async method to setup webhook"""
        client = PluggyClient()
        
        # Build webhook URL
        webhook_path = reverse('pluggy_webhook')
        base_url = getattr(settings, 'BACKEND_URL', settings.FRONTEND_URL.replace(':3000', ':8000'))
        webhook_url = f"{base_url}{webhook_path}"
        
        self.stdout.write(f"Setting up webhook at: {webhook_url}")
        
        try:
            # Check if webhook already exists
            existing_webhook = await client.get_webhook_url()
            
            if existing_webhook and not force:
                self.stdout.write(
                    self.style.WARNING(f'Webhook already configured: {existing_webhook}')
                )
                self.stdout.write('Use --force to update the webhook')
                return
            
            # Events we want to subscribe to
            events = [
                'item/created',
                'item/updated', 
                'item/error',
                'transactions/created',
                'transactions/updated',
                'account/created',
                'account/updated'
            ]
            
            # Create or update webhook
            result = await client.create_webhook(webhook_url, events)
            
            if result:
                self.stdout.write(
                    self.style.SUCCESS(f'Webhook configured successfully!')
                )
                self.stdout.write(f"URL: {webhook_url}")
                self.stdout.write(f"Events: {', '.join(events)}")
                
                # Important reminder about webhook secret
                if not getattr(settings, 'PLUGGY_WEBHOOK_SECRET', ''):
                    self.stdout.write(
                        self.style.WARNING(
                            '\nIMPORTANT: Remember to set PLUGGY_WEBHOOK_SECRET '
                            'in your environment variables with the secret provided by Pluggy!'
                        )
                    )
            else:
                self.stdout.write(
                    self.style.ERROR('Failed to configure webhook')
                )
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error setting up webhook: {str(e)}')
            )
            raise