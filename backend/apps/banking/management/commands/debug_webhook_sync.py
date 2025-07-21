"""
Django management command to debug webhook and sync issues
"""
import json
import asyncio
from django.core.management.base import BaseCommand
from django.conf import settings
from django.utils import timezone
from apps.banking.models import BankAccount, Transaction
from apps.banking.pluggy_client import PluggyClient
from apps.banking.pluggy_sync_service import pluggy_sync_service


class Command(BaseCommand):
    help = 'Debug webhook and sync issues for Pluggy accounts'

    def add_arguments(self, parser):
        parser.add_argument(
            '--account-id',
            type=str,
            help='Specific account ID to debug'
        )
        parser.add_argument(
            '--check-webhook',
            action='store_true',
            help='Check webhook configuration on Pluggy'
        )
        parser.add_argument(
            '--sync-now',
            action='store_true',
            help='Force sync the account now'
        )
        parser.add_argument(
            '--check-item',
            action='store_true',
            help='Check item status on Pluggy'
        )

    def handle(self, *args, **options):
        """Debug webhook and sync issues"""
        account_id = options.get('account_id')
        
        if account_id:
            self._debug_specific_account(account_id, options)
        else:
            self._debug_all_accounts(options)

    def _debug_specific_account(self, account_id, options):
        """Debug a specific account"""
        try:
            account = BankAccount.objects.get(id=account_id)
            self.stdout.write(f"\n{'='*60}")
            self.stdout.write(f"DEBUGGING ACCOUNT: {account.display_name}")
            self.stdout.write(f"{'='*60}")
            
            # Show account details
            self.stdout.write(f"\nAccount Details:")
            self.stdout.write(f"  - ID: {account.id}")
            self.stdout.write(f"  - External ID: {account.external_id or 'NOT SET'}")
            self.stdout.write(f"  - Pluggy Item ID: {account.pluggy_item_id or 'NOT SET'}")
            self.stdout.write(f"  - Status: {account.status}")
            self.stdout.write(f"  - Is Active: {account.is_active}")
            self.stdout.write(f"  - Last Sync: {account.last_sync_at or 'NEVER'}")
            self.stdout.write(f"  - Balance: R$ {account.current_balance}")
            
            # Check if properly connected to Pluggy
            if not account.external_id:
                self.stdout.write(self.style.ERROR("\n❌ Account has no external_id - not connected to Pluggy"))
                return
            
            if not account.pluggy_item_id:
                self.stdout.write(self.style.ERROR("\n❌ Account has no pluggy_item_id - missing connection"))
                return
            
            # Check recent transactions
            recent_transactions = Transaction.objects.filter(
                bank_account=account
            ).order_by('-transaction_date')[:5]
            
            self.stdout.write(f"\nRecent Transactions ({recent_transactions.count()} found):")
            for tx in recent_transactions:
                self.stdout.write(f"  - {tx.transaction_date}: {tx.description} - R$ {tx.amount}")
            
            # Check webhook configuration
            if options.get('check_webhook'):
                self._check_webhook_config()
            
            # Check item status on Pluggy
            if options.get('check_item'):
                self._check_item_status(account.pluggy_item_id)
            
            # Force sync if requested
            if options.get('sync_now'):
                self._force_sync_account(account)
                
        except BankAccount.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"Account {account_id} not found"))

    def _debug_all_accounts(self, options):
        """Debug all Pluggy accounts"""
        accounts = BankAccount.objects.filter(
            pluggy_item_id__isnull=False
        ).select_related('company', 'bank_provider')
        
        self.stdout.write(f"\n{'='*60}")
        self.stdout.write(f"FOUND {accounts.count()} PLUGGY ACCOUNTS")
        self.stdout.write(f"{'='*60}")
        
        for account in accounts:
            self.stdout.write(f"\n{account.display_name} ({account.company.name}):")
            self.stdout.write(f"  - External ID: {account.external_id or 'NOT SET'}")
            self.stdout.write(f"  - Item ID: {account.pluggy_item_id}")
            self.stdout.write(f"  - Status: {account.status}")
            self.stdout.write(f"  - Last Sync: {account.last_sync_at or 'NEVER'}")
            
            if account.last_sync_at:
                time_since_sync = timezone.now() - account.last_sync_at
                hours_since = time_since_sync.total_seconds() / 3600
                if hours_since > 24:
                    self.stdout.write(self.style.WARNING(f"  - ⚠️  Not synced for {hours_since:.1f} hours"))

    def _check_webhook_config(self):
        """Check webhook configuration on Pluggy"""
        self.stdout.write("\n\nChecking webhook configuration...")
        
        async def check_webhooks():
            async with PluggyClient() as client:
                # Get configured webhooks
                response = await client._request('GET', '/webhooks')
                return response
        
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            webhooks = loop.run_until_complete(check_webhooks())
            
            self.stdout.write(f"\nConfigured webhooks: {len(webhooks.get('results', []))}")
            
            for webhook in webhooks.get('results', []):
                self.stdout.write(f"\nWebhook ID: {webhook.get('id')}")
                self.stdout.write(f"  - URL: {webhook.get('url')}")
                self.stdout.write(f"  - Events: {', '.join(webhook.get('events', []))}")
                self.stdout.write(f"  - Active: {webhook.get('active', False)}")
                self.stdout.write(f"  - Created: {webhook.get('createdAt')}")
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error checking webhooks: {e}"))
        finally:
            loop.close()

    def _check_item_status(self, item_id):
        """Check item status on Pluggy"""
        self.stdout.write(f"\n\nChecking item {item_id} on Pluggy...")
        
        async def check_item():
            async with PluggyClient() as client:
                item = await client.get_item(item_id)
                accounts = await client.get_accounts(item_id)
                return item, accounts
        
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            item, accounts = loop.run_until_complete(check_item())
            
            self.stdout.write(f"\nItem Status:")
            self.stdout.write(f"  - ID: {item.get('id')}")
            self.stdout.write(f"  - Status: {item.get('status')}")
            self.stdout.write(f"  - Updated: {item.get('updatedAt')}")
            self.stdout.write(f"  - Connector: {item.get('connector', {}).get('name')}")
            
            if item.get('status') != 'ACTIVE':
                self.stdout.write(self.style.WARNING(f"  - ⚠️  Item is not ACTIVE"))
            
            self.stdout.write(f"\nAccounts in this item: {len(accounts)}")
            for acc in accounts:
                self.stdout.write(f"  - {acc.get('id')}: {acc.get('name')} - Balance: R$ {acc.get('balance')}")
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error checking item: {e}"))
        finally:
            loop.close()

    def _force_sync_account(self, account):
        """Force sync an account"""
        self.stdout.write(f"\n\nForcing sync for account {account.id}...")
        
        async def sync_account():
            return await pluggy_sync_service.sync_account_transactions(account)
        
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(sync_account())
            
            if result.get('status') == 'success':
                self.stdout.write(self.style.SUCCESS(f"✅ Sync successful!"))
                self.stdout.write(f"  - Transactions synced: {result.get('transactions', 0)}")
                self.stdout.write(f"  - New balance: R$ {result.get('new_balance', 0)}")
            else:
                self.stdout.write(self.style.ERROR(f"❌ Sync failed: {result.get('error')}"))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error during sync: {e}"))
        finally:
            loop.close()