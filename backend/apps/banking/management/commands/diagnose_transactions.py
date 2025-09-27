"""
Diagnose transaction sync issues
"""

from django.core.management.base import BaseCommand
from apps.banking.models import BankConnection, BankAccount, Transaction
from apps.banking.pluggy_client import PluggyClient
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
import json


class Command(BaseCommand):
    help = 'Diagnose transaction sync issues'

    def add_arguments(self, parser):
        parser.add_argument(
            '--account-id',
            type=str,
            help='Specific account ID to diagnose'
        )
        parser.add_argument(
            '--days',
            type=int,
            default=7,
            help='Number of days to check (default: 7)'
        )

    def handle(self, *args, **options):
        account_id = options.get('account_id')
        days = options.get('days', 7)

        if account_id:
            accounts = BankAccount.objects.filter(id=account_id)
        else:
            accounts = BankAccount.objects.filter(connection__is_active=True)

        self.stdout.write(f"Diagnosing {accounts.count()} accounts...")

        client = PluggyClient()

        for account in accounts:
            self.stdout.write(f"\n{'='*60}")
            self.stdout.write(f"Account: {account.name}")
            self.stdout.write(f"ID: {account.id}")
            self.stdout.write(f"Pluggy ID: {account.pluggy_account_id}")
            self.stdout.write(f"Balance: R$ {account.balance}")
            self.stdout.write(f"Connection: {account.connection.connector.name}")
            self.stdout.write(f"Connection Status: {account.connection.status}")

            # Get transactions from Pluggy
            date_from = timezone.now() - timedelta(days=days)
            date_to = timezone.now()

            self.stdout.write(f"\nFetching transactions from Pluggy...")
            self.stdout.write(f"Date range: {date_from} to {date_to}")

            try:
                pluggy_transactions = client.get_transactions(
                    account_id=account.pluggy_account_id,
                    date_from=date_from,
                    date_to=date_to
                )

                self.stdout.write(f"Found {len(pluggy_transactions)} transactions from Pluggy")

                # Show recent transactions from Pluggy
                self.stdout.write("\nRecent transactions from Pluggy (last 5):")
                for tx in pluggy_transactions[:5]:
                    tx_date = tx.get('date', 'N/A')
                    tx_desc = tx.get('description', 'N/A')
                    tx_amount = tx.get('amount', 0)
                    tx_type = tx.get('type', 'N/A')
                    self.stdout.write(f"  {tx_date} | {tx_desc[:30]:30} | R$ {tx_amount:10.2f} | {tx_type}")

                # Check transactions in our database
                db_transactions = Transaction.objects.filter(
                    account=account,
                    date__gte=date_from,
                    date__lte=date_to
                ).order_by('-date')

                self.stdout.write(f"\nFound {db_transactions.count()} transactions in database")

                # Show recent transactions from database
                self.stdout.write("\nRecent transactions from database (last 5):")
                for tx in db_transactions[:5]:
                    self.stdout.write(f"  {tx.date} | {tx.description[:30]:30} | R$ {tx.amount:10.2f} | {tx.type}")

                # Compare transactions
                pluggy_ids = {tx['id'] for tx in pluggy_transactions}
                db_ids = set(db_transactions.values_list('pluggy_transaction_id', flat=True))

                missing_in_db = pluggy_ids - db_ids
                extra_in_db = db_ids - pluggy_ids

                if missing_in_db:
                    self.stdout.write(f"\n[WARNING] {len(missing_in_db)} transactions in Pluggy but not in database!")
                    # Show details of missing transactions
                    for tx_id in list(missing_in_db)[:3]:
                        tx = next((t for t in pluggy_transactions if t['id'] == tx_id), None)
                        if tx:
                            self.stdout.write(f"  Missing: {tx['date']} - {tx.get('description', 'N/A')[:30]} - R$ {tx.get('amount', 0):.2f}")

                if extra_in_db:
                    self.stdout.write(f"\n[WARNING] {len(extra_in_db)} transactions in database but not in Pluggy response!")

                # Check for today's transactions specifically
                today_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
                today_pluggy = [tx for tx in pluggy_transactions if tx.get('date', '').startswith(today_start.date().isoformat())]
                today_db = db_transactions.filter(date__gte=today_start)

                self.stdout.write(f"\nToday's transactions ({today_start.date()}):")
                self.stdout.write(f"  From Pluggy: {len(today_pluggy)}")
                self.stdout.write(f"  In database: {today_db.count()}")

                if today_pluggy:
                    self.stdout.write("\nToday's transactions from Pluggy:")
                    for tx in today_pluggy:
                        self.stdout.write(f"  {tx.get('date')} - {tx.get('description', 'N/A')[:30]} - R$ {tx.get('amount', 0):.2f}")

            except Exception as e:
                self.stdout.write(f"[ERROR] Failed to fetch from Pluggy: {e}")

        # Summary
        self.stdout.write(f"\n{'='*60}")
        self.stdout.write("SUMMARY")
        self.stdout.write(f"{'='*60}")

        # Get all transactions from last 24 hours
        last_24h = timezone.now() - timedelta(hours=24)
        recent_txs = Transaction.objects.filter(date__gte=last_24h).order_by('-date')

        self.stdout.write(f"\nTransactions in database (last 24h): {recent_txs.count()}")
        for tx in recent_txs[:5]:
            self.stdout.write(f"  {tx.date} - {tx.account.name} - {tx.description[:30]} - R$ {tx.amount}")

        # Check for 0.15 transaction
        self.stdout.write("\nSearching for 0.15 BRL transaction...")
        fifteen_cents = Transaction.objects.filter(amount=Decimal('0.15')).order_by('-date')[:3]
        for tx in fifteen_cents:
            self.stdout.write(f"  {tx.date} - {tx.account.name} - {tx.description} - R$ {tx.amount}")