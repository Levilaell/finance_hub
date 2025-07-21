"""
Django management command to test Pluggy webhook locally
"""
import json
import hmac
import hashlib
import requests
from django.core.management.base import BaseCommand
from django.conf import settings
from django.urls import reverse


class Command(BaseCommand):
    help = 'Test Pluggy webhook locally by sending sample events'

    def add_arguments(self, parser):
        parser.add_argument(
            'event_type',
            type=str,
            choices=[
                'item/created',
                'item/updated',
                'item/error',
                'transactions/created',
                'account/created',
                'account/updated'
            ],
            help='Type of webhook event to simulate'
        )
        parser.add_argument(
            '--item-id',
            type=str,
            default='test-item-123',
            help='Item ID to use in the test'
        )
        parser.add_argument(
            '--account-id',
            type=str,
            default='test-account-456',
            help='Account ID to use in the test'
        )
        parser.add_argument(
            '--status',
            type=str,
            default='ACTIVE',
            help='Status for item/updated events'
        )

    def handle(self, *args, **options):
        """Send test webhook to local server"""
        event_type = options['event_type']
        
        # Build webhook URL
        webhook_path = reverse('pluggy_webhook')
        base_url = getattr(settings, 'BACKEND_URL', 'http://localhost:8000')
        webhook_url = f"{base_url}{webhook_path}"
        
        # Create sample payload based on event type
        payload = self._create_payload(event_type, options)
        
        # Convert to JSON
        json_payload = json.dumps(payload)
        
        # Calculate signature if webhook secret is configured
        headers = {'Content-Type': 'application/json'}
        webhook_secret = getattr(settings, 'PLUGGY_WEBHOOK_SECRET', '')
        
        if webhook_secret:
            signature = hmac.new(
                webhook_secret.encode('utf-8'),
                json_payload.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            headers['X-Pluggy-Signature'] = signature
            self.stdout.write(f"Using webhook signature: {signature[:16]}...")
        else:
            self.stdout.write(self.style.WARNING('No PLUGGY_WEBHOOK_SECRET configured'))
        
        # Send request
        self.stdout.write(f"Sending {event_type} webhook to {webhook_url}")
        self.stdout.write(f"Payload: {json.dumps(payload, indent=2)}")
        
        try:
            response = requests.post(
                webhook_url,
                data=json_payload,
                headers=headers,
                timeout=10
            )
            
            self.stdout.write(f"Response status: {response.status_code}")
            self.stdout.write(f"Response body: {response.text}")
            
            if response.status_code == 200:
                self.stdout.write(
                    self.style.SUCCESS('Webhook test completed successfully!')
                )
            else:
                self.stdout.write(
                    self.style.ERROR(f'Webhook returned error: {response.status_code}')
                )
                
        except requests.exceptions.RequestException as e:
            self.stdout.write(
                self.style.ERROR(f'Failed to send webhook: {str(e)}')
            )

    def _create_payload(self, event_type, options):
        """Create sample payload for different event types"""
        base_payload = {
            'event': event_type,
            'data': {}
        }
        
        if event_type == 'item/created':
            base_payload['data'] = {
                'id': options['item_id'],
                'status': 'LOGIN_IN_PROGRESS',
                'createdAt': '2024-01-01T10:00:00.000Z'
            }
            
        elif event_type == 'item/updated':
            base_payload['data'] = {
                'id': options['item_id'],
                'status': options['status'],
                'updatedAt': '2024-01-01T10:05:00.000Z'
            }
            
        elif event_type == 'item/error':
            base_payload['data'] = {
                'id': options['item_id'],
                'error': {
                    'code': 'INVALID_CREDENTIALS',
                    'message': 'Invalid username or password'
                }
            }
            
        elif event_type == 'transactions/created':
            base_payload['data'] = {
                'accountId': options['account_id'],
                'count': 25,
                'createdAt': '2024-01-01T10:10:00.000Z'
            }
            
        elif event_type == 'account/created':
            base_payload['data'] = {
                'id': options['account_id'],
                'itemId': options['item_id'],
                'type': 'CHECKING',
                'number': '12345-6',
                'balance': 1500.00
            }
            
        elif event_type == 'account/updated':
            base_payload['data'] = {
                'id': options['account_id'],
                'balance': 2000.00,
                'updatedAt': '2024-01-01T10:15:00.000Z'
            }
            
        return base_payload