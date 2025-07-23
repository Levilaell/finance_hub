"""
Check Pluggy auto-sync status and configuration
"""
from django.core.management.base import BaseCommand
from apps.banking.models import BankAccount
from apps.banking.pluggy_client import PluggyClient
import asyncio
from datetime import datetime, timezone, timedelta


class Command(BaseCommand):
    help = 'Check Pluggy auto-sync status and when items were last updated'

    def add_arguments(self, parser):
        parser.add_argument(
            'account_id',
            type=int,
            help='Account ID to check'
        )

    def handle(self, *args, **options):
        account_id = options['account_id']
        
        try:
            account = BankAccount.objects.get(id=account_id)
            
            if not account.pluggy_item_id:
                self.stdout.write(self.style.ERROR("Account has no pluggy_item_id"))
                return
            
            self.stdout.write(f"\n=== Account Info ===")
            self.stdout.write(f"Account: {account.bank_provider.name} (ID: {account.id})")
            self.stdout.write(f"Item ID: {account.pluggy_item_id}")
            self.stdout.write(f"Last sync in DB: {account.last_sync_at}\n")
            
            async def check_item_status():
                async with PluggyClient() as client:
                    # Get item details
                    item = await client.get_item(account.pluggy_item_id)
                    
                    status = item.get('status', 'UNKNOWN')
                    updated_at = item.get('updatedAt', 'N/A')
                    created_at = item.get('createdAt', 'N/A')
                    connector = item.get('connector', {})
                    
                    self.stdout.write("=== Pluggy Item Status ===")
                    self.stdout.write(f"Status: {status}")
                    self.stdout.write(f"Created: {created_at}")
                    self.stdout.write(f"Last Updated: {updated_at}")
                    self.stdout.write(f"Connector: {connector.get('name', 'Unknown')}")
                    
                    # Check auto-sync eligibility
                    is_updatable = item.get('isUpdatable', False)
                    self.stdout.write(f"\nAuto-sync eligible: {'Yes' if is_updatable else 'No'}")
                    
                    if not is_updatable:
                        self.stdout.write(self.style.WARNING("⚠️ This item is NOT eligible for auto-sync"))
                        self.stdout.write("Possible reasons:")
                        self.stdout.write("- Connector requires manual intervention")
                        self.stdout.write("- Item is in error state")
                        self.stdout.write("- Subscription doesn't include auto-sync")
                    
                    # Calculate time since last update
                    if updated_at != 'N/A':
                        try:
                            last_update = datetime.fromisoformat(updated_at.replace('Z', '+00:00'))
                            now = datetime.now(timezone.utc)
                            time_diff = now - last_update
                            
                            hours = time_diff.total_seconds() / 3600
                            self.stdout.write(f"\nHours since last update: {hours:.1f}")
                            
                            # Auto-sync intervals based on Pluggy docs
                            if is_updatable:
                                if hours < 8:
                                    self.stdout.write(self.style.SUCCESS("✅ Recently updated, auto-sync should run within 8-24 hours"))
                                elif hours < 24:
                                    self.stdout.write(self.style.WARNING("⏳ Auto-sync should run soon (within 24 hours of last update)"))
                                else:
                                    self.stdout.write(self.style.ERROR("❌ Auto-sync may have failed - last update was over 24 hours ago"))
                        except:
                            pass
                    
                    # Check for errors
                    if 'error' in item and item.get('error'):
                        self.stdout.write(f"\n⚠️ Item Error: {item['error'].get('message', 'Unknown error')}")
                    
                    # Get recent transactions to verify if new ones are available
                    self.stdout.write("\n=== Checking Recent Transactions ===")
                    
                    # Get transactions from the last 3 days
                    from_date = (datetime.now() - timedelta(days=3)).date()
                    to_date = (datetime.now() + timedelta(days=1)).date()
                    
                    response = await client.get_transactions(
                        account.external_id,
                        from_date=from_date.isoformat(),
                        to_date=to_date.isoformat(),
                        page=1,
                        page_size=10
                    )
                    
                    transactions = response.get('results', [])
                    self.stdout.write(f"Found {len(transactions)} transactions in the last 3 days")
                    
                    if transactions:
                        self.stdout.write("\nMost recent transactions:")
                        for i, trans in enumerate(transactions[:5]):
                            date = trans.get('date', 'N/A')
                            desc = trans.get('description', 'N/A')[:50]
                            amount = trans.get('amount', 0)
                            trans_id = trans.get('id', 'N/A')
                            self.stdout.write(f"{i+1}. {date}: {desc} (R$ {amount}) - ID: {trans_id}")
                    
                    # Recommendations
                    self.stdout.write("\n=== Recommendations ===")
                    
                    if status == 'WAITING_USER_ACTION':
                        self.stdout.write(self.style.ERROR("1. User needs to re-authenticate in the bank"))
                        self.stdout.write("   The bank is requesting additional authentication")
                    elif status == 'LOGIN_ERROR':
                        self.stdout.write(self.style.ERROR("1. User needs to update their bank credentials"))
                    elif not is_updatable:
                        self.stdout.write(self.style.WARNING("1. This item requires manual sync"))
                        self.stdout.write("   Auto-sync is not available for this connector")
                    elif hours > 24:
                        self.stdout.write(self.style.WARNING("1. Auto-sync may have issues"))
                        self.stdout.write("   Consider contacting Pluggy support if this persists")
                    else:
                        self.stdout.write(self.style.SUCCESS("1. Wait for auto-sync to run"))
                        self.stdout.write("   Pluggy will automatically sync within 8-24 hours")
                    
                    self.stdout.write("\n2. Alternative: Use webhooks to get real-time updates")
                    self.stdout.write("3. Monitor webhook events with: python manage.py monitor_webhook")
            
            # Run async function
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(check_item_status())
            finally:
                loop.close()
                
        except BankAccount.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"Account {account_id} not found"))