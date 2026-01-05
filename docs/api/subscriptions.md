# API de Subscriptions

Base URL: `/api/subscriptions/`

## Endpoints

### POST /checkout/

Criar sessao de checkout Stripe.

**Autenticacao**: Bearer Token

**Request Body**:
```json
{
  "price_id": "price_xxxxx"
}
```

| Campo | Tipo | Obrigatorio | Descricao |
|-------|------|-------------|-----------|
| price_id | string | Nao | ID do preco Stripe (usa default se omitido) |

**Response 200**:
```json
{
  "checkout_url": "https://checkout.stripe.com/pay/...",
  "session_id": "cs_xxxxx"
}
```

**Notas**:
- Se usuario nao usou trial, sessao inclui `trial_period_days=7`
- Se ja usou trial, cobranca imediata

---

### GET /status/

Obter status da assinatura atual.

**Autenticacao**: Bearer Token

**Response 200 (ativa)**:
```json
{
  "status": "active",
  "subscription_id": "sub_xxxxx",
  "customer_id": "cus_xxxxx",
  "current_period_start": "2025-12-01T00:00:00Z",
  "current_period_end": "2026-01-01T00:00:00Z",
  "cancel_at_period_end": false,
  "plan": {
    "id": "price_xxxxx",
    "name": "Plano Pro",
    "amount": 4990,
    "currency": "brl",
    "interval": "month"
  }
}
```

**Response 200 (trial)**:
```json
{
  "status": "trialing",
  "subscription_id": "sub_xxxxx",
  "trial_start": "2025-12-11T00:00:00Z",
  "trial_end": "2025-12-18T00:00:00Z",
  "days_remaining": 3
}
```

**Response 200 (sem assinatura)**:
```json
{
  "status": "none",
  "message": "Nenhuma assinatura ativa"
}
```

### Status Possiveis

| Status | Descricao |
|--------|-----------|
| `trialing` | Em periodo de trial |
| `active` | Assinatura ativa |
| `past_due` | Pagamento atrasado |
| `canceled` | Cancelada |
| `none` | Sem assinatura |

---

### POST /portal/

Criar sessao do portal do cliente Stripe.

**Autenticacao**: Bearer Token

**Request Body**:
```json
{
  "return_url": "https://app.caixahub.com/settings"
}
```

**Response 200**:
```json
{
  "portal_url": "https://billing.stripe.com/session/..."
}
```

**Funcionalidades do Portal**:
- Atualizar forma de pagamento
- Ver historico de faturas
- Cancelar assinatura
- Alterar plano

---

### GET /config/

Obter configuracao publica do Stripe.

**Autenticacao**: Bearer Token

**Response 200**:
```json
{
  "publishable_key": "pk_test_xxxxx",
  "default_price_id": "price_xxxxx"
}
```

---

### GET /session-status/

Verificar status de uma sessao de checkout.

**Autenticacao**: Nao requerida (AllowAny)

**Query Params**:
| Param | Tipo | Descricao |
|-------|------|-----------|
| session_id | string | ID da sessao de checkout |

**Response 200 (completa)**:
```json
{
  "status": "complete",
  "payment_status": "paid",
  "customer_email": "usuario@email.com",
  "subscription_id": "sub_xxxxx"
}
```

**Response 200 (pendente)**:
```json
{
  "status": "open",
  "payment_status": "unpaid"
}
```

**Response 200 (expirada)**:
```json
{
  "status": "expired"
}
```

---

## Fluxo de Checkout

### 1. Iniciar Checkout

```
POST /checkout/
→ { checkout_url, session_id }
→ Redireciona usuario para checkout_url
```

### 2. Usuario no Stripe

```
Usuario preenche dados de pagamento
→ Stripe processa
→ Redireciona para success_url ou cancel_url
```

### 3. Verificar Resultado

```
GET /session-status/?session_id=cs_xxxxx
→ { status: "complete" }
```

### 4. Webhook (Assincrono)

```
Stripe → POST /stripe/webhook/
→ dj-stripe processa
→ Subscription criada/atualizada
```

---

## Trial

### Elegibilidade

```python
# Logica no backend
trial_tracking = TrialUsageTracking.objects.get(user=user)
if trial_tracking.has_used_trial:
    # Sem trial
else:
    # Com trial de 7 dias
```

### Apos Trial

- Cobranca automatica no cartao cadastrado
- Email de aviso antes do fim do trial
- Se pagamento falhar: status = `past_due`

---

## Cancelamento

### Via Portal

1. Usuario acessa `POST /portal/`
2. Abre portal Stripe
3. Cancela assinatura
4. Webhook atualiza status

### Comportamento

- `cancel_at_period_end: true` - Acesso ate fim do periodo
- Nao ha reembolso proporcional
- Pode reativar antes do fim

---

## Webhooks Stripe

Gerenciados automaticamente pelo dj-stripe.

### Eventos Principais

| Evento | Acao |
|--------|------|
| `checkout.session.completed` | Cria subscription |
| `customer.subscription.created` | Sincroniza dados |
| `customer.subscription.updated` | Atualiza status |
| `customer.subscription.deleted` | Marca cancelada |
| `invoice.payment_succeeded` | Registra pagamento |
| `invoice.payment_failed` | Marca past_due |

---

## Erros

| Codigo | Situacao | Resposta |
|--------|----------|----------|
| 400 | Price ID invalido | `{"error": "Invalid price"}` |
| 402 | Pagamento falhou | `{"error": "Payment failed"}` |
| 404 | Sessao nao encontrada | `{"error": "Session not found"}` |

---

## Variaveis de Ambiente

```bash
STRIPE_TEST_PUBLIC_KEY=pk_test_xxxxx
STRIPE_TEST_SECRET_KEY=sk_test_xxxxx
STRIPE_LIVE_MODE=false
STRIPE_DEFAULT_PRICE_ID=price_xxxxx
DJSTRIPE_WEBHOOK_SECRET=whsec_xxxxx
```
