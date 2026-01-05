"""
Test webhook endpoint locally
"""

import json
import requests
from django.core.management.base import BaseCommand
from django.conf import settings


class Command(BaseCommand):
    help = 'Test webhook endpoint with sample payloads'

    def add_arguments(self, parser):
        parser.add_argument(
            '--url',
            type=str,
            default='http://localhost:8000/api/banking/webhooks/pluggy/',
            help='Webhook URL to test'
        )
        parser.add_argument(
            '--event',
            type=str,
            default='item/updated',
            help='Event type to simulate'
        )
        parser.add_argument(
            '--item-id',
            type=str,
            default='test-item-id',
            help='Item ID for the test'
        )

    def handle(self, *args, **options):
        url = options['url']
        event_type = options['event']
        item_id = options['item_id']

        self.stdout.write(f"Testing webhook: {url}")
        self.stdout.write(f"Event: {event_type}")

        # Sample payloads for different events
        payloads = {
            'item/updated': {
                'event': 'item/updated',
                'itemId': item_id,
                'data': {
                    'status': 'UPDATED',
                    'executionStatus': 'SUCCESS'
                }
            },
            'item/login_succeeded': {
                'event': 'item/login_succeeded',
                'itemId': item_id,
                'data': {
                    'status': 'UPDATING'
                }
            },
            'transactions/created': {
                'event': 'transactions/created',
                'itemId': item_id,
                'data': {
                    'count': 10
                }
            },
            'transactions/updated': {
                'event': 'transactions/updated',
                'itemId': item_id,
                'data': {
                    'count': 5
                }
            },
            'item/waiting_user_input': {
                'event': 'item/waiting_user_input',
                'itemId': item_id,
                'parameter': {
                    'name': 'token',
                    'label': 'Enter your 6-digit token',
                    'type': 'string',
                    'expiresAt': '2025-01-01T00:00:00Z'
                }
            }
        }

        payload = payloads.get(event_type, payloads['item/updated'])

        self.stdout.write(f"\nPayload:")
        self.stdout.write(json.dumps(payload, indent=2))

        try:
            # Send webhook request
            headers = {
                'Content-Type': 'application/json',
            }

            # Add webhook secret if configured
            webhook_secret = getattr(settings, 'PLUGGY_WEBHOOK_SECRET', None)
            if webhook_secret:
                import hmac
                import hashlib
                signature = hmac.new(
                    webhook_secret.encode('utf-8'),
                    json.dumps(payload).encode('utf-8'),
                    hashlib.sha256
                ).hexdigest()
                headers['X-Webhook-Signature'] = signature

            response = requests.post(url, json=payload, headers=headers)

            self.stdout.write(f"\nResponse Status: {response.status_code}")
            self.stdout.write(f"Response Body: {response.text}")

            if response.status_code == 200:
                self.stdout.write(self.style.SUCCESS("✅ Webhook processed successfully"))
            else:
                self.stdout.write(self.style.ERROR(f"❌ Webhook failed with status {response.status_code}"))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Error: {e}"))

        # Test with curl command
        self.stdout.write("\n" + "="*50)
        self.stdout.write("You can also test with curl:")
        curl_cmd = f"""
curl -X POST {url} \\
  -H "Content-Type: application/json" \\
  -d '{json.dumps(payload)}'
"""
        self.stdout.write(curl_cmd)