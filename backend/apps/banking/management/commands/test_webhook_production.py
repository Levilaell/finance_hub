"""
Django management command to test webhook in production environment
"""
import json
import hmac
import hashlib
import requests
from django.core.management.base import BaseCommand
from django.conf import settings
from apps.banking.models import BankAccount


class Command(BaseCommand):
    help = 'Test Pluggy webhook with production-like events'

    def add_arguments(self, parser):
        parser.add_argument(
            '--account-id',
            type=str,
            required=True,
            help='BankAccount ID to test with'
        )
        parser.add_argument(
            '--webhook-url',
            type=str,
            help='Override webhook URL (default: use configured URL)'
        )
        parser.add_argument(
            '--event',
            type=str,
            default='transactions/created',
            choices=['transactions/created', 'item/updated', 'account/updated'],
            help='Event type to simulate'
        )

    def handle(self, *args, **options):
        """Test webhook with real account data"""
        account_id = options['account_id']
        
        try:
            # Get the account
            account = BankAccount.objects.get(id=account_id)
            
            if not account.external_id or not account.pluggy_item_id:
                self.stdout.write(
                    self.style.ERROR(
                        f"Account {account_id} is not properly connected to Pluggy\n"
                        f"External ID: {account.external_id or 'MISSING'}\n"
                        f"Item ID: {account.pluggy_item_id or 'MISSING'}"
                    )
                )
                return
            
            self.stdout.write(f"\nTesting webhook for account:")
            self.stdout.write(f"  - Account: {account.display_name}")
            self.stdout.write(f"  - External ID: {account.external_id}")
            self.stdout.write(f"  - Item ID: {account.pluggy_item_id}")
            self.stdout.write(f"  - Company: {account.company.name}")
            
            # Build webhook URL
            webhook_url = options.get('webhook_url')
            if not webhook_url:
                from django.urls import reverse
                webhook_path = reverse('pluggy_webhook')
                base_url = getattr(settings, 'BACKEND_URL', 'http://localhost:8000')
                webhook_url = f"{base_url}{webhook_path}"
            
            # Create payload based on event type
            event_type = options['event']
            payload = self._create_production_payload(event_type, account)
            
            # Send webhook
            self._send_webhook(webhook_url, payload)
            
        except BankAccount.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"Account {account_id} not found"))

    def _create_production_payload(self, event_type, account):
        """Create realistic payload with actual account data"""
        from django.utils import timezone
        
        if event_type == 'transactions/created':
            return {
                'event': 'transactions/created',
                'data': {
                    'accountId': account.external_id,
                    'count': 10,
                    'createdAt': timezone.now().isoformat()
                }
            }
        
        elif event_type == 'item/updated':
            return {
                'event': 'item/updated',
                'data': {
                    'id': account.pluggy_item_id,
                    'status': 'ACTIVE',
                    'updatedAt': timezone.now().isoformat()
                }
            }
        
        elif event_type == 'account/updated':
            return {
                'event': 'account/updated',
                'data': {
                    'id': account.external_id,
                    'itemId': account.pluggy_item_id,
                    'balance': float(account.current_balance),
                    'updatedAt': timezone.now().isoformat()
                }
            }

    def _send_webhook(self, webhook_url, payload):
        """Send webhook request with proper signature"""
        # Convert to JSON
        json_payload = json.dumps(payload)
        
        # Prepare headers
        headers = {'Content-Type': 'application/json'}
        
        # Add signature if webhook secret is configured
        webhook_secret = getattr(settings, 'PLUGGY_WEBHOOK_SECRET', '')
        if webhook_secret:
            signature = hmac.new(
                webhook_secret.encode('utf-8'),
                json_payload.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            headers['X-Pluggy-Signature'] = signature
            self.stdout.write(f"\n✅ Using webhook signature")
        else:
            self.stdout.write(self.style.WARNING('\n⚠️  No PLUGGY_WEBHOOK_SECRET configured'))
        
        # Send request
        self.stdout.write(f"\n📤 Sending {payload['event']} webhook to {webhook_url}")
        self.stdout.write(f"Payload: {json.dumps(payload, indent=2)}")
        
        try:
            response = requests.post(
                webhook_url,
                data=json_payload,
                headers=headers,
                timeout=30
            )
            
            self.stdout.write(f"\n📥 Response:")
            self.stdout.write(f"  - Status: {response.status_code}")
            self.stdout.write(f"  - Body: {response.text}")
            
            if response.status_code == 200:
                self.stdout.write(self.style.SUCCESS('\n✅ Webhook processed successfully!'))
                
                # Check if sync actually happened
                account_refreshed = BankAccount.objects.get(id=payload['data'].get('accountId', ''))
                if account_refreshed.last_sync_at:
                    self.stdout.write(f"\n🔄 Account last sync: {account_refreshed.last_sync_at}")
            else:
                self.stdout.write(self.style.ERROR(f'\n❌ Webhook returned error: {response.status_code}'))
                
        except requests.exceptions.RequestException as e:
            self.stdout.write(self.style.ERROR(f'\n❌ Failed to send webhook: {str(e)}'))