from django.core.management.base import BaseCommand
from django.db import transaction
from apps.banking.models import BankAccount
from apps.companies.models import Company, ResourceUsage
from apps.banking.pluggy_sync_service import pluggy_sync_service
import asyncio


class Command(BaseCommand):
    help = 'Test sync counter update after Pluggy sync'

    def add_arguments(self, parser):
        parser.add_argument(
            '--account-id',
            type=int,
            help='Bank account ID to sync'
        )
        parser.add_argument(
            '--company-id',
            type=int,
            help='Company ID to check'
        )

    def handle(self, *args, **options):
        account_id = options.get('account_id')
        company_id = options.get('company_id')
        
        if account_id:
            self.test_account_sync(account_id)
        elif company_id:
            self.check_company_counters(company_id)
        else:
            self.stdout.write(self.style.ERROR('Please provide --account-id or --company-id'))
    
    def test_account_sync(self, account_id):
        """Test sync for specific account"""
        try:
            account = BankAccount.objects.get(id=account_id)
            company = account.company
            
            self.stdout.write(f"\n🏦 Testing sync for account: {account.display_name}")
            self.stdout.write(f"🏢 Company: {company.name}")
            
            # Get counters before sync
            before_company_counter = company.current_month_transactions
            usage_before = ResourceUsage.get_or_create_current_month(company)
            before_usage_counter = usage_before.transactions_count
            
            self.stdout.write(f"\n📊 BEFORE SYNC:")
            self.stdout.write(f"  - Company counter: {before_company_counter}")
            self.stdout.write(f"  - ResourceUsage counter: {before_usage_counter}")
            
            # Run sync
            self.stdout.write(f"\n🔄 Running sync...")
            
            async def run_sync():
                return await pluggy_sync_service.sync_account_transactions(account)
            
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(run_sync())
            loop.close()
            
            self.stdout.write(f"\n✅ Sync result: {result}")
            
            # Refresh from database
            company.refresh_from_db()
            usage_after = ResourceUsage.get_or_create_current_month(company)
            
            # Get counters after sync
            after_company_counter = company.current_month_transactions
            after_usage_counter = usage_after.transactions_count
            
            self.stdout.write(f"\n📊 AFTER SYNC:")
            self.stdout.write(f"  - Company counter: {after_company_counter}")
            self.stdout.write(f"  - ResourceUsage counter: {after_usage_counter}")
            
            # Calculate differences
            company_diff = after_company_counter - before_company_counter
            usage_diff = after_usage_counter - before_usage_counter
            new_transactions = result.get('transactions', 0)
            
            self.stdout.write(f"\n📈 CHANGES:")
            self.stdout.write(f"  - New transactions synced: {new_transactions}")
            self.stdout.write(f"  - Company counter increased by: {company_diff}")
            self.stdout.write(f"  - ResourceUsage counter increased by: {usage_diff}")
            
            # Verify
            if new_transactions > 0:
                if company_diff == new_transactions and usage_diff == new_transactions:
                    self.stdout.write(self.style.SUCCESS("\n✅ Counters updated correctly!"))
                else:
                    self.stdout.write(self.style.ERROR("\n❌ Counter mismatch!"))
                    self.stdout.write(f"Expected increase: {new_transactions}")
                    self.stdout.write(f"Actual company increase: {company_diff}")
                    self.stdout.write(f"Actual usage increase: {usage_diff}")
            else:
                self.stdout.write(self.style.WARNING("\n⚠️ No new transactions synced"))
                
        except BankAccount.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'Account {account_id} not found'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error: {str(e)}'))
            import traceback
            traceback.print_exc()
    
    def check_company_counters(self, company_id):
        """Check company counters"""
        try:
            company = Company.objects.get(id=company_id)
            usage = ResourceUsage.get_or_create_current_month(company)
            
            self.stdout.write(f"\n🏢 Company: {company.name}")
            self.stdout.write(f"\n📊 Current Counters:")
            self.stdout.write(f"  - Company.current_month_transactions: {company.current_month_transactions}")
            self.stdout.write(f"  - ResourceUsage.transactions_count: {usage.transactions_count}")
            
            # Count real transactions
            from apps.banking.models import Transaction
            from django.utils import timezone
            from datetime import datetime
            
            current_month_start = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            
            real_count = Transaction.objects.filter(
                bank_account__company=company,
                transaction_date__gte=current_month_start.date()
            ).count()
            
            self.stdout.write(f"  - Real transaction count (this month): {real_count}")
            
            if company.current_month_transactions != real_count:
                self.stdout.write(self.style.WARNING(f"\n⚠️ Counter mismatch detected!"))
                self.stdout.write(f"Counter says: {company.current_month_transactions}")
                self.stdout.write(f"Real count: {real_count}")
            else:
                self.stdout.write(self.style.SUCCESS(f"\n✅ Counters match real data"))
                
        except Company.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'Company {company_id} not found'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error: {str(e)}'))