"""
Check webhook configuration and test with real account data
"""
from django.core.management.base import BaseCommand
from django.conf import settings
from apps.banking.models import BankAccount
import requests
import json


class Command(BaseCommand):
    help = 'Check webhook configuration and account setup'

    def add_arguments(self, parser):
        parser.add_argument(
            '--email',
            type=str,
            help='User email to check accounts'
        )
        parser.add_argument(
            '--test-sync',
            action='store_true',
            help='Test sync for all active accounts'
        )

    def handle(self, *args, **options):
        self.stdout.write("=== Webhook Configuration Check ===\n")
        
        # Check webhook settings
        webhook_secret = getattr(settings, 'PLUGGY_WEBHOOK_SECRET', '')
        webhook_url = "https://finance-backend-production-29df.up.railway.app/api/banking/pluggy/webhook/"
        
        self.stdout.write(f"Webhook URL: {webhook_url}")
        self.stdout.write(f"Webhook Secret Configured: {'Yes' if webhook_secret else 'No'}")
        
        # Check accounts
        accounts_query = BankAccount.objects.filter(
            external_id__isnull=False,
            pluggy_item_id__isnull=False
        )
        
        if options.get('email'):
            from apps.authentication.models import User
            try:
                user = User.objects.get(email=options['email'])
                accounts_query = accounts_query.filter(company=user.company)
            except User.DoesNotExist:
                self.stdout.write(self.style.ERROR(f"User not found: {options['email']}"))
                return
        
        accounts = accounts_query.all()
        
        self.stdout.write(f"\n=== Pluggy Connected Accounts ({len(accounts)}) ===")
        
        for account in accounts:
            self.stdout.write(f"\nAccount ID: {account.id}")
            self.stdout.write(f"  Bank: {account.bank_provider.name}")
            self.stdout.write(f"  External ID: {account.external_id}")
            self.stdout.write(f"  Item ID: {account.pluggy_item_id}")
            self.stdout.write(f"  Status: {account.status}")
            self.stdout.write(f"  Active: {account.is_active}")
            self.stdout.write(f"  Last Sync: {account.last_sync_at}")
            self.stdout.write(f"  Balance: R$ {account.current_balance}")
            
            # Check recent transactions
            recent_transactions = account.transactions.order_by('-transaction_date')[:3]
            if recent_transactions:
                self.stdout.write("  Recent transactions:")
                for trans in recent_transactions:
                    self.stdout.write(f"    - {trans.transaction_date}: {trans.description} (R$ {trans.amount})")
            else:
                self.stdout.write("  No transactions found")
            
            if options.get('test_sync'):
                self.stdout.write(f"\n  Testing manual sync for account {account.id}...")
                try:
                    # Call sync endpoint
                    sync_url = f"https://finance-backend-production-29df.up.railway.app/api/banking/pluggy/accounts/{account.id}/sync/"
                    
                    # You would need auth token here
                    self.stdout.write(f"  Would sync via: POST {sync_url}")
                    self.stdout.write("  (Needs auth token to actually sync)")
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"  Sync error: {e}"))
        
        # Test webhook endpoint
        self.stdout.write("\n=== Testing Webhook Endpoint ===")
        try:
            response = requests.get(webhook_url, timeout=5)
            if response.status_code == 405:
                self.stdout.write(self.style.SUCCESS("✅ Webhook endpoint is accessible"))
            else:
                self.stdout.write(self.style.WARNING(f"⚠️  Unexpected status: {response.status_code}"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Webhook test failed: {e}"))
        
        # Check Pluggy API status
        self.stdout.write("\n=== Checking Pluggy API ===")
        from apps.banking.pluggy_client import PluggyClient
        import asyncio
        
        async def check_pluggy():
            try:
                async with PluggyClient() as client:
                    # Test authentication
                    await client._ensure_authenticated()
                    self.stdout.write(self.style.SUCCESS("✅ Pluggy API authentication successful"))
                    return True
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"❌ Pluggy API error: {e}"))
                return False
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        pluggy_ok = loop.run_until_complete(check_pluggy())
        loop.close()
        
        # Summary
        self.stdout.write("\n=== Summary ===")
        issues = []
        
        if not webhook_secret:
            issues.append("- Webhook secret not configured (Pluggy doesn't require it)")
        
        if not accounts:
            issues.append("- No Pluggy connected accounts found")
        
        if not pluggy_ok:
            issues.append("- Pluggy API connection failed")
        
        if issues:
            self.stdout.write(self.style.WARNING("Issues found:"))
            for issue in issues:
                self.stdout.write(issue)
        else:
            self.stdout.write(self.style.SUCCESS("✅ Everything looks configured correctly!"))
            
        self.stdout.write("\n💡 Troubleshooting tips:")
        self.stdout.write("1. Check Railway logs: railway logs --service=backend")
        self.stdout.write("2. Verify webhook is registered in Pluggy dashboard")
        self.stdout.write("3. Make sure the account's item is in ACTIVE status")
        self.stdout.write("4. Try manual sync through the API endpoint")