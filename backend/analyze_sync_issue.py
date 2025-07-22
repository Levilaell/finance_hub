"""
Analyze why some transactions are missed during sync
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

print("=== ANÁLISE DO PROBLEMA DE SINCRONIZAÇÃO ===\n")

# Get account info
acc = requests.get(
    "https://finance-backend-production-29df.up.railway.app/api/banking/accounts/9/",
    headers=headers
).json()

last_sync = acc.get('last_sync_at', 'Never')
print(f"Última sincronização: {last_sync}")

# Analyze timezone issues
brazil_tz = pytz.timezone('America/Sao_Paulo')
utc_now = datetime.now(pytz.UTC)
brazil_now = utc_now.astimezone(brazil_tz)

print(f"\n=== ANÁLISE DE TIMEZONE ===")
print(f"Hora UTC: {utc_now.strftime('%Y-%m-%d %H:%M:%S')}")
print(f"Hora Brasil: {brazil_now.strftime('%Y-%m-%d %H:%M:%S')}")
print(f"Diferença: {(brazil_now.hour - utc_now.hour) % 24} horas")

# O problema pode ser:
print(f"\n=== POSSÍVEIS PROBLEMAS ===")
print("1. TIMEZONE:")
print("   - Transações feitas após 21h (Brasil) podem ter data do dia seguinte em UTC")
print("   - A sincronização pode estar buscando com datas erradas")

print("\n2. JANELA DE SINCRONIZAÇÃO:")
print("   - Se a última sync foi há poucos minutos, busca apenas 1 dia")
print("   - Transações com processamento atrasado ficam de fora")

print("\n3. DATA DE PROCESSAMENTO vs DATA DA TRANSAÇÃO:")
print("   - PIX feito hoje pode ter data de ontem no banco")
print("   - Ou data de amanhã se feito após 21h")

# Get recent transactions to analyze dates
trans = requests.get(
    "https://finance-backend-production-29df.up.railway.app/api/banking/transactions/?limit=10&ordering=-transaction_date",
    headers=headers
).json()

print(f"\n=== ANÁLISE DAS DATAS DAS TRANSAÇÕES ===")
for t in trans.get('results', [])[:5]:
    trans_date = t['transaction_date']
    created_at = t.get('created_at', 'N/A')
    amount = t['amount']
    
    # Parse dates
    trans_dt = datetime.fromisoformat(trans_date.replace('Z', '+00:00'))
    trans_brazil = trans_dt.astimezone(brazil_tz)
    
    print(f"\nValor: R$ {amount}")
    print(f"  Data da transação (UTC): {trans_dt.strftime('%Y-%m-%d %H:%M')}")
    print(f"  Data da transação (Brasil): {trans_brazil.strftime('%Y-%m-%d %H:%M')}")
    print(f"  Criada no sistema: {created_at[:16] if created_at != 'N/A' else 'N/A'}")

print(f"\n=== SOLUÇÃO PROPOSTA ===")
print("Modificar a sincronização para:")
print("1. Sempre buscar pelo menos 5 dias (não 3)")
print("2. Considerar timezone ao calcular datas")
print("3. Buscar 1 dia no futuro também (para transações após 21h)")