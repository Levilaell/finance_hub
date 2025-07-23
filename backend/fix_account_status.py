#!/usr/bin/env python
"""
Script simplificado para resetar status de contas
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.development')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from apps.banking.models import BankAccount
from django.db import connection


def fix_account_status(account_id=28):
    """Reset specific account status"""
    print("🔧 Resetando status da conta")
    print("=" * 60)
    
    # Verificar campos existentes na tabela
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'bank_accounts'
            ORDER BY ordinal_position
        """)
        columns = [row[0] for row in cursor.fetchall()]
        print(f"\n📋 Campos existentes na tabela bank_accounts:")
        for col in columns:
            if 'status' in col or 'sync' in col:
                print(f"   - {col}")
    
    try:
        account = BankAccount.objects.only('id', 'nickname', 'status').get(id=account_id)
        print(f"\n📊 Conta encontrada:")
        print(f"   ID: {account.id}")
        print(f"   Nome: {account.nickname}")
        print(f"   Status atual: {account.status}")
        
        # Resetar status
        if account.status in ['error', 'waiting_user_action']:
            account.status = 'active'
            account.save(update_fields=['status'])
            print(f"\n✅ Status alterado para 'active'")
        else:
            print(f"\n✨ Status já está OK: {account.status}")
            
    except BankAccount.DoesNotExist:
        print(f"\n❌ Conta {account_id} não encontrada")
    except Exception as e:
        print(f"\n❌ Erro: {e}")
    
    print("\n⚠️  NOTA:")
    print("   - Se o Item na Pluggy estiver em WAITING_USER_ACTION,")
    print("   - o usuário precisará reconectar a conta.")
    print("   - A sincronização agora usa janela de 30 dias para evitar esse problema.")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Resetar status de conta')
    parser.add_argument('--account-id', type=int, default=28, help='ID da conta para resetar')
    args = parser.parse_args()
    
    fix_account_status(args.account_id)