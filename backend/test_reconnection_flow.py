#!/usr/bin/env python
"""
Script para testar o fluxo completo de reconexão
"""
import os
import sys
import django
import asyncio
import json
from datetime import datetime

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.development')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from apps.banking.models import BankAccount
from apps.banking.pluggy_client import PluggyClient


async def test_reconnection_flow(account_id=28):
    """Testa o fluxo completo de reconexão"""
    print("🧪 TESTE DO FLUXO DE RECONEXÃO")
    print("=" * 60)
    
    try:
        account = BankAccount.objects.get(id=account_id)
        print(f"\n📊 Conta: {account.nickname} (ID: {account.id})")
        print(f"   Item ID: {account.pluggy_item_id}")
    except BankAccount.DoesNotExist:
        print(f"❌ Conta {account_id} não encontrada")
        return
    
    async with PluggyClient() as client:
        # 1. Verificar status atual
        print("\n1️⃣ VERIFICANDO STATUS ATUAL DO ITEM")
        print("-" * 40)
        
        item = await client.get_item(account.pluggy_item_id)
        current_status = item.get('status')
        
        print(f"   Status: {current_status}")
        print(f"   Last Updated: {item.get('lastUpdatedAt')}")
        
        if item.get('error'):
            print(f"   Error: {json.dumps(item.get('error'), indent=2)}")
        
        # 2. Verificar necessidade de reconexão
        print("\n2️⃣ VERIFICANDO NECESSIDADE DE RECONEXÃO")
        print("-" * 40)
        
        needs_reconnection = current_status in ['WAITING_USER_ACTION', 'LOGIN_ERROR', 'OUTDATED']
        print(f"   Precisa reconexão? {'SIM' if needs_reconnection else 'NÃO'}")
        
        if needs_reconnection:
            messages = {
                'WAITING_USER_ACTION': 'O banco está solicitando autenticação',
                'LOGIN_ERROR': 'Credenciais inválidas ou expiradas',
                'OUTDATED': 'Conexão desatualizada'
            }
            print(f"   Motivo: {messages.get(current_status, 'Status problemático')}")
        
        # 3. Simular geração de token de reconexão
        print("\n3️⃣ TESTANDO GERAÇÃO DE TOKEN DE RECONEXÃO")
        print("-" * 40)
        
        try:
            token_data = await client.create_connect_token(account.pluggy_item_id)
            print(f"   ✅ Token gerado com sucesso!")
            print(f"   Token: {token_data.get('accessToken')[:50]}...")
            print(f"   Expira em: {token_data.get('expiresAt')}")
            
            # URL para reconexão
            connect_url = "https://connect.pluggy.ai"
            print(f"\n   🔗 URL de reconexão: {connect_url}")
            print(f"   📝 Parâmetros:")
            print(f"      - connectToken: {token_data.get('accessToken')[:30]}...")
            print(f"      - itemId: {account.pluggy_item_id}")
            
        except Exception as e:
            print(f"   ❌ Erro ao gerar token: {e}")
        
        # 4. Instruções para reconexão manual
        print("\n4️⃣ INSTRUÇÕES PARA RECONEXÃO MANUAL")
        print("-" * 40)
        print("   1. Use o token gerado acima no Pluggy Connect")
        print("   2. O usuário fará login no banco")
        print("   3. Após sucesso, o Item voltará ao status UPDATED")
        print("   4. As sincronizações voltarão a funcionar")
        
        # 5. Monitorar webhooks (simulação)
        print("\n5️⃣ WEBHOOKS ESPERADOS")
        print("-" * 40)
        print("   Durante a reconexão, você deve receber:")
        print("   - item/updating - Quando iniciar a atualização")
        print("   - item/updated - Quando completar com sucesso")
        print("   - item/error - Se houver algum erro")
        
    print("\n✅ Teste concluído!")
    print("\n💡 PRÓXIMOS PASSOS:")
    print("   1. Implementar interface no frontend para reconexão")
    print("   2. Integrar com Pluggy Connect Widget")
    print("   3. Processar webhooks de atualização")
    print("   4. Sincronizar transações após reconexão bem-sucedida")


async def test_api_endpoints(account_id=28, base_url="http://localhost:8000"):
    """Testa os novos endpoints da API"""
    print("\n\n🔌 TESTE DOS ENDPOINTS DA API")
    print("=" * 60)
    
    import httpx
    
    # Assumindo que você tem um token de autenticação
    # Ajuste conforme seu sistema de autenticação
    headers = {
        "Authorization": "Bearer YOUR_TOKEN_HERE",
        "Content-Type": "application/json"
    }
    
    async with httpx.AsyncClient() as client:
        # 1. Testar endpoint de status
        print("\n1️⃣ GET /api/banking/pluggy/accounts/{id}/status/")
        print("-" * 40)
        
        try:
            response = await client.get(
                f"{base_url}/api/banking/pluggy/accounts/{account_id}/status/",
                headers=headers
            )
            
            print(f"   Status Code: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"   Response: {json.dumps(data, indent=2, ensure_ascii=False)}")
            else:
                print(f"   Error: {response.text}")
                
        except Exception as e:
            print(f"   ❌ Erro na requisição: {e}")
        
        # 2. Testar endpoint de reconexão
        print("\n2️⃣ POST /api/banking/pluggy/accounts/{id}/reconnect/")
        print("-" * 40)
        
        try:
            response = await client.post(
                f"{base_url}/api/banking/pluggy/accounts/{account_id}/reconnect/",
                headers=headers
            )
            
            print(f"   Status Code: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"   Response: {json.dumps(data, indent=2, ensure_ascii=False)}")
            else:
                print(f"   Error: {response.text}")
                
        except Exception as e:
            print(f"   ❌ Erro na requisição: {e}")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Testar fluxo de reconexão')
    parser.add_argument('--account-id', type=int, default=28, help='ID da conta')
    parser.add_argument('--test-api', action='store_true', help='Testar endpoints da API')
    args = parser.parse_args()
    
    # Executar testes
    asyncio.run(test_reconnection_flow(args.account_id))
    
    if args.test_api:
        asyncio.run(test_api_endpoints(args.account_id))