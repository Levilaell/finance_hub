#!/usr/bin/env python
"""
Listar contas Pluggy e seus status
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.development')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from apps.banking.models import BankAccount

print("🏦 CONTAS PLUGGY DISPONÍVEIS")
print("=" * 60)

accounts = BankAccount.objects.filter(
    pluggy_item_id__isnull=False
).select_related('bank_provider', 'company')

for account in accounts:
    print(f"\n📊 ID: {account.id}")
    print(f"   Nome: {account.nickname}")
    print(f"   Banco: {account.bank_provider.name if account.bank_provider else 'N/A'}")
    print(f"   Company: {account.company.name if account.company else 'N/A'}")
    print(f"   Item ID: {account.pluggy_item_id}")
    print(f"   External ID: {account.external_id}")
    print(f"   Status: {account.status}")
    if hasattr(account, 'sync_status'):
        print(f"   Sync Status: {account.sync_status}")
    print(f"   Last Sync: {account.last_sync_at}")

if not accounts:
    print("\n❌ Nenhuma conta Pluggy encontrada")
else:
    print(f"\n📊 Total: {accounts.count()} contas Pluggy")