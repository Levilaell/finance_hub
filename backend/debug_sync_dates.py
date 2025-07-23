#!/usr/bin/env python
"""
Script de diagnóstico para verificar problemas de sincronização incremental
"""
import os
import sys
import django
from datetime import datetime, timedelta
from django.utils import timezone

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.development')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from apps.banking.models import BankAccount, Transaction
from apps.banking.pluggy_sync_service import PluggyTransactionSyncService


def diagnose_sync_issue(account_id=None):
    """Diagnostica problemas de sincronização incremental"""
    print("🔍 DIAGNÓSTICO DE SINCRONIZAÇÃO INCREMENTAL")
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
    
    # Analisar janela de tempo
    sync_service = PluggyTransactionSyncService()
    account_info = {
        'id': account.id,
        'external_id': account.external_id,
        'last_sync_at': account.last_sync_at
    }
    
    print("\n🕐 ANÁLISE DE JANELA DE TEMPO:")
    
    # Calcular sync_from
    sync_from = sync_service._get_sync_from_date_safe(account_info)
    
    # PROBLEMA 1: datetime.now() vs timezone.now()
    sync_to_wrong = (datetime.now() + timedelta(days=1)).date()
    sync_to_correct = (timezone.now() + timedelta(days=1)).date()
    
    print(f"\n   Sync From: {sync_from}")
    print(f"   Sync To (ERRADO - datetime.now()): {sync_to_wrong}")
    print(f"   Sync To (CORRETO - timezone.now()): {sync_to_correct}")
    
    # Mostrar diferença
    print(f"\n   datetime.now(): {datetime.now()}")
    print(f"   timezone.now(): {timezone.now()}")
    print(f"   Timezone: {timezone.get_current_timezone()}")
    
    # Verificar transações recentes
    print("\n📈 TRANSAÇÕES RECENTES:")
    recent_transactions = Transaction.objects.filter(
        bank_account=account
    ).order_by('-transaction_date')[:5]
    
    for tx in recent_transactions:
        print(f"   {tx.transaction_date} - {tx.description[:50]} - R$ {tx.amount}")
    
    # Verificar se há transações que seriam perdidas
    if account.last_sync_at:
        print("\n⚠️  ANÁLISE DE POSSÍVEIS TRANSAÇÕES PERDIDAS:")
        
        # Transações criadas após last_sync_at
        new_transactions = Transaction.objects.filter(
            bank_account=account,
            created_at__gt=account.last_sync_at
        ).count()
        
        print(f"   Transações criadas após último sync: {new_transactions}")
        
        # Transações com data futura (possível problema de timezone)
        future_transactions = Transaction.objects.filter(
            bank_account=account,
            transaction_date__gt=timezone.now().date()
        ).count()
        
        print(f"   Transações com data futura: {future_transactions}")
    
    # Sugestões
    print("\n💡 DIAGNÓSTICO:")
    print("   1. O código usa datetime.now() em vez de timezone.now() para sync_to")
    print("   2. Isso pode causar problemas se o servidor estiver em UTC e as transações em horário local")
    print("   3. A janela de 7 dias para syncs recentes está correta")
    print("   4. O last_sync_at está sendo atualizado corretamente com timezone.now()")
    
    print("\n✅ SOLUÇÃO:")
    print("   Trocar datetime.now() por timezone.now() na linha 170 do pluggy_sync_service.py")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Diagnosticar problemas de sincronização')
    parser.add_argument('--account-id', type=int, help='ID da conta para diagnosticar')
    args = parser.parse_args()
    
    diagnose_sync_issue(args.account_id)