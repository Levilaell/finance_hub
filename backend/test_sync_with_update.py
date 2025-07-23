#!/usr/bin/env python
"""
Script para testar sincronização COM e SEM forçar update do Item
"""
import os
import sys
import django
import asyncio
from datetime import datetime, timedelta
from django.utils import timezone

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.development')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from apps.banking.models import BankAccount, Transaction
from apps.banking.pluggy_sync_service import pluggy_sync_service
from apps.banking.pluggy_client import PluggyClient


async def test_sync_comparison(account_id=None):
    """Compara sincronização com e sem force update"""
    print("🔬 TESTE DE SINCRONIZAÇÃO COM/SEM FORCE UPDATE")
    print("=" * 60)
    
    # Pegar uma conta específica ou a primeira conta ativa
    if account_id:
        account = BankAccount.objects.get(id=account_id)
    else:
        account = BankAccount.objects.filter(
            status='active',
            external_id__isnull=False,
            pluggy_item_id__isnull=False
        ).first()
    
    if not account:
        print("❌ Nenhuma conta Pluggy ativa encontrada")
        return
    
    print(f"\n📊 Conta: {account.nickname} (ID: {account.id})")
    print(f"   External ID: {account.external_id}")
    print(f"   Item ID: {account.pluggy_item_id}")
    print(f"   Last Sync: {account.last_sync_at}")
    
    # Contar transações antes
    tx_count_before = Transaction.objects.filter(bank_account=account).count()
    print(f"\n📈 Transações no banco ANTES: {tx_count_before}")
    
    # TESTE 1: Sincronização SEM force update (como está hoje)
    print("\n🔍 TESTE 1: Sincronização SEM force update")
    print("   (Este é o comportamento atual)")
    
    result_without_update = await pluggy_sync_service.sync_account_transactions(account)
    
    print(f"   Status: {result_without_update.get('status')}")
    print(f"   Novas transações: {result_without_update.get('transactions', 0)}")
    
    tx_count_after_without = Transaction.objects.filter(bank_account=account).count()
    print(f"   Total no banco agora: {tx_count_after_without}")
    
    # Aguardar um pouco
    await asyncio.sleep(2)
    
    # TESTE 2: Sincronização COM force update (proposta de correção)
    print("\n🔍 TESTE 2: Sincronização COM force update")
    print("   (Este é o comportamento proposto)")
    
    # Primeiro, forçar update do item
    if account.pluggy_item_id:
        print(f"   🔄 Forçando update do Item {account.pluggy_item_id}...")
        update_result = await pluggy_sync_service.force_item_update(account.pluggy_item_id)
        print(f"   Update result: {update_result}")
        
        if update_result.get('success'):
            # Aguardar um pouco para a Pluggy processar
            print("   ⏳ Aguardando 5 segundos para Pluggy processar...")
            await asyncio.sleep(5)
            
            # Agora sincronizar
            result_with_update = await pluggy_sync_service.sync_account_transactions(account)
            
            print(f"   Status: {result_with_update.get('status')}")
            print(f"   Novas transações: {result_with_update.get('transactions', 0)}")
            
            tx_count_after_with = Transaction.objects.filter(bank_account=account).count()
            print(f"   Total no banco agora: {tx_count_after_with}")
        else:
            print(f"   ❌ Falha ao forçar update: {update_result}")
    
    # Análise final
    print("\n💡 ANÁLISE:")
    print(f"   Transações antes do teste: {tx_count_before}")
    print(f"   Transações após sync SEM update: {tx_count_after_without}")
    print(f"   Diferença: +{tx_count_after_without - tx_count_before}")
    
    if 'tx_count_after_with' in locals():
        print(f"   Transações após sync COM update: {tx_count_after_with}")
        print(f"   Diferença adicional com update: +{tx_count_after_with - tx_count_after_without}")
    
    # Verificar status do Item
    print("\n📋 STATUS DO ITEM:")
    async with PluggyClient() as client:
        item = await client.get_item(account.pluggy_item_id)
        print(f"   Status atual: {item.get('status')}")
        print(f"   Last Updated: {item.get('lastUpdatedAt')}")
        
        # Verificar execution status se disponível
        if 'executionStatus' in item:
            print(f"   Execution Status: {item.get('executionStatus')}")


async def main():
    import argparse
    parser = argparse.ArgumentParser(description='Testar sync com e sem force update')
    parser.add_argument('--account-id', type=int, help='ID da conta para testar')
    args = parser.parse_args()
    
    await test_sync_comparison(args.account_id)


if __name__ == "__main__":
    asyncio.run(main())