"""
Force sync transactions for all active connections
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.banking.models import BankConnection
from apps.banking.services import BankConnectionService, TransactionService
import logging

User = get_user_model()
logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Force sync transactions for all active connections'

    def add_arguments(self, parser):
        parser.add_argument(
            '--connection-id',
            type=str,
            help='Specific connection ID to sync (optional)'
        )
        parser.add_argument(
            '--skip-update',
            action='store_true',
            help='Skip item update and sync directly'
        )

    def handle(self, *args, **options):
        # Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

        connection_id = options.get('connection_id')
        skip_update = options.get('skip_update', False)

        if connection_id:
            connections = BankConnection.objects.filter(id=connection_id, is_active=True)
        else:
            connections = BankConnection.objects.filter(is_active=True)

        self.stdout.write(f"Found {connections.count()} active connections")

        connection_service = BankConnectionService()
        tx_service = TransactionService()

        for conn in connections:
            self.stdout.write(f"\n{'='*50}")
            self.stdout.write(f"Processing: {conn.connector.name}")
            self.stdout.write(f"Item ID: {conn.pluggy_item_id}")
            self.stdout.write(f"Status: {conn.status}")

            try:
                # Update connection status
                self.stdout.write("1. Updating connection status...")
                updated_conn = connection_service.update_connection_status(conn)
                self.stdout.write(f"   New status: {updated_conn.status}")

                # Sync accounts
                self.stdout.write("2. Syncing accounts...")
                account_count = connection_service.sync_accounts(updated_conn)
                self.stdout.write(f"   Synced {account_count} accounts")

                # List accounts
                for account in updated_conn.accounts.all():
                    self.stdout.write(f"   - {account.name}: R$ {account.balance}")

                # Sync transactions
                self.stdout.write("3. Syncing transactions...")
                results = tx_service.sync_all_accounts_transactions(
                    updated_conn,
                    trigger_update=not skip_update
                )

                total = sum(results.values())
                self.stdout.write(f"   Total transactions synced: {total}")

                for account_id, count in results.items():
                    account = updated_conn.accounts.filter(id=account_id).first()
                    if account:
                        self.stdout.write(f"   - {account.name}: {count} transactions")

                self.stdout.write(self.style.SUCCESS(f"✅ Successfully synced {conn.connector.name}"))

            except Exception as e:
                self.stdout.write(self.style.ERROR(f"❌ Error: {e}"))
                import traceback
                traceback.print_exc()

        self.stdout.write(f"\n{'='*50}")
        self.stdout.write(self.style.SUCCESS("Sync complete!"))

        # Show summary
        from apps.banking.models import Transaction
        from django.utils import timezone
        from datetime import timedelta

        recent = Transaction.objects.filter(
            date__gte=timezone.now() - timedelta(days=1)
        ).order_by('-date')[:10]

        self.stdout.write(f"\nRecent transactions (last 24h): {recent.count()}")
        for tx in recent:
            self.stdout.write(f"  {tx.date.strftime('%Y-%m-%d %H:%M')} - {tx.description[:30]} - R$ {tx.amount} ({tx.type})")