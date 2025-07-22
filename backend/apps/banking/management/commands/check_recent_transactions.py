from django.core.management.base import BaseCommand
from apps.banking.models import BankAccount, Transaction
from apps.banking.pluggy_client import PluggyClient
from datetime import datetime, timedelta
import asyncio
from decimal import Decimal

class Command(BaseCommand):
    help = 'Check recent transactions from Pluggy API'

    def add_arguments(self, parser):
        parser.add_argument('--email', type=str, default='levilaelsilvaa@gmail.com')
        parser.add_argument('--days', type=int, default=2)

    def handle(self, *args, **options):
        email = options['email']
        days = options['days']
        
        self.stdout.write(f"🔍 Checking transactions for {email}")
        self.stdout.write(f"📅 Looking back {days} days")
        
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
        self.stdout.write(f'   Last sync: {account.last_sync_at}')
        
        # Run async function
        asyncio.run(self.check_transactions(account, days))
    
    async def check_transactions(self, account, days):
        try:
            async with PluggyClient() as client:
                from_date = (datetime.now() - timedelta(days=days)).date()
                to_date = (datetime.now() + timedelta(days=1)).date()
                
                self.stdout.write(f'\n📡 Fetching from Pluggy API...')
                self.stdout.write(f'   Period: {from_date} to {to_date}')
                
                response = await client.get_transactions(
                    account.external_id,
                    from_date=from_date.isoformat(),
                    to_date=to_date.isoformat(),
                    page=1,
                    page_size=100
                )
                
                transactions = response.get('results', [])
                self.stdout.write(self.style.SUCCESS(f'\n📊 Found {len(transactions)} transactions'))
                
                # Filter small transactions
                small_txs = []
                for tx in transactions:
                    amount = abs(Decimal(str(tx.get('amount', '0'))))
                    if amount <= Decimal('0.10'):  # 10 cents or less
                        small_txs.append(tx)
                
                if small_txs:
                    self.stdout.write(self.style.WARNING(f'\n💰 Small transactions found: {len(small_txs)}'))
                    for tx in small_txs:
                        self.stdout.write(f'\n{"="*60}')
                        self.stdout.write(f'ID: {tx.get("id")}')
                        self.stdout.write(f'Date: {tx.get("date")}')
                        self.stdout.write(f'Amount: R$ {tx.get("amount")}')
                        self.stdout.write(f'Type: {tx.get("type")}')
                        self.stdout.write(f'Description: {tx.get("description")}')
                        self.stdout.write(f'Status: {tx.get("status")}')
                        
                        # Check if exists locally
                        exists = Transaction.objects.filter(
                            bank_account=account,
                            external_id=str(tx.get('id'))
                        ).exists()
                        
                        if exists:
                            self.stdout.write(self.style.SUCCESS('✅ EXISTS in local database'))
                        else:
                            self.stdout.write(self.style.ERROR('❌ MISSING from local database'))
                            
                            # Show why it might be missing
                            tx_date = tx.get('date', '')
                            self.stdout.write(f'\n🔍 Debug info:')
                            self.stdout.write(f'   - Transaction date: {tx_date}')
                            self.stdout.write(f'   - Current time: {datetime.now()}')
                            
                            if account.last_sync_at:
                                hours_since = (datetime.now() - account.last_sync_at.replace(tzinfo=None)).total_seconds() / 3600
                                self.stdout.write(f'   - Hours since last sync: {hours_since:.1f}')
                                self.stdout.write(f'   - Sync window used: {"2 days" if hours_since < 24 else "3+ days"}')
                else:
                    self.stdout.write(self.style.WARNING('\n⚠️ No small transactions found'))
                
                # Show recent transactions regardless of amount
                self.stdout.write(f'\n\n📋 Recent transactions (any amount):')
                for i, tx in enumerate(transactions[:10]):
                    self.stdout.write(f'\n{i+1}. {tx.get("description", "No description")}')
                    self.stdout.write(f'   Date: {tx.get("date")}')
                    self.stdout.write(f'   Amount: R$ {tx.get("amount")}')
                    self.stdout.write(f'   Type: {tx.get("type")}')
                    
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'\n❌ Error: {e}'))
            import traceback
            traceback.print_exc()