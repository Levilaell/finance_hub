"""Fix item status to ACTIVE"""
import os
import sys
sys.path.insert(0, '/Users/levilaell/Desktop/finance_hub/backend')
os.environ['DJANGO_SETTINGS_MODULE'] = 'core.settings.development'

import django
django.setup()

import asyncio
from apps.banking.pluggy_client import PluggyClient

async def fix_item_status():
    item_id = "d95eaa49-e067-4014-8220-4bc3993746f3"
    
    async with PluggyClient() as client:
        print("=== TENTANDO CORRIGIR STATUS DO ITEM ===\n")
        
        # 1. Check current status
        item = await client.get_item(item_id)
        current_status = item.get('status')
        print(f"Status atual: {current_status}")
        
        if current_status == 'ACTIVE':
            print("✅ Item já está ACTIVE!")
            return
        
        # 2. Try to update the item
        print("\nTentando atualizar o item...")
        try:
            # Force an update
            update_response = await client.update_item(item_id)
            print(f"Resposta: {update_response}")
            
            new_status = update_response.get('status')
            print(f"Novo status: {new_status}")
            
            if new_status == 'UPDATING':
                print("\n✅ Item está sendo atualizado!")
                print("Aguarde alguns minutos e verifique novamente")
                print("Quando terminar, o status pode mudar para ACTIVE")
            
        except Exception as e:
            print(f"❌ Erro ao atualizar: {e}")
            
        # 3. Alternative solutions
        print("\n=== SOLUÇÕES ALTERNATIVAS ===")
        print("\n1. RECONECTAR A CONTA (Recomendado):")
        print("   - Desconecte a conta no frontend")
        print("   - Conecte novamente")
        print("   - Durante a conexão, autorize 'Atualização Automática'")
        print("   - Isso criará um item com status ACTIVE")
        
        print("\n2. USAR WEBHOOKS DE ITEM:")
        print("   - O webhook 'item/updated' funciona mesmo com status UPDATED")
        print("   - Quando o item atualiza, podemos sincronizar as transações")
        
        print("\n3. SINCRONIZAÇÃO PROGRAMADA:")
        print("   - Criar uma tarefa que sincroniza a cada 30 minutos")
        print("   - Não é em tempo real, mas mantém os dados atualizados")

# Run
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)
try:
    loop.run_until_complete(fix_item_status())
finally:
    loop.close()