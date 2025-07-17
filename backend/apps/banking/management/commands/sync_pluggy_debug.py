"""
Debug Pluggy sync with detailed logging
"""
from django.core.management.base import BaseCommand
from django.conf import settings
from apps.banking.models import BankAccount
from apps.banking.pluggy_sync_service import pluggy_sync_service
import asyncio
import logging

# Configure detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

class Command(BaseCommand):
    help = 'Debug sync Pluggy transactions with detailed logging'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--account-id',
            type=int,
            help='Specific account ID to sync'
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=1,
            help='Number of accounts to sync'
        )
    
    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('\n=== PLUGGY SYNC DEBUG ===\n'))
        
        # Get accounts to sync
        queryset = BankAccount.objects.filter(
            external_id__isnull=False,
            status='active'
        )
        
        if options['account_id']:
            queryset = queryset.filter(id=options['account_id'])
        
        accounts = queryset[:options['limit']]
        
        if not accounts:
            self.stdout.write(self.style.ERROR('No active Pluggy accounts found!'))
            return
        
        # Run sync
        for account in accounts:
            self.stdout.write(f"\nSyncing account: {account.bank_provider.name} - {account.id}")
            self.stdout.write(f"External ID: {account.external_id}\n")
            
            # Run async sync
            result = asyncio.run(pluggy_sync_service.sync_account_transactions(account))
            
            self.stdout.write(f"\nResult: {result}")
            
            if result.get('status') == 'success':
                self.stdout.write(
                    self.style.SUCCESS(
                        f"✅ Synced {result['transactions']} transactions"
                    )
                )
            else:
                self.stdout.write(
                    self.style.ERROR(
                        f"❌ Sync failed: {result.get('error', 'Unknown error')}"
                    )
                )