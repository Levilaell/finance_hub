from django.core.management.base import BaseCommand
from apps.banking.models import BankAccount
from apps.banking.pluggy_sync_service import pluggy_sync_service
from apps.banking.pluggy_client import PluggyClient
import asyncio

class Command(BaseCommand):
    help = 'Debug forced sync for recent transactions'

    def add_arguments(self, parser):
        parser.add_argument('--email', type=str, default='levilaelsilvaa@gmail.com')

    def handle(self, *args, **options):
        email = options['email']
        
        self.stdout.write(f"🔍 Debug sync for {email}")
        
        # Get account
        from apps.companies.models import Company
        company = Company.objects.filter(owner__email=email).first()
        
        if not company:
            self.stdout.write(self.style.ERROR('❌ Company not found'))
            return
        
        account = BankAccount.objects.filter(
            company=company,
            is_active=True,
            external_id__isnull=False
        ).first()
        
        if not account:
            self.stdout.write(self.style.ERROR('❌ No active Pluggy account found'))
            return
        
        self.stdout.write(self.style.SUCCESS(f'✅ Found account: {account}'))
        self.stdout.write(f'   External ID: {account.external_id}')
        self.stdout.write(f'   Item ID: {account.pluggy_item_id}')
        self.stdout.write(f'   Last sync: {account.last_sync_at}')
        
        # Run sync with debug
        asyncio.run(self.debug_sync(account))
    
    async def debug_sync(self, account):
        self.stdout.write(f'\n🔄 Starting debug sync...')
        
        # Step 1: Check item status
        if account.pluggy_item_id:
            try:
                async with PluggyClient() as client:
                    self.stdout.write(f'\n📋 Checking item status...')
                    item = await client.get_item(account.pluggy_item_id)
                    self.stdout.write(f'   Status: {item.get("status")}')
                    self.stdout.write(f'   Updated: {item.get("updatedAt")}')
                    self.stdout.write(f'   Error: {item.get("error")}')
                    
                    # Step 2: Force sync
                    self.stdout.write(f'\n🔄 Forcing item sync...')
                    sync_result = await client.sync_item(account.pluggy_item_id)
                    self.stdout.write(f'   Sync result: {sync_result}')
                    
                    # Step 3: Wait and check again
                    self.stdout.write(f'\n⏳ Waiting 5 seconds...')
                    await asyncio.sleep(5)
                    
                    item_after = await client.get_item(account.pluggy_item_id)
                    self.stdout.write(f'\n📋 Item status after sync:')
                    self.stdout.write(f'   Status: {item_after.get("status")}')
                    self.stdout.write(f'   Updated: {item_after.get("updatedAt")}')
                    self.stdout.write(f'   Last update request: {item_after.get("lastUpdateRequest")}')
                    
                    # Step 4: Try transactions
                    self.stdout.write(f'\n📊 Checking transactions from API...')
                    from datetime import datetime, timedelta
                    
                    from_date = (datetime.now() - timedelta(days=2)).date()
                    to_date = (datetime.now() + timedelta(days=1)).date()
                    
                    response = await client.get_transactions(
                        account.external_id,
                        from_date=from_date.isoformat(),
                        to_date=to_date.isoformat(),
                        page=1,
                        page_size=50
                    )
                    
                    transactions = response.get('results', [])
                    self.stdout.write(f'   Found {len(transactions)} transactions')
                    
                    if transactions:
                        self.stdout.write(f'\n📋 Recent transactions:')
                        for i, tx in enumerate(transactions[:5]):
                            self.stdout.write(f'\n   {i+1}. {tx.get("description", "No description")}')
                            self.stdout.write(f'      Date: {tx.get("date")}')
                            self.stdout.write(f'      Amount: R$ {tx.get("amount")}')
                            self.stdout.write(f'      ID: {tx.get("id")}')
                    
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'❌ Error: {e}'))
                import traceback
                traceback.print_exc()
        
        # Step 5: Run full sync
        self.stdout.write(f'\n🔄 Running full account sync...')
        try:
            result = await pluggy_sync_service.sync_account_transactions(account)
            self.stdout.write(f'\n✅ Sync completed:')
            self.stdout.write(f'   Status: {result.get("status")}')
            self.stdout.write(f'   New transactions: {result.get("transactions", 0)}')
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Sync error: {e}'))
            import traceback
            traceback.print_exc()