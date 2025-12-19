# Vinculacao Manual de Transacoes e Contas

## Descricao

Permite vincular transacoes bancarias a contas (bills) mesmo quando os valores sao diferentes. O sistema registra a vinculacao como um pagamento parcial.

## Endpoints

### GET /api/banking/transactions/{id}/all_pending_bills/

Retorna TODAS as bills pendentes compativeis (sem filtro de valor).

**Response:**
```json
[
  {
    "id": "uuid",
    "description": "Conta de Luz",
    "amount": 150.00,
    "amount_remaining": 150.00,
    "due_date": "2025-12-20",
    "type": "payable",
    "amount_match": false,
    "amount_diff": -50.00,
    "would_overpay": false,
    "relevance_score": 45
  }
]
```

### POST /api/banking/transactions/{id}/link_bill_manual/

Vincula transacao a bill, criando um BillPayment.

**Request:**
```json
{
  "bill_id": "uuid"
}
```

**Comportamento:**
- `tx.amount <= bill.remaining`: Pagamento parcial
- `tx.amount > bill.remaining`: Registra apenas o valor restante da bill

---

## Como Testar

### 1. Preparacao

```bash
# Acessar Django shell
cd backend
python manage.py shell
```

```python
from apps.banking.models import Bill, Transaction, BillPayment
from apps.authentication.models import User
from decimal import Decimal

user = User.objects.first()

# Criar bill de teste
bill = Bill.objects.create(
    user=user,
    type='payable',
    description='Teste Vinculacao Manual',
    amount=Decimal('100.00'),
    due_date='2025-12-20'
)
print(f"Bill criada: {bill.id}")

# Pegar uma transacao DEBIT nao vinculada
tx = Transaction.objects.filter(
    account__connection__user=user,
    type='DEBIT',
    linked_bill__isnull=True
).exclude(
    bill_payment__isnull=False
).first()
print(f"Transacao: {tx.id} - R$ {tx.amount}")
```

### 2. Testar via API (curl)

```bash
# Substituir TOKEN, TX_ID e BILL_ID

# Listar bills disponiveis
curl -X GET "http://localhost:8000/api/banking/transactions/{TX_ID}/all_pending_bills/" \
  -H "Authorization: Bearer {TOKEN}"

# Vincular
curl -X POST "http://localhost:8000/api/banking/transactions/{TX_ID}/link_bill_manual/" \
  -H "Authorization: Bearer {TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"bill_id": "{BILL_ID}"}'
```

### 3. Testar via Frontend

1. Acessar `/transactions`
2. Clicar nos 3 pontos de uma transacao
3. Selecionar "Vincular a Conta"
4. Verificar que TODAS as bills aparecem (nao so valor exato)
5. Bills com valor diferente mostram warning amarelo/azul
6. Clicar "Vincular Mesmo Assim"
7. Verificar toast de sucesso

### 4. Verificar Resultado

```python
# No Django shell
bill.refresh_from_db()
print(f"Status: {bill.status}")
print(f"Pago: R$ {bill.amount_paid}")
print(f"Restante: R$ {bill.amount_remaining}")

# Ver pagamento criado
payment = BillPayment.objects.filter(bill=bill).first()
print(f"Payment: R$ {payment.amount} - TX: {payment.transaction_id}")
```

---

## Casos de Teste

| Cenario | TX | Bill | Resultado |
|---------|-----|------|-----------|
| Valor exato | R$ 100 | R$ 100 | Bill paga |
| Pagamento parcial | R$ 80 | R$ 100 | Bill parcialmente paga (resta R$ 20) |
| Transacao maior | R$ 150 | R$ 100 | Bill paga (registra R$ 100) |
| Bill ja paga | - | status=paid | Erro |
| TX ja vinculada | - | - | Erro |

---

## Arquivos Modificados

- `backend/apps/banking/services.py` - Novos metodos
- `backend/apps/banking/views.py` - Novos endpoints
- `backend/apps/banking/serializers.py` - Suporte a allow_partial
- `frontend/services/banking.service.ts` - Novos metodos API
- `frontend/types/banking.ts` - Novo tipo BillSuggestionExtended
- `frontend/components/banking/LinkBillDialog.tsx` - UI atualizada
