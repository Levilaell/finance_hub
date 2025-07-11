#!/usr/bin/env python
"""
Script para testar credenciais do Pluggy
"""
import os
import sys
import django
import asyncio

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from apps.banking.pluggy_client import PluggyClient


async def test_pluggy():
    """Testa conexão com Pluggy"""
    try:
        print("🔌 Testando conexão com Pluggy...")
        print("-" * 50)
        
        async with PluggyClient() as client:
            # Testa autenticação
            print("✅ Autenticação bem-sucedida!")
            
            # Lista alguns bancos disponíveis
            print("\n📊 Buscando bancos disponíveis...")
            connectors = await client.get_connectors()
            
            print(f"\n✅ {len(connectors)} bancos encontrados!")
            print("\nPrimeiros 5 bancos disponíveis:")
            print("-" * 50)
            
            for i, connector in enumerate(connectors[:5]):
                if connector.get('type') == 'PERSONAL_BANK':
                    print(f"{i+1}. {connector['name']} (ID: {connector['id']})")
                    print(f"   Status: {connector.get('health', {}).get('status', 'ONLINE')}")
            
            print("\n✅ Suas credenciais Pluggy estão funcionando corretamente!")
            print("🎉 Você pode conectar contas bancárias reais!")
            
    except Exception as e:
        print(f"\n❌ Erro ao conectar com Pluggy: {e}")
        print("\nVerifique:")
        print("1. Se as credenciais estão corretas no .env")
        print("2. Se são credenciais do ambiente Sandbox")
        print("3. Se você tem conexão com a internet")


if __name__ == "__main__":
    print("🚀 CaixaHub - Teste de Credenciais Pluggy")
    print("=" * 50)
    asyncio.run(test_pluggy())