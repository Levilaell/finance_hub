"""
Force sync today's transactions with timezone debug
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.banking.models import BankAccount
from apps.banking.pluggy_client import PluggyClient
from datetime import datetime, timedelta
import asyncio
import pytz


class Command(BaseCommand):
    help = 'Force sync today transactions with timezone debugging'

    def add_arguments(self, parser):
        parser.add_argument(
            'account_id',
            type=int,
            help='Account ID to sync'
        )

    def handle(self, *args, **options):
        account_id = options['account_id']
        
        try:
            account = BankAccount.objects.get(id=account_id)
            self.stdout.write(f"\nAccount: {account.bank_provider.name} (ID: {account.id})")
            self.stdout.write(f"External ID: {account.external_id}\n")
            
            # Show timezone info
            brazil_tz = pytz.timezone('America/Sao_Paulo')
            now_utc = datetime.now(pytz.UTC)
            now_brazil = now_utc.astimezone(brazil_tz)
            
            self.stdout.write("=== Timezone Info ===")
            self.stdout.write(f"UTC time: {now_utc}")
            self.stdout.write(f"Brazil time: {now_brazil}")
            self.stdout.write(f"Server timezone: {timezone.get_current_timezone()}\n")
            
            # Calculate date range
            # Get today in Brazil timezone
            today_brazil = now_brazil.date()
            yesterday_brazil = today_brazil - timedelta(days=1)
            tomorrow_brazil = today_brazil + timedelta(days=1)
            
            self.stdout.write("=== Sync Date Range ===")
            self.stdout.write(f"Yesterday (Brazil): {yesterday_brazil}")
            self.stdout.write(f"Today (Brazil): {today_brazil}")
            self.stdout.write(f"Tomorrow (Brazil): {tomorrow_brazil}\n")
            
            async def fetch_transactions():
                async with PluggyClient() as client:
                    # Try different date ranges
                    for from_date, to_date, label in [
                        (yesterday_brazil, tomorrow_brazil, "Yesterday to Tomorrow"),
                        (today_brazil, tomorrow_brazil, "Today to Tomorrow"),
                        (yesterday_brazil, today_brazil, "Yesterday to Today"),
                    ]:
                        self.stdout.write(f"\n=== Fetching: {label} ===")
                        self.stdout.write(f"From: {from_date} To: {to_date}")
                        
                        try:
                            response = await client.get_transactions(
                                account.external_id,
                                from_date=from_date.isoformat(),
                                to_date=to_date.isoformat(),
                                page=1,
                                page_size=50
                            )
                            
                            transactions = response.get('results', [])
                            self.stdout.write(f"Found {len(transactions)} transactions")
                            
                            if transactions:
                                self.stdout.write("\nRecent transactions:")
                                for trans in transactions[:5]:
                                    date = trans.get('date', 'N/A')
                                    desc = trans.get('description', 'N/A')[:50]
                                    amount = trans.get('amount', 0)
                                    self.stdout.write(f"  {date}: {desc} (R$ {amount})")
                                    
                        except Exception as e:
                            self.stdout.write(self.style.ERROR(f"Error: {e}"))
                    
                    # Also check account balance
                    self.stdout.write("\n=== Account Balance ===")
                    account_data = await client.get_account(account.external_id)
                    balance = account_data.get('balance', 'N/A')
                    self.stdout.write(f"Current balance in Pluggy: R$ {balance}")
                    self.stdout.write(f"Balance in database: R$ {account.current_balance}")
            
            # Run async function
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(fetch_transactions())
            finally:
                loop.close()
                
        except BankAccount.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"Account {account_id} not found"))