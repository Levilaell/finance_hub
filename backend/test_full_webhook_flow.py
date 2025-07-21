"""
Test complete webhook flow in production
"""
import requests
import json
import time
from datetime import datetime

def test_full_flow(email, password):
    base_url = "https://finance-backend-production-29df.up.railway.app"
    
    # 1. Login
    print("1. Fazendo login...")
    login_response = requests.post(
        f"{base_url}/api/auth/login/",
        json={"email": email, "password": password}
    )
    
    tokens = login_response.json()
    access_token = tokens.get('tokens', {}).get('access')
    headers = {"Authorization": f"Bearer {access_token}"}
    
    # 2. Get current balance and transaction count
    print("\n2. Verificando estado atual da conta...")
    accounts_response = requests.get(f"{base_url}/api/banking/accounts/", headers=headers)
    account = accounts_response.json()['results'][0]
    
    print(f"   Conta ID: {account['id']}")
    print(f"   Banco: {account['bank_provider']['name']}")
    print(f"   Saldo atual: R$ {account['current_balance']}")
    print(f"   Total de transações: {account['transaction_count']}")
    print(f"   External ID: {account.get('external_id', 'N/A')}")
    print(f"   Item ID: {account.get('pluggy_item_id', 'N/A')}")
    
    initial_balance = float(account['current_balance'])
    initial_count = account['transaction_count']
    
    # 3. Get last 5 transactions
    print("\n3. Últimas transações:")
    trans_response = requests.get(
        f"{base_url}/api/banking/transactions/?limit=5",
        headers=headers
    )
    transactions = trans_response.json().get('results', [])
    
    for trans in transactions[:3]:
        print(f"   {trans['transaction_date']}: {trans['description'][:40]} (R$ {trans['amount']})")
    
    # 4. Instructions for testing
    print("\n" + "="*60)
    print("INSTRUÇÕES PARA TESTAR:")
    print("="*60)
    
    print("\n1. FAÇA UMA TRANSAÇÃO PIX AGORA:")
    print("   - Envie um PIX de qualquer valor (pode ser R$ 0,01)")
    print("   - Anote a hora exata da transação")
    print("   - Aguarde a confirmação do banco")
    
    print("\n2. AGUARDE O WEBHOOK (1-3 minutos):")
    print("   - A Pluggy deve detectar a transação")
    print("   - O webhook será enviado automaticamente")
    print("   - A transação aparecerá no sistema")
    
    print("\n3. MONITORAR RESULTADO:")
    input("\nPressione ENTER após fazer a transação PIX...")
    
    # 5. Monitor for changes
    print("\nMonitorando mudanças (verificando a cada 30 segundos por 5 minutos)...")
    start_time = time.time()
    checks = 0
    
    while time.time() - start_time < 300:  # 5 minutes
        checks += 1
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Verificação #{checks}")
        
        # Check balance
        accounts_response = requests.get(f"{base_url}/api/banking/accounts/8/", headers=headers)
        if accounts_response.status_code == 200:
            current_account = accounts_response.json()
            current_balance = float(current_account['current_balance'])
            current_count = current_account.get('transaction_count', 0)
            
            print(f"   Saldo: R$ {current_balance} ", end="")
            if current_balance != initial_balance:
                print(f"(MUDOU! Diferença: R$ {current_balance - initial_balance:.2f})")
            else:
                print("(sem mudança)")
            
            print(f"   Transações: {current_count} ", end="")
            if current_count > initial_count:
                print(f"(NOVAS! +{current_count - initial_count})")
                
                # Get new transactions
                trans_response = requests.get(
                    f"{base_url}/api/banking/transactions/?limit=5",
                    headers=headers
                )
                new_trans = trans_response.json().get('results', [])
                print("\n   NOVAS TRANSAÇÕES DETECTADAS:")
                for trans in new_trans[:3]:
                    print(f"   - {trans['transaction_date']}: {trans['description'][:40]} (R$ {trans['amount']})")
                
                print("\n✅ WEBHOOK FUNCIONOU! Transações sincronizadas automaticamente!")
                return
            else:
                print("(sem mudança)")
        
        # Wait before next check
        if time.time() - start_time < 300:
            print("   Aguardando 30 segundos para próxima verificação...")
            time.sleep(30)
    
    print("\n⏱️  Tempo esgotado (5 minutos)")
    print("\nSe a transação não apareceu automaticamente:")
    print("1. Tente sincronizar manualmente no frontend")
    print("2. Verifique se o item está ACTIVE na Pluggy")
    print("3. A Pluggy pode demorar mais para processar")
    
    # 6. Final manual sync test
    print("\n4. Tentando sincronização manual...")
    sync_response = requests.post(
        f"{base_url}/api/banking/pluggy/accounts/8/sync/",
        headers=headers
    )
    print(f"   Status: {sync_response.status_code}")
    if sync_response.status_code == 200:
        result = sync_response.json()
        print(f"   Transações sincronizadas: {result.get('data', {}).get('transactions_synced', 0)}")

if __name__ == "__main__":
    print("=== TESTE COMPLETO DO WEBHOOK PLUGGY ===\n")
    test_full_flow("levilaelsilvaa@gmail.com", "Levi123*")