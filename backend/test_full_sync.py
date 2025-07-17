"""
Force full sync to see transaction data from Pluggy
"""
import os
import sys
import django
import asyncio
from datetime import datetime, timedelta

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from apps.banking.models import BankAccount
from apps.banking.pluggy_sync_service import pluggy_sync_service
import logging

# Enable detailed logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def force_full_sync():
    print("\n=== FORÇANDO SYNC COMPLETA ===\n")
    
    # Get first Pluggy account
    account = BankAccount.objects.filter(
        external_id__isnull=False,
        status='active'
    ).first()
    
    if not account:
        print("❌ No active Pluggy account found!")
        return
    
    print(f"Account: {account.bank_provider.name} - ID: {account.id}")
    print(f"External ID: {account.external_id}")
    
    # Force last_sync_at to None to trigger full sync
    account.last_sync_at = None
    account.save()
    
    print("\nStarting full sync (90 days)...\n")
    
    # Run sync
    result = await pluggy_sync_service.sync_account_transactions(account)
    
    print(f"\n\nFINAL RESULT: {result}")

if __name__ == '__main__':
    asyncio.run(force_full_sync())