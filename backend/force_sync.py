"""Force sync and check results"""
import requests
import time

# Login
print("1. Fazendo login...")
r = requests.post(
    "https://finance-backend-production-29df.up.railway.app/api/auth/login/",
    json={"email": "levilaelsilvaa@gmail.com", "password": "Levi123*"}
)
token = r.json()['tokens']['access']
headers = {"Authorization": f"Bearer {token}"}

# Get initial state
acc = requests.get(
    "https://finance-backend-production-29df.up.railway.app/api/banking/accounts/8/",
    headers=headers
).json()

print(f"\n2. Estado antes da sincronização:")
print(f"   Transações: {acc.get('transaction_count', 'N/A')}")
print(f"   Última sync: {acc['last_sync_at']}")

# Force sync
print(f"\n3. Forçando sincronização manual...")
sync_response = requests.post(
    "https://finance-backend-production-29df.up.railway.app/api/banking/pluggy/accounts/8/sync/",
    headers=headers
)

print(f"   Status: {sync_response.status_code}")
if sync_response.status_code == 200:
    result = sync_response.json()
    print(f"   Mensagem: {result.get('data', {}).get('message')}")
    print(f"   Transações sincronizadas: {result.get('data', {}).get('transactions_synced')}")

# Wait a bit
print("\n4. Aguardando 5 segundos...")
time.sleep(5)

# Check again
acc_after = requests.get(
    "https://finance-backend-production-29df.up.railway.app/api/banking/accounts/8/",
    headers=headers
).json()

print(f"\n5. Estado após sincronização:")
print(f"   Transações: {acc_after.get('transaction_count', 'N/A')}")
print(f"   Última sync: {acc_after['last_sync_at']}")

if acc_after.get('transaction_count', 0) > acc.get('transaction_count', 0):
    print(f"\n✅ NOVAS TRANSAÇÕES ENCONTRADAS!")
    
    # Get latest transactions
    trans = requests.get(
        "https://finance-backend-production-29df.up.railway.app/api/banking/transactions/?limit=5",
        headers=headers
    ).json()
    
    print(f"\nÚltimas transações:")
    for t in trans.get('results', [])[:5]:
        print(f"- {t['transaction_date']}: {t['description'][:40]} (R$ {t['amount']})")
else:
    print(f"\n⚠️  Nenhuma transação nova encontrada")
    print(f"\nPossíveis razões:")
    print(f"1. A Pluggy ainda não processou a transação")
    print(f"2. O item pode precisar ser reconectado")
    print(f"3. Aguarde mais alguns minutos")