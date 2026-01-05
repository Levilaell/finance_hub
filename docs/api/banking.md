# API de Banking

Base URL: `/api/banking/`

## Conectores

### GET /connectors/

Listar bancos disponiveis.

**Autenticacao**: Bearer Token

**Query Params**:
| Param | Tipo | Descricao |
|-------|------|-----------|
| country | string | Filtrar por pais (ex: BR) |
| type | string | PERSONAL_BANK, BUSINESS_BANK |

**Response 200**:
```json
[
  {
    "id": 1,
    "pluggy_id": 123,
    "name": "Banco do Brasil",
    "institution_name": "Banco do Brasil S.A.",
    "logo_url": "https://...",
    "primary_color": "#FFCC00",
    "type": "BUSINESS_BANK",
    "supports_mfa": true,
    "is_sandbox": false
  }
]
```

### POST /connectors/sync/

Sincronizar lista de conectores do Pluggy.

**Autenticacao**: Bearer Token

**Response 200**:
```json
{
  "synced": 150,
  "created": 5,
  "updated": 145
}
```

---

## Conexoes

### GET /connections/

Listar conexoes do usuario.

**Autenticacao**: Bearer Token

**Response 200**:
```json
[
  {
    "id": "uuid",
    "connector": {
      "id": 1,
      "name": "Banco do Brasil"
    },
    "status": "UPDATED",
    "last_updated_at": "2025-12-18T10:00:00Z",
    "accounts_count": 2
  }
]
```

### POST /connections/

Criar nova conexao.

**Autenticacao**: Bearer Token

**Request Body**:
```json
{
  "pluggy_item_id": "item_xxxxx"
}
```

**Response 201**:
```json
{
  "id": "uuid",
  "pluggy_item_id": "item_xxxxx",
  "status": "UPDATING"
}
```

### DELETE /connections/{id}/

Desconectar banco.

**Autenticacao**: Bearer Token

**Response 204**: No content

### GET /connections/connect_token/

Obter token para widget Pluggy (nova conexao).

**Autenticacao**: Bearer Token

**Response 200**:
```json
{
  "accessToken": "xxxxx",
  "expires_at": "2025-12-18T10:25:00Z"
}
```

### GET /connections/{id}/reconnect_token/

Obter token para reconectar (credenciais expiradas).

**Autenticacao**: Bearer Token

**Response 200**:
```json
{
  "accessToken": "xxxxx",
  "itemId": "item_xxxxx"
}
```

### POST /connections/{id}/sync_transactions/

Sincronizar transacoes da conexao.

**Autenticacao**: Bearer Token

**Response 200**:
```json
{
  "status": "syncing",
  "message": "Sincronizacao iniciada"
}
```

### GET /connections/{id}/check_status/

Verificar status de sincronizacao.

**Autenticacao**: Bearer Token

**Response 200**:
```json
{
  "syncing": false,
  "status": "UPDATED",
  "message": "Sincronizado com sucesso",
  "last_updated_at": "2025-12-18T10:00:00Z"
}
```

### POST /connections/{id}/send_mfa/

Enviar token MFA.

**Autenticacao**: Bearer Token

**Request Body**:
```json
{
  "mfa_token": "123456"
}
```

**Response 200**:
```json
{
  "status": "UPDATING"
}
```

---

## Contas

### GET /accounts/

Listar contas bancarias.

**Autenticacao**: Bearer Token

**Response 200**:
```json
[
  {
    "id": "uuid",
    "name": "Conta Corrente",
    "type": "CHECKING",
    "balance": "15000.00",
    "currency_code": "BRL",
    "connection": {
      "id": "uuid",
      "connector": {
        "name": "Banco do Brasil"
      }
    },
    "last_synced_at": "2025-12-18T10:00:00Z"
  },
  {
    "id": "uuid",
    "name": "Cartao Platinum",
    "type": "CREDIT_CARD",
    "balance": "-2500.00",
    "credit_limit": "10000.00",
    "available_credit_limit": "7500.00"
  }
]
```

### POST /accounts/{id}/sync_transactions/

Sincronizar transacoes de uma conta especifica.

**Autenticacao**: Bearer Token

**Query Params**:
| Param | Tipo | Default | Descricao |
|-------|------|---------|-----------|
| days_back | int | 365 | Dias para buscar |

**Response 200**:
```json
{
  "synced": 150,
  "new": 5,
  "updated": 145
}
```

---

## Transacoes

### GET /transactions/

Listar transacoes.

**Autenticacao**: Bearer Token

**Query Params**:
| Param | Tipo | Descricao |
|-------|------|-----------|
| account_id | uuid | Filtrar por conta |
| date_from | date | Data inicial (YYYY-MM-DD) |
| date_to | date | Data final (YYYY-MM-DD) |
| type | string | CREDIT, DEBIT |
| category | uuid | Filtrar por categoria |
| limit | int | Limite de resultados |
| page | int | Pagina (paginacao) |

**Response 200**:
```json
{
  "count": 1500,
  "next": "/api/banking/transactions/?page=2",
  "previous": null,
  "results": [
    {
      "id": "uuid",
      "account_id": "uuid",
      "description": "SUPERMERCADO XYZ",
      "amount": "-350.00",
      "type": "DEBIT",
      "date": "2025-12-18T14:30:00Z",
      "pluggy_category": "Alimentacao",
      "user_category": {
        "id": "uuid",
        "name": "Supermercado",
        "color": "#22c55e",
        "icon": "🛒"
      },
      "user_subcategory": null,
      "merchant_name": "Supermercado XYZ",
      "has_linked_bill": false,
      "is_income": false,
      "is_expense": true,
      "effective_category": "Supermercado"
    }
  ]
}
```

### PATCH /transactions/{id}/

Atualizar categoria da transacao.

**Autenticacao**: Bearer Token

**Request Body**:
```json
{
  "user_category_id": "uuid",
  "user_subcategory_id": "uuid",
  "apply_to_similar": true,
  "create_rule": true
}
```

| Campo | Tipo | Descricao |
|-------|------|-----------|
| user_category_id | uuid | ID da categoria |
| user_subcategory_id | uuid | ID da subcategoria (opcional) |
| apply_to_similar | bool | Aplicar a transacoes similares |
| create_rule | bool | Criar regra automatica |

**Response 200**:
```json
{
  "id": "uuid",
  "user_category": {...},
  "similar_updated": 15,
  "rule_created": true
}
```

### GET /transactions/{id}/similar/

Buscar transacoes similares.

**Autenticacao**: Bearer Token

**Response 200**:
```json
[
  {
    "id": "uuid",
    "description": "SUPERMERCADO XYZ",
    "amount": "-280.00",
    "date": "2025-12-10T10:00:00Z"
  }
]
```

### GET /transactions/{id}/suggested_bills/

Obter bills sugeridas para vinculacao.

**Autenticacao**: Bearer Token

**Response 200**:
```json
[
  {
    "id": "uuid",
    "description": "Conta de Luz",
    "amount": "180.00",
    "due_date": "2025-12-15",
    "match_score": 0.95
  }
]
```

### POST /transactions/{id}/link_bill/

Vincular transacao a uma bill.

**Autenticacao**: Bearer Token

**Request Body**:
```json
{
  "bill_id": "uuid"
}
```

**Response 200**:
```json
{
  "success": true,
  "bill": {...}
}
```

### GET /transactions/summary/

Resumo financeiro do periodo.

**Autenticacao**: Bearer Token

**Query Params**:
| Param | Tipo | Descricao |
|-------|------|-----------|
| date_from | date | Data inicial |
| date_to | date | Data final |

**Response 200**:
```json
{
  "income": 70000.00,
  "expenses": 25000.00,
  "balance": 45000.00,
  "transaction_count": 150,
  "period_start": "2025-12-01",
  "period_end": "2025-12-18"
}
```

---

## Categorias

### GET /categories/

Listar categorias.

**Autenticacao**: Bearer Token

**Query Params**:
| Param | Tipo | Descricao |
|-------|------|-----------|
| type | string | income, expense |

**Response 200**:
```json
[
  {
    "id": "uuid",
    "name": "Alimentacao",
    "type": "expense",
    "color": "#ef4444",
    "icon": "🍔",
    "is_system": false,
    "subcategories": [
      {
        "id": "uuid",
        "name": "Restaurantes",
        "color": "#f97316"
      },
      {
        "id": "uuid",
        "name": "Supermercado",
        "color": "#84cc16"
      }
    ]
  }
]
```

### POST /categories/

Criar categoria.

**Autenticacao**: Bearer Token

**Request Body**:
```json
{
  "name": "Educacao",
  "type": "expense",
  "color": "#3b82f6",
  "icon": "📚",
  "parent_id": null
}
```

**Response 201**:
```json
{
  "id": "uuid",
  "name": "Educacao",
  "type": "expense",
  "color": "#3b82f6",
  "icon": "📚",
  "is_system": false
}
```

### PATCH /categories/{id}/

Atualizar categoria.

**Autenticacao**: Bearer Token

**Request Body**:
```json
{
  "name": "Educacao e Cursos",
  "color": "#6366f1"
}
```

### DELETE /categories/{id}/

Deletar categoria.

**Autenticacao**: Bearer Token

**Response 204**: No content

**Erros**:
| Codigo | Descricao |
|--------|-----------|
| 400 | Categoria de sistema nao pode ser deletada |

---

## Bills (Contas)

### GET /bills/

Listar bills.

**Autenticacao**: Bearer Token

**Query Params**:
| Param | Tipo | Descricao |
|-------|------|-----------|
| type | string | payable, receivable |
| status | string | pending, partially_paid, paid |
| is_overdue | bool | Apenas atrasadas |
| date_from | date | Vencimento a partir de |
| date_to | date | Vencimento ate |
| category | uuid | Por categoria |

**Response 200**:
```json
{
  "count": 50,
  "results": [
    {
      "id": "uuid",
      "type": "payable",
      "description": "Aluguel",
      "amount": "2500.00",
      "amount_paid": "0.00",
      "amount_remaining": "2500.00",
      "due_date": "2025-12-20",
      "status": "pending",
      "is_overdue": false,
      "category": {...},
      "recurrence": "monthly",
      "payments_count": 0,
      "payment_percentage": 0,
      "can_add_payment": true
    }
  ]
}
```

### POST /bills/

Criar bill.

**Autenticacao**: Bearer Token

**Request Body**:
```json
{
  "type": "payable",
  "description": "Conta de Luz",
  "amount": "180.00",
  "due_date": "2025-12-20",
  "category_id": "uuid",
  "recurrence": "monthly",
  "customer_supplier": "CEMIG",
  "notes": "Referente a dezembro"
}
```

### PATCH /bills/{id}/

Atualizar bill.

**Autenticacao**: Bearer Token

### DELETE /bills/{id}/

Deletar bill.

**Autenticacao**: Bearer Token

**Response 204**: No content

### POST /bills/{id}/add_payment/

Adicionar pagamento.

**Autenticacao**: Bearer Token

**Request Body**:
```json
{
  "amount": 100.00,
  "payment_date": "2025-12-18",
  "notes": "Pagamento parcial",
  "transaction_id": "uuid"
}
```

**Response 200**:
```json
{
  "id": "uuid",
  "amount": "100.00",
  "payment_date": "2025-12-18",
  "bill": {
    "status": "partially_paid",
    "amount_paid": "100.00"
  }
}
```

### GET /bills/{id}/payments/

Listar pagamentos de uma bill.

**Autenticacao**: Bearer Token

**Response 200**:
```json
[
  {
    "id": "uuid",
    "amount": "100.00",
    "payment_date": "2025-12-18",
    "notes": "Pagamento parcial",
    "transaction": {...}
  }
]
```

### DELETE /bills/{id}/payments/{payment_id}/

Remover pagamento.

**Autenticacao**: Bearer Token

**Response 204**: No content

### POST /bills/{id}/link_transaction/

Vincular transacao (pagamento total).

**Autenticacao**: Bearer Token

**Request Body**:
```json
{
  "transaction_id": "uuid"
}
```

### POST /bills/{id}/unlink_transaction/

Desvincular transacao.

**Autenticacao**: Bearer Token

**Response 200**:
```json
{
  "success": true
}
```

### GET /bills/{id}/suggested_transactions/

Transacoes sugeridas para vinculacao.

**Autenticacao**: Bearer Token

### GET /bills/summary/

Resumo de bills.

**Autenticacao**: Bearer Token

**Response 200**:
```json
{
  "total_payable_pending": 15000.00,
  "total_receivable_pending": 25000.00,
  "total_overdue": 2000.00,
  "count_payable": 10,
  "count_receivable": 15,
  "count_overdue": 2
}
```

### GET /bills/cash_flow_projection/

Projecao de fluxo de caixa (12 meses).

**Autenticacao**: Bearer Token

**Response 200**:
```json
[
  {
    "month": "2025-12",
    "receivable": 25000.00,
    "payable": 15000.00,
    "net": 10000.00
  }
]
```

### POST /bills/upload_boleto/

Upload e OCR de boleto.

**Autenticacao**: Bearer Token

**Content-Type**: multipart/form-data

**Request Body**:
| Campo | Tipo | Descricao |
|-------|------|-----------|
| file | File | PDF ou imagem |

**Response 200**:
```json
{
  "barcode": "23793.38128 60000.000003 00000.000400 1 87650000012500",
  "amount": 125.00,
  "due_date": "2025-12-20",
  "beneficiary": "CEMIG",
  "confidence": 85
}
```

### POST /bills/create_from_ocr/

Criar bill a partir de OCR.

**Autenticacao**: Bearer Token

**Request Body**:
```json
{
  "barcode": "23793.38128...",
  "amount": 125.00,
  "due_date": "2025-12-20",
  "description": "Conta CEMIG",
  "category_id": "uuid"
}
```

---

## Category Rules

### GET /category-rules/

Listar regras de categorizacao.

**Autenticacao**: Bearer Token

**Response 200**:
```json
[
  {
    "id": "uuid",
    "pattern": "supermercado",
    "match_type": "contains",
    "category": {...},
    "is_active": true,
    "applied_count": 25
  }
]
```

### POST /category-rules/

Criar regra.

**Autenticacao**: Bearer Token

**Request Body**:
```json
{
  "pattern": "uber",
  "match_type": "prefix",
  "category_id": "uuid"
}
```

### PATCH /category-rules/{id}/

Atualizar regra.

### DELETE /category-rules/{id}/

Deletar regra.

### GET /category-rules/stats/

Estatisticas de regras.

**Response 200**:
```json
{
  "total": 15,
  "active": 12,
  "total_applied": 450
}
```

---

## Sync Logs

### GET /sync-logs/

Listar logs de sincronizacao.

**Autenticacao**: Bearer Token

**Response 200**:
```json
[
  {
    "id": 1,
    "connection": {...},
    "sync_type": "TRANSACTIONS",
    "status": "SUCCESS",
    "started_at": "2025-12-18T10:00:00Z",
    "completed_at": "2025-12-18T10:00:30Z",
    "records_synced": 150
  }
]
```

---

## Webhooks

### POST /webhooks/pluggy/

Webhook do Pluggy (uso interno).

**Autenticacao**: Signature HMAC-SHA256

**Headers**:
```
X-Pluggy-Signature: <signature>
```

**Request Body**: Varia por evento

**Response 200**:
```json
{
  "received": true
}
```
