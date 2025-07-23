#!/usr/bin/env python
"""
Script para testar sincronização forçada ignorando duplicatas
"""
import os
import sys
import django
import asyncio
from datetime import datetime, timedelta
from django.utils import timezone
from decimal import Decimal

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.development')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from apps.banking.models import BankAccount, Transaction, TransactionCategory
from apps.banking.pluggy_client import PluggyClient
from django.db import transaction


async def force_sync_recent_transactions(account_id=28):
    """Força sincronização das transações mais recentes"""
    print("🔧 SINCRONIZAÇÃO FORÇADA DE TRANSAÇÕES RECENTES")
    print("=" * 60)
    
    account = BankAccount.objects.get(id=account_id)
    print(f"\n📊 Conta: {account.nickname} (ID: {account.id})")
    
    async with PluggyClient() as client:
        # Buscar apenas transações de hoje e ontem
        from_date = (timezone.now() - timedelta(days=2)).date()
        to_date = (timezone.now() + timedelta(days=1)).date()
        
        print(f"\n🔍 Buscando transações de {from_date} até {to_date}")
        
        response = await client.get_transactions(
            account.external_id,
            from_date=from_date.isoformat(),
            to_date=to_date.isoformat(),
            page=1,
            page_size=50
        )
        
        api_transactions = response.get('results', [])
        print(f"\n📊 Total de transações encontradas: {len(api_transactions)}")
        
        # Filtrar apenas transações de hoje
        today = timezone.now().date()
        today_transactions = [
            tx for tx in api_transactions 
            if tx.get('date', '').startswith(str(today))
        ]
        
        print(f"\n📅 Transações de hoje ({today}): {len(today_transactions)}")
        
        if today_transactions:
            print("\n🆕 TRANSAÇÕES DE HOJE:")
            for tx in today_transactions:
                tx_id = tx.get('id')
                tx_date = tx.get('date')
                tx_amount = tx.get('amount')
                tx_desc = tx.get('description', '')
                
                exists = Transaction.objects.filter(
                    bank_account=account,
                    external_id=str(tx_id)
                ).exists()
                
                print(f"\n   ID: {tx_id}")
                print(f"   Data: {tx_date}")
                print(f"   Valor: R$ {tx_amount}")
                print(f"   Descrição: {tx_desc}")
                print(f"   Já existe? {'SIM' if exists else 'NÃO'}")
                
                if not exists:
                    print(f"   ➡️ Esta transação DEVERIA ser sincronizada!")
        
        # Mostrar últimas transações no banco
        print("\n📊 ÚLTIMAS TRANSAÇÕES NO BANCO:")
        db_transactions = Transaction.objects.filter(
            bank_account=account
        ).order_by('-transaction_date')[:5]
        
        for tx in db_transactions:
            print(f"\n   Data: {tx.transaction_date}")
            print(f"   Valor: R$ {tx.amount}")
            print(f"   Descrição: {tx.description}")
            print(f"   ID Externo: {tx.external_id}")
    
    print("\n💡 DIAGNÓSTICO:")
    if len(today_transactions) > 0:
        exists_count = sum(1 for tx in today_transactions if Transaction.objects.filter(
            bank_account=account, external_id=str(tx.get('id'))).exists())
        new_count = len(today_transactions) - exists_count
        
        if new_count > 0:
            print(f"   ❌ Há {new_count} transações novas que não foram sincronizadas!")
            print(f"   ⚠️  O problema é que o Item está OUTDATED")
            print(f"   🔄 A Pluggy TEM as transações mas não conseguimos sincronizar")
            print(f"   👤 Solução: O usuário precisa reconectar a conta")
        else:
            print(f"   ✅ Todas as transações de hoje já foram sincronizadas")
    else:
        print(f"   ℹ️  Nenhuma transação encontrada para hoje")
        print(f"   📝 Isso pode significar:")
        print(f"      1. Realmente não há transações hoje")
        print(f"      2. A Pluggy não atualizou os dados (Item OUTDATED)")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Forçar sync de transações recentes')
    parser.add_argument('--account-id', type=int, default=28, help='ID da conta')
    args = parser.parse_args()
    
    asyncio.run(force_sync_recent_transactions(args.account_id))