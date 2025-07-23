"""
Command to check which accounts need reconnection
"""
import asyncio
from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.banking.models import BankAccount
from apps.banking.pluggy_client import PluggyClient
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Check which Pluggy accounts need reconnection'

    def add_arguments(self, parser):
        parser.add_argument(
            '--notify',
            action='store_true',
            help='Send notifications to users'
        )

    def handle(self, *args, **options):
        """Check all Pluggy accounts for reconnection needs"""
        notify = options.get('notify', False)
        
        self.stdout.write("🔍 Checking Pluggy accounts for reconnection needs...")
        
        # Get all active Pluggy accounts
        accounts = BankAccount.objects.filter(
            status='active',
            pluggy_item_id__isnull=False
        ).select_related('company')
        
        self.stdout.write(f"\n📊 Found {accounts.count()} active Pluggy accounts")
        
        # Check each account
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        needs_reconnection = []
        
        async def check_accounts():
            async with PluggyClient() as client:
                for account in accounts:
                    try:
                        item = await client.get_item(account.pluggy_item_id)
                        item_status = item.get('status')
                        
                        if item_status in ['WAITING_USER_ACTION', 'LOGIN_ERROR', 'OUTDATED']:
                            needs_reconnection.append({
                                'account': account,
                                'status': item_status,
                                'bank': account.bank_provider.name if account.bank_provider else 'Unknown',
                                'company': account.company.name if account.company else 'Unknown',
                                'last_sync': account.last_sync_at
                            })
                            
                            # Update account status
                            account.status = 'waiting_user_action'
                            if hasattr(account, 'sync_error_message'):
                                account.sync_error_message = f'Item status: {item_status}'
                            await sync_to_async(account.save)()
                            
                    except Exception as e:
                        self.stdout.write(
                            self.style.ERROR(f"❌ Error checking account {account.id}: {e}")
                        )
        
        from asgiref.sync import sync_to_async
        
        try:
            loop.run_until_complete(check_accounts())
        finally:
            loop.close()
        
        # Report results
        self.stdout.write(f"\n📋 RESULTS:")
        self.stdout.write(f"   Total accounts checked: {accounts.count()}")
        self.stdout.write(f"   Accounts needing reconnection: {len(needs_reconnection)}")
        
        if needs_reconnection:
            self.stdout.write(f"\n⚠️  ACCOUNTS NEEDING RECONNECTION:")
            for item in needs_reconnection:
                account = item['account']
                self.stdout.write(f"\n   🏦 {item['bank']} - {account.nickname}")
                self.stdout.write(f"      Company: {item['company']}")
                self.stdout.write(f"      Status: {item['status']}")
                self.stdout.write(f"      Last sync: {item['last_sync']}")
                self.stdout.write(f"      Account ID: {account.id}")
                
                # Send notification if requested
                if notify and account.company:
                    self._send_notification(account, item['status'])
        
        self.stdout.write(self.style.SUCCESS("\n✅ Check completed"))
    
    def _send_notification(self, account, status):
        """Send notification to user about reconnection need"""
        try:
            # TODO: Implement actual notification system
            # For now, just log
            logger.warning(
                f"📧 Notification needed for account {account.id} "
                f"(Company: {account.company.name}) - Status: {status}"
            )
            
            # You can implement:
            # - Email notification
            # - Push notification
            # - In-app notification
            # - SMS
            
        except Exception as e:
            logger.error(f"Error sending notification: {e}")