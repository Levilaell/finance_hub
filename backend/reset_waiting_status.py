#!/usr/bin/env python
"""
Script para resetar contas que ficaram em WAITING_USER_ACTION
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.development')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from apps.banking.models import BankAccount
from django.db.models import Q


def reset_waiting_accounts():
    """Reset accounts in waiting_user_action status"""
    print("🔧 Resetando contas em WAITING_USER_ACTION")
    print("=" * 60)
    
    # Buscar contas com problemas
    # Primeiro verificar quais contas existem
    all_accounts = BankAccount.objects.filter(
        pluggy_item_id__isnull=False
    )
    
    print(f"\n📊 Total de contas Pluggy: {all_accounts.count()}")
    
    # Verificar se o campo sync_status existe
    if all_accounts.exists():
        sample = all_accounts.first()
        print(f"\n🔍 Campos disponíveis na conta de exemplo:")
        print(f"   - status: {sample.status}")
        if hasattr(sample, 'sync_status'):
            print(f"   - sync_status: {sample.sync_status}")
        else:
            print(f"   - sync_status: CAMPO NÃO EXISTE")
    
    # Buscar contas com status 'error' ou que possam estar com problemas
    waiting_accounts = BankAccount.objects.filter(
        Q(status='error') | Q(status='waiting_user_action')
    )
    
    print(f"\n📊 Encontradas {waiting_accounts.count()} contas em WAITING_USER_ACTION")
    
    for account in waiting_accounts:
        print(f"\n🔄 Resetando conta: {account.nickname} (ID: {account.id})")
        print(f"   Item ID: {account.pluggy_item_id}")
        
        # Resetar para active
        account.status = 'active'
        if hasattr(account, 'sync_status'):
            account.sync_status = 'active'
        if hasattr(account, 'sync_error_message'):
            account.sync_error_message = ''
        account.save()
        
        print(f"   ✅ Status resetado para 'active'")
    
    print("\n✨ Concluído!")
    print("\n⚠️  IMPORTANTE:")
    print("   - As contas foram resetadas mas o Item na Pluggy ainda pode estar em WAITING_USER_ACTION")
    print("   - O usuário precisará reconectar a conta se o banco estiver pedindo autenticação")
    print("   - A sincronização manual agora usa janela de 30 dias para evitar forçar update do Item")


if __name__ == "__main__":
    reset_waiting_accounts()