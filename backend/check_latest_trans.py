"""
Check for 3 cents transaction
"""
import requests
from datetime import datetime

# Login
r = requests.post(
    "https://finance-backend-production-29df.up.railway.app/api/auth/login/",
    json={"email": "levilaelsilvaa@gmail.com", "password": "Levi123*"}
)
token = r.json()['tokens']['access']
headers = {"Authorization": f"Bearer {token}"}

print(f"Hora atual: {datetime.now().strftime('%H:%M:%S')}")
print(f"\n=== PROCURANDO TRANSAÇÃO DE R$ 0,03 ===\n")

# Get all recent transactions
trans = requests.get(
    "https://finance-backend-production-29df.up.railway.app/api/banking/transactions/?limit=200&ordering=-transaction_date",
    headers=headers
).json()

found_003 = False
found_002 = False

print("Transações recentes:")
for t in trans.get('results', []):
    amount = float(t['amount'])
    date = t['transaction_date']
    desc = t['description'][:50]
    
    # Show recent transactions
    if '2025-07-21' in date or '2025-07-22' in date:
        print(f"{date[:10]}: R$ {amount:.2f} - {desc}")
        
        if abs(amount) == 0.03:
            found_003 = True
            print("  ^^^ TRANSAÇÃO DE 3 CENTAVOS ENCONTRADA! ^^^")
            
        if abs(amount) == 0.02:
            found_002 = True
            print("  ^^^ TRANSAÇÃO DE 2 CENTAVOS ENCONTRADA! ^^^")

print(f"\n=== RESULTADO ===")
if found_003:
    print("✅ Transação de R$ 0,03 FOI sincronizada!")
elif found_002:
    print("✅ Transação de R$ 0,02 FOI sincronizada!")
    print("❌ Mas a de R$ 0,03 ainda não apareceu")
else:
    print("❌ Nenhuma das transações recentes (0,02 ou 0,03) apareceu")
    print("\nPossíveis razões:")
    print("1. Banco/Pluggy ainda não processou (aguarde 5-15 min)")
    print("2. Transação com data futura (timezone)")
    print("3. Correção do sync ainda não está em produção")