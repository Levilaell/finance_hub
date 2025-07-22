"""
Debug sync issue in real-time
"""
import requests
from datetime import datetime, timedelta
import pytz

# Login
r = requests.post(
    "https://finance-backend-production-29df.up.railway.app/api/auth/login/",
    json={"email": "levilaelsilvaa@gmail.com", "password": "Levi123*"}
)
token = r.json()['tokens']['access']
headers = {"Authorization": f"Bearer {token}"}

print("=== DEBUG SINCRONIZAÇÃO ÀS 22:01 ===\n")

# Timezone info
brazil_tz = pytz.timezone('America/Sao_Paulo')
now_brazil = datetime.now(brazil_tz)
now_utc = datetime.now(pytz.UTC)

print(f"Hora atual Brasil: {now_brazil.strftime('%Y-%m-%d %H:%M:%S')}")
print(f"Hora atual UTC: {now_utc.strftime('%Y-%m-%d %H:%M:%S')}")

# Get account info
acc = requests.get(
    "https://finance-backend-production-29df.up.railway.app/api/banking/accounts/9/",
    headers=headers
).json()

print(f"\nÚltima sync: {acc.get('last_sync_at', 'Never')}")
trans_count_before = acc.get('transaction_count', 0)
print(f"Transações antes: {trans_count_before}")

# Force sync
print(f"\n=== FORÇANDO SINCRONIZAÇÃO ===")
sync_resp = requests.post(
    "https://finance-backend-production-29df.up.railway.app/api/banking/pluggy/accounts/9/sync/",
    headers=headers
)

if sync_resp.status_code == 200:
    result = sync_resp.json()
    print(f"Status: OK")
    print(f"Transações sincronizadas: {result.get('data', {}).get('transactions_synced', 0)}")
    
    # Check logs if available
    if 'data' in result:
        data = result['data']
        print(f"Mensagem: {data.get('message', '')}")
        print(f"Status sync: {data.get('status', '')}")

# Get updated count
acc_after = requests.get(
    "https://finance-backend-production-29df.up.railway.app/api/banking/accounts/9/",
    headers=headers
).json()

trans_count_after = acc_after.get('transaction_count', 0)
print(f"\nTransações depois: {trans_count_after}")
print(f"Novas transações: {trans_count_after - trans_count_before}")

# Get latest transactions
print(f"\n=== ÚLTIMAS TRANSAÇÕES ===")
trans = requests.get(
    "https://finance-backend-production-29df.up.railway.app/api/banking/transactions/?limit=10&ordering=-created_at",
    headers=headers
).json()

for t in trans.get('results', [])[:5]:
    created = t.get('created_at', 'N/A')
    trans_date = t['transaction_date']
    amount = t['amount']
    desc = t['description'][:40]
    
    # Check if it's today's transaction
    if abs(float(amount)) == 0.03:
        print(f"\n✅ TRANSAÇÃO DE 3 CENTAVOS ENCONTRADA!")
    
    print(f"\nR$ {amount} - {desc}")
    print(f"  Data transação: {trans_date}")
    print(f"  Criada em: {created}")

print(f"\n=== ANÁLISE ===")
print("Se a transação de R$ 0,03 não apareceu:")
print("1. A correção pode não ter sido aplicada ainda (aguarde deploy)")
print("2. A Pluggy ainda não processou a transação")
print("3. O banco ainda não disponibilizou via API")
print("\nTente novamente em 5-10 minutos")