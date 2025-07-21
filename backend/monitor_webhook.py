"""
Monitor webhook activity in production
"""
import requests
import time
from datetime import datetime

def monitor_production():
    base_url = "https://finance-backend-production-29df.up.railway.app"
    
    # Login
    print("Fazendo login...")
    login_response = requests.post(
        f"{base_url}/api/auth/login/",
        json={"email": "levilaelsilvaa@gmail.com", "password": "Levi123*"}
    )
    
    tokens = login_response.json()
    access_token = tokens.get('tokens', {}).get('access')
    headers = {"Authorization": f"Bearer {access_token}"}
    
    # Get initial state
    accounts_response = requests.get(f"{base_url}/api/banking/accounts/", headers=headers)
    account = accounts_response.json()['results'][0]
    
    print(f"\n=== ESTADO INICIAL ===")
    print(f"Conta: {account['bank_provider']['name']} (ID: {account['id']})")
    print(f"Saldo: R$ {account['current_balance']}")
    print(f"Transações: {account['transaction_count']}")
    print(f"External ID: {account.get('external_id')}")
    print(f"Item ID: {account.get('pluggy_item_id')}")
    
    initial_count = account['transaction_count']
    
    # Get last transaction
    trans_response = requests.get(f"{base_url}/api/banking/transactions/?limit=1", headers=headers)
    last_trans = trans_response.json().get('results', [{}])[0]
    if last_trans:
        print(f"\nÚltima transação:")
        print(f"  {last_trans.get('transaction_date')}: {last_trans.get('description', '')[:50]}")
    
    print(f"\n=== INSTRUÇÕES ===")
    print(f"1. Faça uma transação PIX agora (pode ser R$ 0,01)")
    print(f"2. Este script vai monitorar por 3 minutos")
    print(f"3. Se o webhook funcionar, a transação aparecerá automaticamente")
    
    print(f"\n=== MONITORANDO (3 minutos) ===")
    start_time = time.time()
    checks = 0
    
    while time.time() - start_time < 180:  # 3 minutes
        checks += 1
        time.sleep(20)  # Check every 20 seconds
        
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Verificação #{checks}")
        
        # Check for new transactions
        accounts_response = requests.get(f"{base_url}/api/banking/accounts/8/", headers=headers)
        if accounts_response.status_code == 200:
            current_account = accounts_response.json()
            current_count = current_account.get('transaction_count', 0)
            
            if current_count > initial_count:
                print(f"🎉 NOVAS TRANSAÇÕES DETECTADAS! (+{current_count - initial_count})")
                
                # Get new transactions
                trans_response = requests.get(
                    f"{base_url}/api/banking/transactions/?limit=3",
                    headers=headers
                )
                transactions = trans_response.json().get('results', [])
                
                print("\nNovas transações:")
                for trans in transactions:
                    trans_date = trans.get('transaction_date', 'N/A')
                    if trans_date != last_trans.get('transaction_date'):
                        print(f"  ✅ {trans_date}: {trans.get('description', '')[:50]} (R$ {trans.get('amount')})")
                
                print("\n✅ WEBHOOK FUNCIONOU! As transações foram sincronizadas automaticamente!")
                
                # Test webhook URL
                print("\nTestando endpoint do webhook...")
                webhook_test = requests.get(f"{base_url}/api/banking/pluggy/webhook/")
                print(f"Webhook status: {webhook_test.status_code} (405 = funcionando)")
                
                return
            else:
                print(f"  Transações: {current_count} (sem mudanças)")
                print(f"  Saldo: R$ {current_account.get('current_balance')}")
    
    print(f"\n⏱️  Tempo esgotado")
    print(f"\nSe a transação não apareceu:")
    print(f"1. A Pluggy pode demorar mais para processar")
    print(f"2. Tente sincronizar manualmente no frontend")
    print(f"3. Verifique o status do item na Pluggy")

if __name__ == "__main__":
    monitor_production()