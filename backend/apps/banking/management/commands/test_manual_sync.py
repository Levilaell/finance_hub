"""
Test manual synchronization with item update
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.banking.models import BankConnection
from apps.banking.services import BankConnectionService, TransactionService
from apps.banking.pluggy_client import PluggyClient
import logging

User = get_user_model()
logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Test manual synchronization with item update'

    def add_arguments(self, parser):
        parser.add_argument(
            '--connection-id',
            type=int,
            help='ID of the bank connection to test'
        )
        parser.add_argument(
            '--user-email',
            type=str,
            help='Email of the user who owns the connection'
        )
        parser.add_argument(
            '--item-id',
            type=str,
            help='Pluggy item ID to test directly'
        )

    def handle(self, *args, **options):
        # Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

        self.stdout.write("Testing manual synchronization with item update...")

        # Get the connection
        connection = None
        if options.get('connection_id'):
            try:
                connection = BankConnection.objects.get(id=options['connection_id'])
                self.stdout.write(f"Found connection: {connection.id}")
            except BankConnection.DoesNotExist:
                self.stdout.write(self.style.ERROR(f"Connection {options['connection_id']} not found"))
                return
        elif options.get('user_email'):
            try:
                user = User.objects.get(email=options['user_email'])
                connection = BankConnection.objects.filter(user=user, is_active=True).first()
                if not connection:
                    self.stdout.write(self.style.ERROR(f"No active connections for user {options['user_email']}"))
                    return
                self.stdout.write(f"Found connection: {connection.id}")
            except User.DoesNotExist:
                self.stdout.write(self.style.ERROR(f"User {options['user_email']} not found"))
                return

        # Test with direct item ID if provided
        if options.get('item_id'):
            self._test_direct_item_update(options['item_id'])
        elif connection:
            self._test_connection_sync(connection)
        else:
            self.stdout.write(self.style.ERROR("Please provide --connection-id, --user-email, or --item-id"))

    def _test_direct_item_update(self, item_id):
        """Test updating an item directly using Pluggy API"""
        self.stdout.write(f"\n{'='*50}")
        self.stdout.write(f"Testing direct item update for: {item_id}")
        self.stdout.write(f"{'='*50}\n")

        try:
            client = PluggyClient()

            # 1. Get current item status
            self.stdout.write("1. Getting current item status...")
            item = client.get_item(item_id)
            self.stdout.write(f"   Current status: {item['status']}")
            self.stdout.write(f"   Last update: {item.get('lastUpdatedAt', 'N/A')}")

            # 2. Trigger item update
            self.stdout.write("\n2. Triggering item update...")
            updated_item = client.trigger_item_update(item_id)
            self.stdout.write(f"   New status: {updated_item['status']}")

            # 3. Check if MFA is required
            if updated_item['status'] == 'WAITING_USER_INPUT':
                self.stdout.write(self.style.WARNING("\n   ⚠️  MFA Required!"))
                parameter = updated_item.get('parameter', {})
                self.stdout.write(f"   Parameter: {parameter.get('name', 'N/A')}")
                self.stdout.write(f"   Label: {parameter.get('label', 'N/A')}")
                self.stdout.write(f"   Expires at: {parameter.get('expiresAt', 'N/A')}")
            elif updated_item['status'] == 'LOGIN_ERROR':
                self.stdout.write(self.style.ERROR("\n   ❌ Login Error - Invalid credentials"))
            elif updated_item['status'] == 'UPDATING':
                self.stdout.write(self.style.SUCCESS("\n   ✅ Item is updating successfully"))
            else:
                self.stdout.write(f"\n   Status: {updated_item['status']}")

            self.stdout.write(self.style.SUCCESS("\n✅ Direct item update test completed"))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"\n❌ Error: {e}"))

    def _test_connection_sync(self, connection):
        """Test synchronization through the service layer"""
        self.stdout.write(f"\n{'='*50}")
        self.stdout.write(f"Testing connection sync for: {connection.connector.name}")
        self.stdout.write(f"Item ID: {connection.pluggy_item_id}")
        self.stdout.write(f"{'='*50}\n")

        try:
            # 1. Check current status
            connection_service = BankConnectionService()
            self.stdout.write("1. Checking current connection status...")
            updated_connection = connection_service.update_connection_status(connection)
            self.stdout.write(f"   Status: {updated_connection.status}")

            # 2. Trigger manual sync
            self.stdout.write("\n2. Triggering manual sync...")
            sync_result = connection_service.trigger_manual_sync(connection)
            self.stdout.write(f"   Sync status: {sync_result['status']}")
            self.stdout.write(f"   Message: {sync_result['message']}")

            if sync_result['status'] == 'MFA_REQUIRED':
                self.stdout.write(self.style.WARNING("\n   ⚠️  MFA Required!"))
                parameter = sync_result.get('parameter', {})
                self.stdout.write(f"   Parameter details: {parameter}")
            elif sync_result['status'] == 'CREDENTIALS_REQUIRED':
                self.stdout.write(self.style.ERROR("\n   ❌ Credentials Required - Please reconnect"))
            elif sync_result['status'] == 'SYNC_TRIGGERED':
                self.stdout.write(self.style.SUCCESS("\n   ✅ Sync triggered successfully"))

                # 3. Try to sync transactions
                self.stdout.write("\n3. Attempting to sync transactions...")
                transaction_service = TransactionService()

                # Get first account
                account = connection.accounts.filter(is_active=True).first()
                if account:
                    self.stdout.write(f"   Syncing account: {account.name}")
                    try:
                        # Don't trigger update again since we just did it
                        count = transaction_service.sync_transactions(account, trigger_update=False)
                        self.stdout.write(self.style.SUCCESS(f"   ✅ Synced {count} transactions"))
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f"   ❌ Error syncing transactions: {e}"))
                else:
                    self.stdout.write(self.style.WARNING("   No active accounts found"))

            self.stdout.write(self.style.SUCCESS("\n✅ Connection sync test completed"))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"\n❌ Error: {e}"))

        # Summary
        self.stdout.write(f"\n{'='*50}")
        self.stdout.write("Summary:")
        self.stdout.write(f"- Connection ID: {connection.id}")
        self.stdout.write(f"- Item ID: {connection.pluggy_item_id}")
        self.stdout.write(f"- Status: {connection.status}")
        self.stdout.write(f"- Last updated: {connection.last_updated_at}")
        self.stdout.write(f"{'='*50}")