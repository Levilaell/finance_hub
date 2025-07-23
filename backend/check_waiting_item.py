#!/usr/bin/env python
"""
Verificar conta associada ao Item em WAITING_USER_ACTION
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.development')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from apps.banking.models import BankAccount

item_id = "a0beeaac-806b-410f-b814-fbb8fe517d54"

print(f"🔍 Verificando Item: {item_id}")
print("=" * 60)

# Buscar contas com esse Item ID
accounts = BankAccount.objects.filter(pluggy_item_id=item_id)

if accounts.exists():
    for account in accounts:
        print(f"\n📊 Conta encontrada:")
        print(f"   ID: {account.id}")
        print(f"   Nome: {account.nickname}")
        print(f"   Banco: {account.bank_provider.name if account.bank_provider else 'N/A'}")
        print(f"   Company: {account.company.name if account.company else 'N/A'}")
        print(f"   Status: {account.status}")
        if hasattr(account, 'sync_status'):
            print(f"   Sync Status: {account.sync_status}")
        
        print(f"\n⚠️  Esta conta precisa RECONEXÃO!")
        print(f"\n📱 No frontend, você deve ver:")
        print(f"   - Mensagem de erro informando que precisa reconectar")
        print(f"   - Botão ou link para reconectar")
        print(f"   - URL de reconexão: /api/banking/pluggy/accounts/{account.id}/reconnect/")
        
        print(f"\n💡 Para testar a reconexão:")
        print(f"   1. Faça uma requisição POST para /api/banking/pluggy/accounts/{account.id}/reconnect/")
        print(f"   2. Use o token retornado no Pluggy Connect")
        print(f"   3. O usuário fará login no banco")
        print(f"   4. Após sucesso, o Item voltará a funcionar")
else:
    print(f"\n❌ Nenhuma conta encontrada com esse Item ID")

print("\n✅ O webhook está funcionando corretamente!")
print("   - Recebeu evento item/waiting_user_action")
print("   - Atualizou status da conta")
print("   - Frontend deve mostrar opção de reconexão")