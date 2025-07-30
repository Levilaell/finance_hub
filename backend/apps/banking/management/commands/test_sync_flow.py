"""
Test command to verify the complete sync flow after connection
"""
import logging
from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.banking.models import PluggyItem, BankAccount
from apps.banking.tasks import sync_bank_account

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Test the sync flow for bank connections'

    def add_arguments(self, parser):
        parser.add_argument(
            '--item-id',
            type=str,
            help='Specific item ID to test'
        )
        parser.add_argument(
            '--account-id',
            type=str,
            help='Specific account ID to test'
        )

    def handle(self, *args, **options):
        item_id = options.get('item_id')
        account_id = options.get('account_id')

        if item_id:
            self.test_specific_item(item_id, account_id)
        else:
            self.test_all_items()

    def test_specific_item(self, item_id, account_id=None):
        """Test sync for a specific item"""
        try:
            item = PluggyItem.objects.get(id=item_id)
            self.stdout.write(f"\nTesting sync for item: {item.pluggy_item_id}")
            self.stdout.write(f"Connector: {item.connector.name}")
            self.stdout.write(f"Status: {item.status}")
            self.stdout.write(f"Last successful update: {item.last_successful_update}")
            
            # List accounts
            accounts = item.accounts.filter(is_active=True)
            self.stdout.write(f"\nAccounts ({accounts.count()}):")
            for account in accounts:
                self.stdout.write(f"  - {account.display_name} ({account.type}): {account.balance}")
            
            # Trigger sync
            self.stdout.write("\nTriggering sync...")
            result = sync_bank_account(str(item.id), account_id=account_id)
            
            if result['success']:
                self.stdout.write(self.style.SUCCESS(f"✓ Sync successful!"))
                self.stdout.write(f"  Accounts synced: {result['accounts_synced']}")
                self.stdout.write(f"  Transactions synced: {result.get('transactions_synced', 0)}")
                
                # Show results per account
                for acc_result in result['results']:
                    if acc_result['success']:
                        self.stdout.write(self.style.SUCCESS(
                            f"  ✓ Account {acc_result['account_id']}: "
                            f"{acc_result['transactions_synced']} transactions, "
                            f"balance: {acc_result['balance']}"
                        ))
                    else:
                        self.stdout.write(self.style.ERROR(
                            f"  ✗ Account {acc_result['account_id']}: {acc_result['error']}"
                        ))
            else:
                self.stdout.write(self.style.ERROR(f"✗ Sync failed: {result.get('reason', 'Unknown error')}"))
                if result.get('requires_reconnection'):
                    self.stdout.write(self.style.WARNING("  → Reconnection required"))
                    
        except PluggyItem.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"Item {item_id} not found"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error: {str(e)}"))

    def test_all_items(self):
        """Test sync for all active items"""
        items = PluggyItem.objects.exclude(status='DELETED')
        
        self.stdout.write(f"\nFound {items.count()} items to test\n")
        
        for item in items:
            self.stdout.write(f"\n{'='*50}")
            self.test_specific_item(str(item.id))
            
        self.stdout.write(f"\n{'='*50}")
        self.stdout.write(self.style.SUCCESS("\nAll tests completed!"))