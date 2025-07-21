"""
Simulate a transaction webhook from Pluggy
"""
import json
import requests
from django.core.management.base import BaseCommand
from apps.banking.models import BankAccount


class Command(BaseCommand):
    help = 'Simulate a transaction webhook for testing'

    def add_arguments(self, parser):
        parser.add_argument(
            '--account-id',
            type=int,
            required=True,
            help='Local account ID to simulate webhook for'
        )
        parser.add_argument(
            '--production',
            action='store_true',
            help='Send to production URL instead of localhost'
        )

    def handle(self, *args, **options):
        account_id = options['account_id']
        
        try:
            # Get account
            account = BankAccount.objects.get(id=account_id)
            
            if not account.external_id:
                self.stdout.write(self.style.ERROR(f"Account {account_id} has no external_id"))
                return
            
            # Prepare webhook payload
            payload = {
                "event": "transactions/created",
                "data": {
                    "accountId": account.external_id,
                    "count": 1,
                    "createdAt": "2025-07-21T20:00:00.000Z"
                }
            }
            
            # Determine URL
            if options['production']:
                url = "https://finance-backend-production-29df.up.railway.app/api/banking/pluggy/webhook/"
            else:
                url = "http://localhost:8000/api/banking/pluggy/webhook/"
            
            self.stdout.write(f"Sending webhook to: {url}")
            self.stdout.write(f"Account: {account.bank_provider.name} - {account.id}")
            self.stdout.write(f"External ID: {account.external_id}")
            self.stdout.write(f"Payload: {json.dumps(payload, indent=2)}")
            
            # Send webhook
            response = requests.post(
                url,
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=30
            )
            
            self.stdout.write(f"\nResponse Status: {response.status_code}")
            self.stdout.write(f"Response Body: {response.text}")
            
            if response.status_code == 200:
                self.stdout.write(self.style.SUCCESS("\n✅ Webhook sent successfully!"))
                self.stdout.write("Check if transactions were synced")
                
                # Check if account was synced
                account.refresh_from_db()
                recent_trans = account.transactions.order_by('-created_at').first()
                if recent_trans:
                    self.stdout.write(f"\nMost recent transaction: {recent_trans.created_at}")
            else:
                self.stdout.write(self.style.ERROR(f"\n❌ Webhook failed: {response.status_code}"))
                
        except BankAccount.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"Account {account_id} not found"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error: {e}"))