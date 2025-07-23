"""
Check for recent transactions directly from Pluggy API
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.banking.models import BankAccount, Transaction
from apps.banking.pluggy_client import PluggyClient
from datetime import datetime, timedelta
import asyncio
import pytz


class Command(BaseCommand):
    help = 'Check recent transactions from Pluggy API and compare with database'

    def add_arguments(self, parser):
        parser.add_argument(
            'account_id',
            type=int,
            help='Account ID to check'
        )
        parser.add_argument(
            '--days',
            type=int,
            default=3,
            help='Number of days to check (default: 3)'
        )
        parser.add_argument(
            '--force-update',
            action='store_true',
            help='Force item update before checking'
        )

    def handle(self, *args, **options):
        account_id = options['account_id']
        days_back = options['days']
        
        try:
            account = BankAccount.objects.get(id=account_id)
            
            if not account.external_id:
                self.stdout.write(self.style.ERROR("Account has no external_id"))
                return
            
            self.stdout.write(f"\n=== Account Info ===")
            self.stdout.write(f"Account: {account.bank_provider.name} (ID: {account.id})")
            self.stdout.write(f"External ID: {account.external_id}")
            self.stdout.write(f"Item ID: {account.pluggy_item_id}")
            self.stdout.write(f"Last sync: {account.last_sync_at}")
            
            # Show timezone info
            brazil_tz = pytz.timezone('America/Sao_Paulo')
            now_utc = datetime.now(pytz.UTC)
            now_brazil = now_utc.astimezone(brazil_tz)
            
            self.stdout.write(f"\n=== Current Time ===")
            self.stdout.write(f"UTC: {now_utc}")
            self.stdout.write(f"Brazil: {now_brazil}")
            
            async def check_transactions():
                async with PluggyClient() as client:
                    # Check item status first
                    if account.pluggy_item_id:
                        self.stdout.write(f"\n=== Item Status ===")
                        item = await client.get_item(account.pluggy_item_id)
                        status = item.get('status')
                        updated_at = item.get('updatedAt')
                        self.stdout.write(f"Status: {status}")
                        self.stdout.write(f"Last updated: {updated_at}")
                        
                        if updated_at:
                            last_update = datetime.fromisoformat(updated_at.replace('Z', '+00:00'))
                            hours_ago = (now_utc - last_update).total_seconds() / 3600
                            self.stdout.write(f"Hours since update: {hours_ago:.1f}")
                        
                        # Force update if requested
                        if options['force_update'] and status in ['ACTIVE', 'UPDATED']:
                            self.stdout.write(f"\n=== Forcing Item Update ===")
                            try:
                                response = await client.sync_item(account.pluggy_item_id)
                                new_status = response.get('status')
                                self.stdout.write(f"Update triggered, new status: {new_status}")
                                self.stdout.write("Waiting 10 seconds for update to process...")
                                await asyncio.sleep(10)
                            except Exception as e:
                                self.stdout.write(self.style.ERROR(f"Failed to update: {e}"))
                    
                    # Get transactions
                    from_date = (datetime.now() - timedelta(days=days_back)).date()
                    to_date = (datetime.now() + timedelta(days=1)).date()
                    
                    self.stdout.write(f"\n=== Fetching Transactions ===")
                    self.stdout.write(f"Date range: {from_date} to {to_date}")
                    
                    response = await client.get_transactions(
                        account.external_id,
                        from_date=from_date.isoformat(),
                        to_date=to_date.isoformat(),
                        page=1,
                        page_size=100
                    )
                    
                    api_transactions = response.get('results', [])
                    total_count = response.get('total', len(api_transactions))
                    
                    self.stdout.write(f"\nFound {len(api_transactions)} transactions (total: {total_count})")
                    
                    if api_transactions:
                        # Get existing transaction IDs from database
                        existing_ids = set(
                            Transaction.objects.filter(
                                bank_account=account,
                                external_id__isnull=False
                            ).values_list('external_id', flat=True)
                        )
                        
                        self.stdout.write(f"\n=== Transaction Analysis ===")
                        self.stdout.write(f"Transactions in database: {len(existing_ids)}")
                        
                        new_transactions = []
                        existing_transactions = []
                        
                        for trans in api_transactions:
                            trans_id = trans.get('id')
                            if trans_id in existing_ids:
                                existing_transactions.append(trans)
                            else:
                                new_transactions.append(trans)
                        
                        self.stdout.write(f"Already in database: {len(existing_transactions)}")
                        self.stdout.write(f"NEW transactions not in database: {len(new_transactions)}")
                        
                        # Show recent transactions
                        self.stdout.write(f"\n=== Most Recent Transactions (from API) ===")
                        for i, trans in enumerate(api_transactions[:10]):
                            trans_id = trans.get('id')
                            date = trans.get('date', 'N/A')
                            desc = trans.get('description', 'N/A')[:50]
                            amount = trans.get('amount', 0)
                            status = "NEW" if trans_id not in existing_ids else "EXISTS"
                            
                            # Parse date to show in Brazil timezone
                            if date != 'N/A':
                                trans_date = datetime.fromisoformat(date.replace('Z', '+00:00'))
                                trans_date_brazil = trans_date.astimezone(brazil_tz)
                                date_str = trans_date_brazil.strftime('%Y-%m-%d %H:%M')
                            else:
                                date_str = date
                            
                            self.stdout.write(
                                f"{i+1}. [{status}] {date_str}: {desc} (R$ {amount:.2f}) - ID: {trans_id[:8]}..."
                            )
                        
                        if new_transactions:
                            self.stdout.write(self.style.WARNING(
                                f"\n⚠️  Found {len(new_transactions)} NEW transactions not in database!"
                            ))
                            self.stdout.write("These transactions are available in Pluggy but not synced yet.")
                            self.stdout.write("\nRecommendations:")
                            self.stdout.write("1. Run manual sync from the frontend")
                            self.stdout.write("2. Wait for webhook (if auto-sync is working)")
                            self.stdout.write("3. Check webhook configuration in Pluggy dashboard")
                    else:
                        self.stdout.write("\nNo transactions found in the specified date range.")
                    
                    # Check account balance
                    self.stdout.write(f"\n=== Account Balance ===")
                    account_data = await client.get_account(account.external_id)
                    api_balance = account_data.get('balance', 'N/A')
                    self.stdout.write(f"Balance in Pluggy API: R$ {api_balance}")
                    self.stdout.write(f"Balance in database: R$ {account.current_balance}")
                    
                    if api_balance != 'N/A' and abs(float(api_balance) - float(account.current_balance)) > 0.01:
                        self.stdout.write(self.style.WARNING("⚠️  Balance mismatch detected!"))
            
            # Run async function
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(check_transactions())
            finally:
                loop.close()
                
        except BankAccount.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"Account {account_id} not found"))