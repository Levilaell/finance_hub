"""
Check accounts for a specific user to debug production issues
"""
from django.core.management.base import BaseCommand
from apps.authentication.models import User
from apps.banking.models import BankAccount
import json


class Command(BaseCommand):
    help = 'Check accounts for specific user'

    def add_arguments(self, parser):
        parser.add_argument(
            'email',
            type=str,
            help='User email to check'
        )

    def handle(self, *args, **options):
        email = options['email']
        
        try:
            user = User.objects.get(email=email)
            self.stdout.write(f"\n=== User Info ===")
            self.stdout.write(f"Email: {user.email}")
            self.stdout.write(f"ID: {user.id}")
            self.stdout.write(f"Company: {user.company.name if user.company else 'No company'}")
            
            if not user.company:
                self.stdout.write(self.style.ERROR("User has no company"))
                return
            
            # Get all accounts for this user's company
            accounts = BankAccount.objects.filter(company=user.company).order_by('-created_at')
            
            self.stdout.write(f"\n=== Bank Accounts ({accounts.count()}) ===")
            
            for account in accounts:
                self.stdout.write(f"\nAccount ID: {account.id}")
                self.stdout.write(f"  Bank: {account.bank_provider.name}")
                self.stdout.write(f"  Created: {account.created_at}")
                self.stdout.write(f"  External ID: {account.external_id or 'None'}")
                self.stdout.write(f"  Item ID: {account.pluggy_item_id or 'None'}")
                self.stdout.write(f"  Status: {account.status}")
                self.stdout.write(f"  Active: {account.is_active}")
                self.stdout.write(f"  Balance: R$ {account.current_balance}")
                self.stdout.write(f"  Last Sync: {account.last_sync_at}")
                
                # Check if it's a Pluggy account
                if account.external_id:
                    self.stdout.write(self.style.SUCCESS("  ✅ Pluggy connected"))
                    
                    # Count recent transactions
                    from datetime import datetime, timedelta
                    from django.utils import timezone
                    recent = account.transactions.filter(
                        created_at__gte=timezone.now() - timedelta(hours=1)
                    ).count()
                    
                    if recent > 0:
                        self.stdout.write(self.style.SUCCESS(f"  ✅ {recent} transactions synced in last hour"))
                else:
                    self.stdout.write(self.style.WARNING("  ⚠️  Not connected to Pluggy"))
            
            # Summary
            self.stdout.write(f"\n=== Summary ===")
            pluggy_accounts = accounts.filter(external_id__isnull=False).count()
            active_accounts = accounts.filter(is_active=True).count()
            
            self.stdout.write(f"Total accounts: {accounts.count()}")
            self.stdout.write(f"Pluggy connected: {pluggy_accounts}")
            self.stdout.write(f"Active accounts: {active_accounts}")
            
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"User not found: {email}"))