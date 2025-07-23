#!/usr/bin/env python
"""
Script para verificar se há transações pendentes via webhook
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
from apps.banking.pluggy_client import PluggyClient


async def check_pending_webhooks(account_id=None):
    """Verifica se há transações pendentes que poderiam vir via webhook"""
    print("🔍 VERIFICANDO TRANSAÇÕES PENDENTES")
    print("=" * 60)
    
    # Pegar uma conta específica
    if account_id:
        account = BankAccount.objects.get(id=account_id)
    else:
        account = BankAccount.objects.filter(
            status='active',
            external_id__isnull=False
        ).first()
    
    if not account:
        print("❌ Nenhuma conta Pluggy ativa encontrada")
        return
    
    print(f"\n📊 Conta: {account.nickname} (ID: {account.id})")
    print(f"   External ID: {account.external_id}")
    print(f"   Item ID: {account.pluggy_item_id}")
    
    async with PluggyClient() as client:
        # Verificar status do Item
        if account.pluggy_item_id:
            item = await client.get_item(account.pluggy_item_id)
            print(f"\n📋 Status do Item:")
            print(f"   Status: {item.get('status')}")
            print(f"   Last Updated: {item.get('lastUpdatedAt')}")
            print(f"   Connector: {item.get('connector', {}).get('name')}")
            
            # Verificar execution details
            execution = item.get('executionStatus')
            if execution:
                print(f"\n🔧 Execution Status: {execution}")
            
            error = item.get('error')
            if error:
                print(f"\n❌ Error: {error}")
        
        # Buscar transações recentes para debug
        print("\n🔍 Buscando transações dos últimos 3 dias na API...")
        from_date = (timezone.now() - timedelta(days=3)).date()
        to_date = (timezone.now() + timedelta(days=1)).date()
        
        response = await client.get_transactions(
            account.external_id,
            from_date=from_date.isoformat(),
            to_date=to_date.isoformat(),
            page=1,
            page_size=10
        )
        
        api_transactions = response.get('results', [])
        print(f"\n📊 Transações encontradas na API: {len(api_transactions)}")
        
        # Mostrar últimas transações
        for tx in api_transactions[:5]:
            tx_id = tx.get('id')
            tx_date = tx.get('date')
            tx_amount = tx.get('amount')
            tx_desc = tx.get('description', '')[:40]
            
            # Verificar se existe no banco
            exists = Transaction.objects.filter(
                bank_account=account,
                external_id=str(tx_id)
            ).exists()
            
            status = "✅ Sincronizada" if exists else "❌ NÃO sincronizada"
            print(f"\n   {tx_date} | R$ {tx_amount}")
            print(f"   {tx_desc}")
            print(f"   ID: {tx_id}")
            print(f"   Status: {status}")
    
    print("\n💡 CONCLUSÃO:")
    print("   - Se há transações NÃO sincronizadas, elas estão na API mas não no banco")
    print("   - O problema é que o Item está OUTDATED e não conseguimos atualizar")
    print("   - A solução é o usuário reconectar a conta manualmente")


async def main():
    import argparse
    parser = argparse.ArgumentParser(description='Verificar transações pendentes')
    parser.add_argument('--account-id', type=int, help='ID da conta para verificar')
    args = parser.parse_args()
    
    await check_pending_webhooks(args.account_id)


if __name__ == "__main__":
    asyncio.run(main())