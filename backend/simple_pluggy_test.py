#!/usr/bin/env python
"""
Simple synchronous test of Pluggy data
"""
import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from apps.banking.models import BankAccount, Transaction
import requests
from django.conf import settings
import json

def test_pluggy():
    print("\n=== TESTE SIMPLES PLUGGY ===\n")
    
    # 1. Check if we have Pluggy configuration
    print("1. Configuração Pluggy:")
    print(f"   PLUGGY_CLIENT_ID: {'✓' if getattr(settings, 'PLUGGY_CLIENT_ID', None) else '✗'}")
    print(f"   PLUGGY_CLIENT_SECRET: {'✓' if getattr(settings, 'PLUGGY_CLIENT_SECRET', None) else '✗'}")
    print(f"   PLUGGY_USE_SANDBOX: {getattr(settings, 'PLUGGY_USE_SANDBOX', False)}\n")
    
    # 2. Check Pluggy accounts
    print("2. Contas Pluggy no banco:")
    pluggy_accounts = BankAccount.objects.filter(external_id__isnull=False)
    print(f"   Total de contas com external_id: {pluggy_accounts.count()}")
    
    if pluggy_accounts.exists():
        account = pluggy_accounts.first()
        print(f"   Primeira conta: {account.bank_provider.name}")
        print(f"   External ID: {account.external_id}\n")
        
        # 3. Check transactions for this account
        print("3. Transações desta conta:")
        transactions = Transaction.objects.filter(
            bank_account=account
        ).order_by('-transaction_date')[:5]
        
        for tx in transactions:
            cat_info = f"Categoria: {tx.category.name}" if tx.category else "SEM CATEGORIA"
            print(f"   - {tx.description[:40]} | {cat_info}")
            
        # 4. Check all transaction fields
        if transactions:
            print("\n4. Campos de uma transação:")
            tx = transactions.first()
            print(f"   - external_id: {tx.external_id}")
            print(f"   - category: {tx.category}")
            print(f"   - is_ai_categorized: {tx.is_ai_categorized}")
            print(f"   - ai_category_confidence: {tx.ai_category_confidence}")
            print(f"   - ai_suggested_category: {tx.ai_suggested_category}")

if __name__ == '__main__':
    test_pluggy()