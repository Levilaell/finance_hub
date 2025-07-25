"""
Management command to sync transactions from Pluggy
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta

from apps.banking.models import BankAccount
from apps.banking.integrations.pluggy.client import PluggyClient
from apps.banking.views.pluggy_views import PluggyCallbackView


class Command(BaseCommand):
    help = 'Sync transactions from Pluggy for existing bank accounts'

    def add_arguments(self, parser):
        parser.add_argument(
            '--account-id',
            type=int,
            help='Sync specific account by ID'
        )
        parser.add_argument(
            '--days',
            type=int,
            default=90,
            help='Number of days to sync (default: 90)'
        )

    def handle(self, *args, **options):
        account_id = options.get('account_id')
        days = options.get('days', 90)
        
        if account_id:
            accounts = BankAccount.objects.filter(id=account_id, pluggy_item_id__isnull=False)
        else:
            accounts = BankAccount.objects.filter(pluggy_item_id__isnull=False, is_active=True)
        
        if not accounts.exists():
            self.stdout.write(self.style.WARNING('No Pluggy-connected accounts found'))
            return
        
        self.stdout.write(f'Found {accounts.count()} accounts to sync')
        
        pluggy = PluggyClient()
        callback_view = PluggyCallbackView()
        
        for account in accounts:
            self.stdout.write(f'\nSyncing account: {account} (ID: {account.id})')
            
            try:
                # Update account balance first
                self.stdout.write('Fetching account details...')
                accounts_data = pluggy.get_accounts(account.pluggy_item_id)
                
                for acc_data in accounts_data:
                    if acc_data.get('id') == account.external_id:
                        account.current_balance = float(acc_data.get('balance', 0))
                        account.available_balance = float(acc_data.get('balance', 0))
                        account.last_sync_at = timezone.now()
                        account.save()
                        self.stdout.write(f'Updated balance: R$ {account.current_balance}')
                        break
                
                # Sync transactions
                self.stdout.write(f'Syncing transactions for last {days} days...')
                callback_view._sync_transactions(account, pluggy)
                
                # Count transactions
                from_date = timezone.now() - timedelta(days=days)
                transaction_count = account.transactions.filter(
                    transaction_date__gte=from_date
                ).count()
                
                self.stdout.write(
                    self.style.SUCCESS(
                        f'✓ Successfully synced {transaction_count} transactions'
                    )
                )
                
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'✗ Error syncing account {account.id}: {e}')
                )