"""
Verify correct account
"""
import requests

# Login
r = requests.post(
    "https://finance-backend-production-29df.up.railway.app/api/auth/login/",
    json={"email": "levilaelsilvaa@gmail.com", "password": "Levi123*"}
)
token = r.json()['tokens']['access']
headers = {"Authorization": f"Bearer {token}"}

# Get all accounts
print("=== VERIFICANDO CONTAS ===\n")
accounts_resp = requests.get(
    "https://finance-backend-production-29df.up.railway.app/api/banking/accounts/",
    headers=headers
)

accounts = accounts_resp.json().get('results', [])
print(f"Total de contas: {len(accounts)}")

for acc in accounts:
    print(f"\nConta ID: {acc.get('id')}")
    print(f"  Banco: {acc.get('bank_provider', {}).get('name', 'N/A')}")
    print(f"  Número: {acc.get('account_number', 'N/A')}")
    print(f"  Saldo: R$ {acc.get('current_balance', 0)}")
    print(f"  Transações: {acc.get('transaction_count', 0)}")
    print(f"  External ID: {acc.get('external_id', 'N/A')}")
    print(f"  Última sync: {acc.get('last_sync_at', 'Never')}")
    
    # Try to sync this account
    if acc.get('external_id'):
        print(f"\n  Tentando sincronizar conta {acc['id']}...")
        sync_resp = requests.post(
            f"https://finance-backend-production-29df.up.railway.app/api/banking/pluggy/accounts/{acc['id']}/sync/",
            headers=headers
        )
        
        if sync_resp.status_code == 200:
            result = sync_resp.json()
            synced = result.get('data', {}).get('transactions_synced', 0)
            print(f"  ✅ Sincronizado: {synced} transações")
        else:
            print(f"  ❌ Erro: {sync_resp.status_code}")

print("\n=== RESUMO ===")            
print("Se a transação de R$ 0,03 não apareceu em nenhuma conta:")
print("1. Ainda não foi processada pela Pluggy/banco")
print("2. Aguarde mais 5-10 minutos")
print("3. A correção da janela de sincronização pode não ter sido aplicada ainda")