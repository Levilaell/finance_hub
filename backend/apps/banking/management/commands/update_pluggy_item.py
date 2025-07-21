"""
Check and update Pluggy item status
"""
from django.core.management.base import BaseCommand
from apps.banking.models import BankAccount
from apps.banking.pluggy_client import PluggyClient
import asyncio
from datetime import datetime


class Command(BaseCommand):
    help = 'Check and force update Pluggy item'

    def add_arguments(self, parser):
        parser.add_argument(
            'account_id',
            type=int,
            help='Account ID to check'
        )
        parser.add_argument(
            '--force-update',
            action='store_true',
            help='Force item update'
        )

    def handle(self, *args, **options):
        account_id = options['account_id']
        
        try:
            account = BankAccount.objects.get(id=account_id)
            
            if not account.pluggy_item_id:
                self.stdout.write(self.style.ERROR("Account has no pluggy_item_id"))
                return
            
            self.stdout.write(f"\nAccount: {account.bank_provider.name} (ID: {account.id})")
            self.stdout.write(f"Item ID: {account.pluggy_item_id}\n")
            
            async def check_and_update():
                async with PluggyClient() as client:
                    # Get item status
                    self.stdout.write("=== Current Item Status ===")
                    item = await client.get_item(account.pluggy_item_id)
                    
                    status = item.get('status', 'UNKNOWN')
                    updated_at = item.get('updatedAt', 'N/A')
                    created_at = item.get('createdAt', 'N/A')
                    
                    self.stdout.write(f"Status: {status}")
                    self.stdout.write(f"Created: {created_at}")
                    self.stdout.write(f"Last Updated: {updated_at}")
                    
                    if 'error' in item and item.get('error'):
                        self.stdout.write(f"Error: {item['error'].get('message', 'Unknown error')}")
                    
                    # Calculate time since last update
                    if updated_at != 'N/A':
                        try:
                            # Parse ISO format
                            last_update = datetime.fromisoformat(updated_at.replace('Z', '+00:00'))
                            now = datetime.now(last_update.tzinfo)
                            time_diff = now - last_update
                            
                            hours = time_diff.total_seconds() / 3600
                            self.stdout.write(f"Hours since last update: {hours:.1f}")
                            
                            if hours < 1:
                                self.stdout.write(self.style.SUCCESS("✅ Item was updated recently"))
                            else:
                                self.stdout.write(self.style.WARNING(f"⚠️ Item hasn't been updated in {hours:.1f} hours"))
                        except:
                            pass
                    
                    # Force update if requested
                    if options['force_update'] and status in ['ACTIVE', 'UPDATED']:
                        self.stdout.write("\n=== Forcing Item Update ===")
                        try:
                            # Trigger item update
                            update_response = await client._make_request(
                                'PATCH',
                                f'/items/{account.pluggy_item_id}',
                                json={}
                            )
                            
                            new_status = update_response.get('status', 'UNKNOWN')
                            self.stdout.write(f"Update triggered - New status: {new_status}")
                            
                            if new_status == 'UPDATING':
                                self.stdout.write(self.style.SUCCESS("✅ Item is now updating"))
                                self.stdout.write("Wait a few minutes for the update to complete")
                                self.stdout.write("The webhook should fire when new transactions are found")
                            else:
                                self.stdout.write(f"Response: {update_response}")
                                
                        except Exception as e:
                            self.stdout.write(self.style.ERROR(f"❌ Failed to update item: {e}"))
                    
                    elif status != 'ACTIVE':
                        self.stdout.write(self.style.WARNING("\n⚠️ Item is not ACTIVE, cannot force update"))
                        self.stdout.write("The item needs to be in ACTIVE status to update")
                    
                    # Suggestions
                    self.stdout.write("\n=== Next Steps ===")
                    if status == 'ACTIVE' and not options['force_update']:
                        self.stdout.write("1. Run with --force-update to trigger an update")
                    self.stdout.write("2. Wait for the update to complete (usually 1-3 minutes)")
                    self.stdout.write("3. Check if webhook fires with new transactions")
                    self.stdout.write("4. Monitor with: python manage.py monitor_webhook --account-id " + str(account_id))
            
            # Run async function
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(check_and_update())
            finally:
                loop.close()
                
        except BankAccount.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"Account {account_id} not found"))