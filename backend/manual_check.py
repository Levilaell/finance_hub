"""Manual check for transactions"""
import requests
import time

def check_and_sync():
    # Login
    r = requests.post(
        "https://finance-backend-production-29df.up.railway.app/api/auth/login/",
        json={"email": "levilaelsilvaa@gmail.com", "password": "Levi123*"}
    )
    token = r.json()['tokens']['access']
    headers = {"Authorization": f"Bearer {token}"}
    
    print("=== SINCRONIZAÇÃO MANUAL ===\n")
    
    # Force sync
    sync_resp = requests.post(
        "https://finance-backend-production-29df.up.railway.app/api/banking/pluggy/accounts/9/sync/",
        headers=headers
    )
    
    if sync_resp.status_code == 200:
        result = sync_resp.json()
        synced = result.get('data', {}).get('transactions_synced', 0)
        
        if synced > 0:
            print(f"✅ {synced} novas transações encontradas!")
            
            # Get latest
            trans = requests.get(
                "https://finance-backend-production-29df.up.railway.app/api/banking/transactions/?limit=3&ordering=-transaction_date",
                headers=headers
            ).json()
            
            print("\nÚltimas transações:")
            for t in trans.get('results', []):
                print(f"- {t['transaction_date']}: {t['description'][:40]} (R$ {t['amount']})")
        else:
            print("⏳ Nenhuma transação nova ainda")
            print("A Pluggy pode demorar 5-30 minutos para processar transações PIX")
    else:
        print(f"❌ Erro na sincronização: {sync_resp.status_code}")

if __name__ == "__main__":
    check_and_sync()