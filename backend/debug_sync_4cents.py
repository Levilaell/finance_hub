#!/usr/bin/env python
import os
import sys
import django
from datetime import datetime, timedelta
import asyncio

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from apps.banking.models import BankAccount, Transaction
from apps.banking.pluggy_sync_service import pluggy_sync_service
from apps.banking.pluggy_client import PluggyClient
from decimal import Decimal

async def debug_sync():
    # Buscar conta em produção
    # Primeiro buscar a company do usuário
    from apps.companies.models import Company
    company = Company.objects.filter(owner__email='levilaelsilvaa@gmail.com').first()
    
    if not company:
        print("❌ Company não encontrada para o usuário")
        return
    
    account = BankAccount.objects.filter(
        company=company,
        is_active=True,
        external_id__isnull=False
    ).first()
    
    if not account:
        print("❌ Conta não encontrada")
        return
    
    print(f"✅ Conta encontrada: {account}")
    print(f"   - ID: {account.id}")
    print(f"   - External ID: {account.external_id}")
    print(f"   - Last sync: {account.last_sync_at}")
    print(f"   - Banco: {account.bank_provider.name if account.bank_provider else 'N/A'}")
    
    # Verificar janela de sincronização
    if account.last_sync_at:
        hours_since = (datetime.now() - account.last_sync_at.replace(tzinfo=None)).total_seconds() / 3600
        print(f"\n⏰ Última sync há {hours_since:.1f} horas")
        
        if hours_since < 24:
            print("   → Será usado período de 2 dias para sync")
        else:
            print("   → Será usado período de 3-7 dias para sync")
    
    # Buscar diretamente da API da Pluggy
    print("\n📡 Buscando transações diretamente da API Pluggy...")
    
    try:
        async with PluggyClient() as client:
            # Buscar últimas transações
            from_date = (datetime.now() - timedelta(days=2)).date()
            to_date = (datetime.now() + timedelta(days=1)).date()
            
            print(f"   - Período: {from_date} até {to_date}")
            
            response = await client.get_transactions(
                account.external_id,
                from_date=from_date.isoformat(),
                to_date=to_date.isoformat(),
                page=1,
                page_size=50
            )
            
            transactions = response.get('results', [])
            print(f"\n📊 Total de transações encontradas: {len(transactions)}")
            
            # Filtrar transações de centavos
            cent_transactions = []
            for tx in transactions:
                amount = Decimal(str(tx.get('amount', '0')))
                if abs(amount) < Decimal('0.10'):  # Menos de 10 centavos
                    cent_transactions.append(tx)
            
            if cent_transactions:
                print(f"\n💰 Transações de centavos encontradas: {len(cent_transactions)}")
                for tx in cent_transactions:
                    print(f"\n   📌 Transação:")
                    print(f"      - ID: {tx.get('id')}")
                    print(f"      - Data: {tx.get('date')}")
                    print(f"      - Valor: R$ {tx.get('amount')}")
                    print(f"      - Tipo: {tx.get('type')}")
                    print(f"      - Descrição: {tx.get('description')}")
                    print(f"      - Status: {tx.get('status')}")
                    
                    # Verificar se já existe no banco
                    exists = Transaction.objects.filter(
                        bank_account=account,
                        external_id=str(tx.get('id'))
                    ).exists()
                    
                    if exists:
                        print(f"      ✅ Já existe no banco local")
                    else:
                        print(f"      ❌ NÃO existe no banco local")
            else:
                print("\n⚠️ Nenhuma transação de centavos encontrada no período")
                
            # Mostrar últimas 5 transações para contexto
            print("\n📋 Últimas 5 transações (qualquer valor):")
            for i, tx in enumerate(transactions[:5]):
                print(f"\n   {i+1}. {tx.get('description', 'Sem descrição')}")
                print(f"      - Data: {tx.get('date')}")
                print(f"      - Valor: R$ {tx.get('amount')}")
                print(f"      - Tipo: {tx.get('type')}")
                
    except Exception as e:
        print(f"\n❌ Erro ao buscar da API: {e}")
        import traceback
        traceback.print_exc()
    
    # Executar sync
    print("\n\n🔄 Executando sincronização...")
    try:
        result = await pluggy_sync_service.sync_account_transactions(account)
        print(f"\n✅ Sincronização concluída:")
        print(f"   - Status: {result.get('status')}")
        print(f"   - Transações novas: {result.get('transactions', 0)}")
    except Exception as e:
        print(f"\n❌ Erro na sincronização: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🔍 Debug de sincronização - Transação de 4 centavos")
    print("=" * 60)
    asyncio.run(debug_sync())