"""Trigger item update to force transaction sync"""
import os
import sys
sys.path.insert(0, '/Users/levilaell/Desktop/finance_hub/backend')
os.environ['DJANGO_SETTINGS_MODULE'] = 'core.settings.development'

import django
django.setup()

import asyncio
import httpx
from apps.banking.pluggy_client import PluggyClient

async def trigger_update():
    item_id = "d95eaa49-e067-4014-8220-4bc3993746f3"
    
    async with PluggyClient() as client:
        print("=== FORÇANDO ATUALIZAÇÃO DO ITEM ===\n")
        
        try:
            # Get auth token
            await client._ensure_authenticated()
            
            # Make direct PATCH request to trigger update
            headers = {
                'Authorization': f'Bearer {client.access_token}',
                'Content-Type': 'application/json'
            }
            
            async with httpx.AsyncClient() as http_client:
                response = await http_client.patch(
                    f"{client.base_url}/items/{item_id}",
                    headers=headers,
                    json={}  # Empty body triggers update
                )
                
                if response.status_code == 200:
                    result = response.json()
                    print(f"✅ Atualização iniciada!")
                    print(f"Status: {result.get('status')}")
                    print(f"ID: {result.get('id')}")
                    
                    print("\nPróximos passos:")
                    print("1. Aguarde 1-2 minutos para a atualização completar")
                    print("2. Execute 'python sync_now.py' para sincronizar")
                    print("3. Sua transação deve aparecer")
                    
                    print("\nOBS: Com status UPDATED, o webhook não funciona automaticamente")
                    print("Mas podemos forçar atualizações manuais como esta")
                else:
                    print(f"❌ Erro: {response.status_code}")
                    print(f"Resposta: {response.text}")
                    
        except Exception as e:
            print(f"❌ Erro: {e}")

# Run
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)
try:
    loop.run_until_complete(trigger_update())
finally:
    loop.close()