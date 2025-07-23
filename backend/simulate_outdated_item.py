#!/usr/bin/env python
"""
Simular um Item OUTDATED para teste
"""
import os
import sys
import django
import asyncio

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.development')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from apps.banking.models import BankAccount
from apps.banking.pluggy_client import PluggyClient


async def check_item_status(item_id):
    """Verificar status atual do Item"""
    async with PluggyClient() as client:
        item = await client.get_item(item_id)
        return item


def main():
    print("🔍 VERIFICANDO STATUS DOS ITEMS PLUGGY")
    print("=" * 60)
    
    # Pegar todas as contas Pluggy
    accounts = BankAccount.objects.filter(
        pluggy_item_id__isnull=False
    ).select_related('bank_provider')
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    for account in accounts:
        print(f"\n📊 Conta: {account.nickname} (ID: {account.id})")
        print(f"   Banco: {account.bank_provider.name if account.bank_provider else 'N/A'}")
        print(f"   Item ID: {account.pluggy_item_id}")
        
        try:
            item_data = loop.run_until_complete(check_item_status(account.pluggy_item_id))
            status = item_data.get('status')
            last_updated = item_data.get('lastUpdatedAt')
            
            print(f"   Status: {status}")
            print(f"   Last Updated: {last_updated}")
            
            # Verificar se precisa reconexão
            needs_reconnection = status in ['WAITING_USER_ACTION', 'LOGIN_ERROR', 'OUTDATED']
            
            if needs_reconnection:
                print(f"   ⚠️  PRECISA RECONEXÃO!")
                
                # Sugerir teste
                print(f"\n   💡 Para testar a reconexão com esta conta:")
                print(f"      1. Use o endpoint: GET /api/banking/pluggy/accounts/{account.id}/status/")
                print(f"      2. Deve retornar needs_reconnection: true")
                print(f"      3. Use o endpoint: POST /api/banking/pluggy/accounts/{account.id}/reconnect/")
                print(f"      4. Use o token retornado no Pluggy Connect")
            else:
                print(f"   ✅ Status OK")
                
                # Se estiver UPDATED, mostrar quando podemos forçar para OUTDATED
                if status == 'UPDATED':
                    print(f"\n   📝 NOTA: Para testar reconexão, você pode:")
                    print(f"      1. Esperar o Item ficar OUTDATED naturalmente")
                    print(f"      2. Tentar forçar update repetidamente até o banco pedir autenticação")
                    print(f"      3. Mudar a senha no banco (vai gerar LOGIN_ERROR)")
                
        except Exception as e:
            print(f"   ❌ Erro ao verificar: {e}")
    
    loop.close()
    
    print("\n" + "=" * 60)
    print("💡 DICA: Items ficam OUTDATED quando:")
    print("   - Não são atualizados há muito tempo")
    print("   - O banco muda políticas de segurança")
    print("   - A sessão expira")


if __name__ == "__main__":
    main()