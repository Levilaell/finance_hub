"""
Test sync directly without Celery to debug issues
"""
import logging
from django.core.management.base import BaseCommand
from apps.banking.models import PluggyItem, BankAccount
from apps.banking.tasks import sync_bank_account

# Configure logging to see all debug info
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Test sync directly without Celery'

    def add_arguments(self, parser):
        parser.add_argument(
            '--account-id',
            type=str,
            help='Account ID to sync'
        )
        parser.add_argument(
            '--item-id',
            type=str,
            help='Item ID to sync'
        )

    def handle(self, *args, **options):
        account_id = options.get('account_id')
        item_id = options.get('item_id')

        if account_id:
            self.sync_by_account(account_id)
        elif item_id:
            self.sync_by_item(item_id)
        else:
            self.list_accounts()

    def list_accounts(self):
        """List all accounts with their sync status"""
        accounts = BankAccount.objects.filter(is_active=True).select_related('item')
        
        if not accounts:
            self.stdout.write(self.style.WARNING("No active accounts found"))
            return
            
        self.stdout.write("\nActive accounts:")
        for account in accounts:
            self.stdout.write(
                f"\n{account.id} - {account.display_name}"
                f"\n  Item: {account.item.id} ({account.item.status})"
                f"\n  Last update: {account.pluggy_updated_at}"
                f"\n  Balance: {account.balance}"
            )
            
        self.stdout.write("\n\nTo sync an account, run:")
        self.stdout.write("python manage.py test_sync_direct --account-id <uuid>")

    def sync_by_account(self, account_id):
        """Sync a specific account"""
        try:
            account = BankAccount.objects.get(id=account_id)
            self.stdout.write(f"\nSyncing account: {account.display_name}")
            self.stdout.write(f"Item ID: {account.item.id}")
            self.stdout.write(f"Item status: {account.item.status}")
            
            # Call the sync task directly (not through Celery)
            self.stdout.write("\nCalling sync_bank_account directly...")
            result = sync_bank_account(str(account.item.id), account_id=str(account.id))
            
            self.stdout.write(f"\nResult: {result}")
            
            if result['success']:
                self.stdout.write(self.style.SUCCESS("✓ Sync completed successfully!"))
                if 'message' in result:
                    self.stdout.write(result['message'])
            else:
                self.stdout.write(self.style.ERROR(f"✗ Sync failed: {result.get('reason', 'Unknown')}"))
                
        except BankAccount.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"Account {account_id} not found"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error: {str(e)}"))
            import traceback
            traceback.print_exc()

    def sync_by_item(self, item_id):
        """Sync all accounts for an item"""
        try:
            item = PluggyItem.objects.get(id=item_id)
            self.stdout.write(f"\nSyncing item: {item.pluggy_item_id}")
            self.stdout.write(f"Status: {item.status}")
            
            # Call the sync task directly
            self.stdout.write("\nCalling sync_bank_account directly...")
            result = sync_bank_account(str(item.id))
            
            self.stdout.write(f"\nResult: {result}")
            
            if result['success']:
                self.stdout.write(self.style.SUCCESS("✓ Sync completed successfully!"))
            else:
                self.stdout.write(self.style.ERROR(f"✗ Sync failed: {result.get('reason', 'Unknown')}"))
                
        except PluggyItem.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"Item {item_id} not found"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error: {str(e)}"))
            import traceback
            traceback.print_exc()