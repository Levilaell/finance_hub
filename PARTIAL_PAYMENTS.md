# Pagamentos Parciais (Rateados) - Documentação

## Visão Geral

Sistema que permite vincular **múltiplas transações bancárias** a uma única conta a pagar/receber (Bill), possibilitando pagamentos rateados/parciais com rastreamento individual de cada pagamento.

**Caso de uso:** Conta de R$ 5.000 paga em 5 transações de R$ 1.000 cada.

## Arquitetura

### Modelo de Dados

```
Bill (1) ←→ (N) BillPayment (1) ←→ (0..1) Transaction
```

- Uma Bill pode ter múltiplos BillPayments
- Cada BillPayment pode ter uma Transaction vinculada (ou ser manual)
- Cada Transaction só pode estar em um BillPayment (OneToOne)

### Modelo BillPayment

```python
class BillPayment(models.Model):
    id = models.UUIDField(primary_key=True)
    bill = models.ForeignKey(Bill, related_name='payments')
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    payment_date = models.DateTimeField(default=timezone.now)
    notes = models.TextField(blank=True)
    transaction = models.OneToOneField(Transaction, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

## API Endpoints

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET | `/api/banking/bills/{id}/payments/` | Lista pagamentos da bill |
| POST | `/api/banking/bills/{id}/add_payment/` | Adiciona pagamento |
| DELETE | `/api/banking/bills/{id}/payments/{payment_id}/` | Remove pagamento |
| GET | `/api/banking/bills/{id}/suggested_transactions_partial/` | Transações sugeridas |

### Exemplo: Adicionar Pagamento

```bash
POST /api/banking/bills/{bill_id}/add_payment/
Content-Type: application/json

# Com transação vinculada:
{
  "amount": 1000.00,
  "transaction_id": "uuid-da-transacao",
  "notes": "Pagamento parcial 1/5"
}

# Pagamento manual (sem transação):
{
  "amount": 1000.00,
  "notes": "Pagamento via PIX"
}
```

## Componentes Frontend

### LinkPartialPaymentDialog

Dialog com duas abas:
1. **Vincular Transação** - Lista transações sugeridas com score de relevância
2. **Pagamento Manual** - Formulário para registrar pagamento sem vincular transação

### BillPaymentsList

Lista de pagamentos de uma bill com:
- Valor e data de cada pagamento
- Indicador se é vinculado ou manual
- Detalhes da transação (quando vinculada)
- Botão para remover pagamento

## Campos Adicionados ao Bill

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `payments` | Array | Lista de BillPayment |
| `payments_count` | Number | Quantidade de pagamentos |
| `can_add_payment` | Boolean | Se pode adicionar mais pagamentos |

## Validações

- Soma dos pagamentos não pode exceder `amount` da bill
- Transação só pode estar vinculada a um pagamento
- Tipos compatíveis: payable→DEBIT, receivable→CREDIT
- Bill deve estar elegível (status não paid/cancelled)
- Valor do pagamento deve ser > 0

## Migração

A migração `0014_billpayment.py` inclui data migration que:
1. Cria BillPayment para bills com `linked_transaction` preenchido
2. Cria BillPayment para bills com `amount_paid > 0` sem transação
3. Limpa `Bill.linked_transaction` após migração

### Executar Migração

```bash
cd backend
python manage.py migrate banking
```

## Retrocompatibilidade

- Campo `linked_transaction` no Bill mantido (será NULL após migração)
- Endpoints antigos continuam funcionando
- `has_linked_transaction` verifica ambos: legacy e BillPayment

---

## Bug Fix: Seleção de Subcategorias

### Problema
Ao criar/editar uma conta, subcategorias não apareciam no dropdown de categorias.

### Solução
Função `flattenCategories()` em `bills/page.tsx` que achata a hierarquia:

```typescript
const flattenCategories = (cats: Category[], type: 'income' | 'expense') => {
  return cats
    .filter(c => c.type === type)
    .flatMap(cat => {
      const items = [{ ...cat, displayName: cat.name, isSubcategory: false }];
      if (cat.subcategories?.length) {
        items.push(...cat.subcategories.map(sub => ({
          ...sub,
          displayName: `  └ ${sub.name}`,
          isSubcategory: true
        })));
      }
      return items;
    });
};
```

Subcategorias agora aparecem com indentação visual (`└`).
