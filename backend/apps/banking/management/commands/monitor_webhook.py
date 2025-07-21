"""
Monitor webhook activity and debug issues
"""
import json
import requests
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.banking.models import BankAccount, Transaction
from apps.banking.pluggy_client import PluggyClient
import asyncio


class Command(BaseCommand):
    help = 'Monitor webhook activity and check for issues'

    def add_arguments(self, parser):
        parser.add_argument(
            '--account-id',
            type=int,
            help='Account ID to monitor'
        )
        parser.add_argument(
            '--check-pluggy',
            action='store_true',
            help='Check item status directly from Pluggy'
        )

    def handle(self, *args, **options):
        account_id = options.get('account_id')
        
        self.stdout.write("=== Webhook Monitor ===\n")
        
        # Check webhook endpoint
        self.stdout.write("1. Checking webhook endpoint...")
        webhook_url = "https://finance-backend-production-29df.up.railway.app/api/banking/pluggy/webhook/"
        try:
            response = requests.get(webhook_url, timeout=5)
            if response.status_code == 405:
                self.stdout.write(self.style.SUCCESS("✅ Webhook endpoint is accessible"))
            else:
                self.stdout.write(self.style.WARNING(f"⚠️ Unexpected status: {response.status_code}"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Webhook unreachable: {e}"))
        
        # Check recent transactions
        self.stdout.write("\n2. Recent transaction activity:")
        
        if account_id:
            accounts = BankAccount.objects.filter(id=account_id)
        else:
            accounts = BankAccount.objects.filter(
                external_id__isnull=False,
                is_active=True
            )
        
        for account in accounts:
            self.stdout.write(f"\nAccount: {account.bank_provider.name} (ID: {account.id})")
            self.stdout.write(f"  External ID: {account.external_id}")
            self.stdout.write(f"  Item ID: {account.pluggy_item_id}")
            self.stdout.write(f"  Last sync: {account.last_sync_at}")
            
            # Check recent transactions
            recent = account.transactions.order_by('-created_at')[:5]
            now = timezone.now()
            
            if recent:
                latest = recent[0]
                time_diff = now - latest.created_at
                
                self.stdout.write(f"  Latest transaction:")
                self.stdout.write(f"    Created: {latest.created_at} ({time_diff.total_seconds():.0f}s ago)")
                self.stdout.write(f"    Date: {latest.transaction_date}")
                self.stdout.write(f"    Description: {latest.description[:50]}")
                
                # Check if transactions were added recently
                recent_adds = account.transactions.filter(
                    created_at__gte=now - timedelta(minutes=10)
                ).count()
                
                if recent_adds > 0:
                    self.stdout.write(self.style.SUCCESS(f"  ✅ {recent_adds} transactions added in last 10 minutes"))
                else:
                    self.stdout.write(self.style.WARNING("  ⚠️ No transactions added in last 10 minutes"))
            else:
                self.stdout.write(self.style.WARNING("  ⚠️ No transactions found"))
            
            # Check Pluggy item status
            if options.get('check_pluggy') and account.pluggy_item_id:
                self.stdout.write("\n  Checking Pluggy item status...")
                
                async def check_item():
                    try:
                        async with PluggyClient() as client:
                            item = await client.get_item(account.pluggy_item_id)
                            return item
                    except Exception as e:
                        return {'error': str(e)}
                
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    item_data = loop.run_until_complete(check_item())
                    
                    if 'error' in item_data:
                        self.stdout.write(self.style.ERROR(f"  ❌ Pluggy API error: {item_data['error']}"))
                    else:
                        status = item_data.get('status', 'UNKNOWN')
                        updated = item_data.get('updatedAt', 'N/A')
                        
                        self.stdout.write(f"  Pluggy item status: {status}")
                        self.stdout.write(f"  Last updated: {updated}")
                        
                        if status != 'ACTIVE':
                            self.stdout.write(self.style.WARNING(f"  ⚠️ Item is not ACTIVE"))
                            if 'error' in item_data:
                                self.stdout.write(f"  Error: {item_data['error'].get('message', 'Unknown')}")
                finally:
                    loop.close()
        
        # Suggestions
        self.stdout.write("\n=== Troubleshooting ===")
        self.stdout.write("1. Make sure the item is ACTIVE in Pluggy")
        self.stdout.write("2. Check if webhook is properly registered in Pluggy dashboard")
        self.stdout.write("3. Verify that transactions are being created in Pluggy")
        self.stdout.write("4. Try manual sync: POST /api/banking/pluggy/accounts/{id}/sync/")
        self.stdout.write("5. Check Railway logs for webhook activity:")
        self.stdout.write("   railway logs --service=backend | grep webhook")