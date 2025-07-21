"""Quick check for new transactions"""
import requests
from datetime import datetime

# Login
r = requests.post(
    "https://finance-backend-production-29df.up.railway.app/api/auth/login/",
    json={"email": "levilaelsilvaa@gmail.com", "password": "Levi123*"}
)
token = r.json()['tokens']['access']
headers = {"Authorization": f"Bearer {token}"}

# Get account
acc = requests.get(
    "https://finance-backend-production-29df.up.railway.app/api/banking/accounts/8/",
    headers=headers
).json()

print(f"Conta: {acc['bank_provider']['name']}")
print(f"Saldo: R$ {acc['current_balance']}")
print(f"Transações: {acc.get('transaction_count', 'N/A')}")
print(f"Última sync: {acc['last_sync_at']}")

# Get last 3 transactions
trans = requests.get(
    "https://finance-backend-production-29df.up.railway.app/api/banking/transactions/?limit=3",
    headers=headers
).json()

print(f"\nÚltimas transações:")
for t in trans.get('results', []):
    print(f"- {t['transaction_date']}: {t['description'][:40]} (R$ {t['amount']})")