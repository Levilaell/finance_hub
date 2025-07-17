#!/usr/bin/env python
"""
Test Pluggy API directly to see transaction data
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
from apps.banking.pluggy_client import PluggyClient
import json


async def test_pluggy_api():
    print("\n=== TESTE DIRETO DA API PLUGGY ===\n")
    
    # Get a Pluggy account
    account = BankAccount.objects.filter(
        external_id__isnull=False,
        status='active'
    ).first()
    
    if not account:
        print("❌ Nenhuma conta Pluggy ativa encontrada!")
        return
    
    print(f"Conta: {account.bank_provider.name} - {account.account_number}")
    print(f"External ID: {account.external_id}\n")
    
    async with PluggyClient() as client:
        try:
            # Get recent transactions
            from_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
            to_date = datetime.now().strftime('%Y-%m-%d')
            
            print(f"Buscando transações de {from_date} até {to_date}\n")
            
            response = await client.get_transactions(
                account.external_id,
                from_date=from_date,
                to_date=to_date,
                page=1,
                page_size=5
            )
            
            print("RESPOSTA COMPLETA DA PLUGGY:")
            print("=" * 60)
            print(json.dumps(response, indent=2, ensure_ascii=False))
            print("=" * 60)
            
            transactions = response.get('results', [])
            
            if transactions:
                print(f"\n\nANÁLISE DE {len(transactions)} TRANSAÇÕES:")
                print("-" * 60)
                
                for i, tx in enumerate(transactions, 1):
                    print(f"\nTransação {i}:")
                    print(f"  ID: {tx.get('id')}")
                    print(f"  Descrição: {tx.get('description')}")
                    print(f"  Valor: R$ {tx.get('amount')}")
                    print(f"  Tipo: {tx.get('type')}")
                    print(f"  Data: {tx.get('date')}")
                    
                    # VERIFICAR SE TEM CATEGORIA
                    category = tx.get('category')
                    print(f"  Categoria: {category if category else '❌ NÃO FORNECIDA'}")
                    
                    # VERIFICAR SE TEM SUBCATEGORIA
                    subcategory = tx.get('subcategory')
                    print(f"  Subcategoria: {subcategory if subcategory else 'Não fornecida'}")
                    
                    # VERIFICAR MERCHANT
                    merchant = tx.get('merchant', {})
                    if merchant:
                        print(f"  Merchant:")
                        print(f"    - Nome: {merchant.get('name', 'N/A')}")
                        print(f"    - MCC: {merchant.get('mcc', 'N/A')}")
                        print(f"    - Categoria MCC: {merchant.get('category', 'N/A')}")
                    
                    # VERIFICAR OUTROS CAMPOS
                    print(f"  Campos disponíveis: {list(tx.keys())}")
                    
            else:
                print("❌ Nenhuma transação encontrada!")
                
        except Exception as e:
            print(f"❌ Erro ao buscar transações: {e}")
            import traceback
            traceback.print_exc()


if __name__ == '__main__':
    asyncio.run(test_pluggy_api())