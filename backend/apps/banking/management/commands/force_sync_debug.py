"""
Force sync with detailed debug information
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.banking.models import BankAccount
from apps.banking.pluggy_sync_service import PluggyTransactionSyncService
import asyncio
import json


class Command(BaseCommand):
    help = 'Force sync account with detailed debug'

    def add_arguments(self, parser):
        parser.add_argument(
            'account_id',
            type=int,
            help='Account ID to sync'
        )
        parser.add_argument(
            '--days',
            type=int,
            default=30,
            help='Number of days to sync (default: 30)'
        )

    def handle(self, *args, **options):
        account_id = options['account_id']
        days = options['days']
        
        try:
            account = BankAccount.objects.get(id=account_id)
            self.stdout.write(f"Account: {account.bank_provider.name} (ID: {account.id})")
            self.stdout.write(f"External ID: {account.external_id}")
            self.stdout.write(f"Item ID: {account.pluggy_item_id}")
            self.stdout.write(f"Last sync: {account.last_sync_at}")
            
            # Count existing transactions
            existing_count = account.transactions.count()
            self.stdout.write(f"\nExisting transactions: {existing_count}")
            
            # Force sync
            self.stdout.write(f"\nStarting sync for last {days} days...")
            
            sync_service = PluggyTransactionSyncService()
            
            async def do_sync():
                try:
                    # Get the sync service instance
                    result = await sync_service.sync_account_transactions(account)
                    return result
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"Sync error: {str(e)}"))
                    import traceback
                    traceback.print_exc()
                    return {'error': str(e)}
            
            # Run sync
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(do_sync())
                
                if 'error' in result:
                    self.stdout.write(self.style.ERROR(f"\n❌ Sync failed: {result['error']}"))
                else:
                    self.stdout.write(self.style.SUCCESS(f"\n✅ Sync completed"))
                    
                    # Check new transactions
                    account.refresh_from_db()
                    new_count = account.transactions.count()
                    added = new_count - existing_count
                    
                    self.stdout.write(f"\nTransactions after sync: {new_count}")
                    self.stdout.write(f"New transactions added: {added}")
                    
                    # Show recent transactions
                    recent = account.transactions.order_by('-transaction_date')[:5]
                    if recent:
                        self.stdout.write("\nMost recent transactions:")
                        for trans in recent:
                            self.stdout.write(
                                f"  {trans.transaction_date}: {trans.description[:50]} "
                                f"(R$ {trans.amount})"
                            )
                    
                    # Update sync timestamp
                    account.last_sync_at = timezone.now()
                    account.save(update_fields=['last_sync_at'])
                    
            finally:
                loop.close()
                
        except BankAccount.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"Account {account_id} not found"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error: {e}"))