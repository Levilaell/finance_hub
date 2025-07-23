#!/usr/bin/env python
"""
Script para testar diretamente a API da Pluggy e verificar se as transações estão disponíveis
"""
import os
import sys
import django
import asyncio
from datetime import datetime, timedelta
from django.utils import timezone
import json

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.development')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from apps.banking.models import BankAccount, Transaction
from apps.banking.pluggy_client import PluggyClient


async def test_pluggy_transactions(account_id=None):
    """Testa diretamente a API da Pluggy para verificar transações"""
    print("🔍 TESTE DIRETO DA API PLUGGY")
    print("=" * 60)
    
    # Pegar uma conta específica ou a primeira conta ativa
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
    print(f"   Last Sync: {account.last_sync_at}")
    
    # Testar diferentes janelas de tempo
    async with PluggyClient() as client:
        # 1. Buscar transações dos últimos 30 dias
        print("\n🔍 TESTE 1: Últimos 30 dias")
        from_date = (timezone.now() - timedelta(days=30)).date()
        to_date = (timezone.now() + timedelta(days=1)).date()
        
        print(f"   From: {from_date}")
        print(f"   To: {to_date}")
        
        response = await client.get_transactions(
            account.external_id,
            from_date=from_date.isoformat(),
            to_date=to_date.isoformat(),
            page=1,
            page_size=100
        )
        
        transactions_30d = response.get('results', [])
        print(f"   Total encontrado: {len(transactions_30d)} transações")
        
        # 2. Buscar transações dos últimos 7 dias
        print("\n🔍 TESTE 2: Últimos 7 dias")
        from_date_7d = (timezone.now() - timedelta(days=7)).date()
        
        print(f"   From: {from_date_7d}")
        print(f"   To: {to_date}")
        
        response_7d = await client.get_transactions(
            account.external_id,
            from_date=from_date_7d.isoformat(),
            to_date=to_date.isoformat(),
            page=1,
            page_size=100
        )
        
        transactions_7d = response_7d.get('results', [])
        print(f"   Total encontrado: {len(transactions_7d)} transações")
        
        # 3. Buscar transações de hoje
        print("\n🔍 TESTE 3: Hoje")
        from_date_today = timezone.now().date()
        
        print(f"   From: {from_date_today}")
        print(f"   To: {to_date}")
        
        response_today = await client.get_transactions(
            account.external_id,
            from_date=from_date_today.isoformat(),
            to_date=to_date.isoformat(),
            page=1,
            page_size=100
        )
        
        transactions_today = response_today.get('results', [])
        print(f"   Total encontrado: {len(transactions_today)} transações")
        
        # Mostrar transações mais recentes
        print("\n📈 TRANSAÇÕES MAIS RECENTES DA API:")
        all_transactions = sorted(transactions_30d, key=lambda x: x.get('date', ''), reverse=True)[:10]
        
        for tx in all_transactions:
            tx_date = tx.get('date', 'no date')
            tx_desc = tx.get('description', 'no description')[:50]
            tx_amount = tx.get('amount', 0)
            tx_id = tx.get('id')
            print(f"   {tx_date} | ID: {tx_id} | {tx_desc} | R$ {tx_amount}")
        
        # Verificar se essas transações existem no banco
        print("\n🔍 VERIFICANDO SE TRANSAÇÕES EXISTEM NO BANCO:")
        for tx in all_transactions[:5]:
            tx_id = tx.get('id')
            exists = Transaction.objects.filter(
                bank_account=account,
                external_id=str(tx_id)
            ).exists()
            status = "✅ Existe" if exists else "❌ NÃO existe"
            print(f"   ID {tx_id}: {status}")
        
        # Verificar transações no banco que não vieram da API
        print("\n🔍 TRANSAÇÕES NO BANCO (últimas 10):")
        db_transactions = Transaction.objects.filter(
            bank_account=account
        ).order_by('-transaction_date')[:10]
        
        api_ids = {tx.get('id') for tx in transactions_30d}
        
        for db_tx in db_transactions:
            in_api = db_tx.external_id in api_ids
            status = "✅ Na API" if in_api else "❌ NÃO está na API"
            print(f"   {db_tx.transaction_date} | ID: {db_tx.external_id} | {status}")
        
        # Análise final
        print("\n💡 ANÁLISE:")
        print(f"   Total de transações na API (30 dias): {len(transactions_30d)}")
        print(f"   Total de transações no banco (30 dias): {Transaction.objects.filter(bank_account=account, transaction_date__gte=(timezone.now() - timedelta(days=30)).date()).count()}")
        
        # Verificar se há problema com o formato de data
        if transactions_30d:
            print("\n📅 FORMATO DE DATAS NA API:")
            sample_tx = transactions_30d[0]
            print(f"   Exemplo de data: {sample_tx.get('date')}")
            print(f"   Estrutura completa de uma transação:")
            print(json.dumps(sample_tx, indent=2, ensure_ascii=False))


async def main():
    import argparse
    parser = argparse.ArgumentParser(description='Testar API Pluggy diretamente')
    parser.add_argument('--account-id', type=int, help='ID da conta para testar')
    args = parser.parse_args()
    
    await test_pluggy_transactions(args.account_id)


if __name__ == "__main__":
    asyncio.run(main())