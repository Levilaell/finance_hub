"""
Force resync of account to see category data
"""
import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from apps.banking.models import BankAccount
from django.core.management import call_command

def force_resync():
    # Get account
    account = BankAccount.objects.filter(
        external_id__isnull=False,
        status='active'
    ).first()
    
    if not account:
        print("No active Pluggy account!")
        return
    
    print(f"Account: {account.bank_provider.name} (ID: {account.id})")
    
    # Clear last sync to force full sync
    account.last_sync_at = None
    account.save()
    
    print("Forcing full resync...")
    
    # Call sync command
    call_command('sync_pluggy_debug', account_id=account.id)

if __name__ == '__main__':
    force_resync()