# Sistema de Assinatura Stripe - Guia de Configuração

## 📋 Resumo do Sistema

Sistema completo de assinatura implementado com:
- **Plano único:** Pro - R$ 97,00/mês
- **Trial:** 7 dias com cartão obrigatório
- **Grace period:** 3 dias após falha de pagamento
- **Cancelamento:** A qualquer momento via Stripe Customer Portal

---

## 🔧 Configuração Inicial

### 1. Instalar Dependências

**Backend:**
```bash
cd backend
pip install stripe==11.0.0 dj-stripe==2.8.3
```

**Frontend:**
Stripe já instalado:
- `@stripe/react-stripe-js@2.4.0`
- `@stripe/stripe-js@2.2.0`

### 2. Configurar Variáveis de Ambiente

Adicione ao arquivo `backend/.env`:

```bash
# Stripe Test Keys (desenvolvimento)
STRIPE_TEST_SECRET_KEY=sk_test_...
STRIPE_TEST_PUBLIC_KEY=pk_test_...
DJSTRIPE_WEBHOOK_SECRET=whsec_...

# Stripe Live Keys (produção)
STRIPE_LIVE_SECRET_KEY=sk_live_...
STRIPE_LIVE_PUBLIC_KEY=pk_live_...
STRIPE_LIVE_MODE=False  # True para produção

# Opcional: Price ID padrão
STRIPE_DEFAULT_PRICE_ID=price_...
```

### 3. Rodar Migrations

```bash
cd backend
python manage.py migrate
```

Isso criará as tabelas do dj-stripe automaticamente.

---

## 🎯 Configuração no Stripe Dashboard

### 1. Criar Product e Price

1. Acesse [Stripe Dashboard](https://dashboard.stripe.com)
2. Vá em **Products** → **Add product**
3. Configure:
   - **Name:** Plano Pro
   - **Description:** Acesso completo ao Finance Hub
   - **Pricing:** R$ 97,00 / month
   - **Currency:** BRL (Brazilian Real)
   - **Billing period:** Monthly

4. Copie o **Price ID** (ex: `price_1234...`) e adicione ao `.env` como `STRIPE_DEFAULT_PRICE_ID`

### 2. Configurar Billing Settings

1. Vá em **Settings** → **Billing**
2. Configure:
   - **Smart retries:** Enabled (tenta cobrar automaticamente)
   - **Grace period:** 3 dias antes de cancelar
   - **Email receipts:** Enabled

### 3. Configurar Customer Portal

1. Vá em **Settings** → **Customer portal**
2. Ative as seguintes opções:
   - ✅ **Update payment method**
   - ✅ **Cancel subscription**
   - ✅ **View invoices**
3. Configurar cancelamento:
   - **Cancel immediately** (ou cancel at period end, sua escolha)

### 4. Configurar Webhooks

1. Vá em **Developers** → **Webhooks**
2. Clique em **Add endpoint**
3. Configure:
   - **Endpoint URL:** `https://seu-dominio.com/api/subscriptions/webhooks/stripe/`
   - **Events to listen:** Select all Subscription and Invoice events, ou específicos:
     - `customer.subscription.created`
     - `customer.subscription.updated`
     - `customer.subscription.deleted`
     - `invoice.paid`
     - `invoice.payment_failed`
     - `customer.subscription.trial_will_end`

4. Copie o **Webhook Secret** (whsec_...) e adicione ao `.env` como `DJSTRIPE_WEBHOOK_SECRET`

---

## 🚀 Endpoints Implementados

### Backend API

| Endpoint | Método | Descrição |
|----------|--------|-----------|
| `/api/subscriptions/config/` | GET | Retorna Stripe public key |
| `/api/subscriptions/status/` | GET | Status da assinatura do usuário |
| `/api/subscriptions/checkout/` | POST | Criar subscription com trial |
| `/api/subscriptions/portal/` | POST | Criar sessão do Customer Portal |
| `/api/subscriptions/webhooks/stripe/` | POST | Webhook handler (dj-stripe) |

### Frontend Routes

| Rota | Descrição |
|------|-----------|
| `/subscription/expired` | Página de bloqueio/reativação |
| `/settings?tab=subscription` | Gerenciamento de assinatura |

---

## 📦 Componentes Frontend

### Componentes Criados

1. **CheckoutForm** (`components/subscription/CheckoutForm.tsx`)
   - Stripe Elements integration
   - Coleta dados do cartão
   - Cria subscription com trial de 7 dias

2. **SubscriptionManagement** (`components/subscription/SubscriptionManagement.tsx`)
   - Exibe status da assinatura
   - Mostra dias restantes do trial
   - Botão para Customer Portal

3. **Subscription Expired Page** (`app/subscription/expired/page.tsx`)
   - Página de bloqueio
   - Opções de reativação
   - Link para atualizar pagamento

### Integração no Fluxo

**Após Cadastro:**
```tsx
// Em app/(auth)/register/page.tsx
// Após registro bem-sucedido, redirecionar para:
router.push('/checkout'); // Coletar dados do cartão

// Ou incluir CheckoutForm na própria página de registro
<CheckoutForm priceId="price_..." />
```

**Em Settings:**
```tsx
// Em app/settings/page.tsx
import { SubscriptionManagement } from '@/components/subscription/SubscriptionManagement';

<TabsContent value="subscription">
  <SubscriptionManagement />
</TabsContent>
```

---

## 🔒 Segurança Implementada

### Middleware de Verificação

O `SubscriptionRequiredMiddleware` verifica automaticamente se o usuário tem assinatura ativa antes de acessar rotas protegidas.

**Rotas Isentas:**
- `/api/auth/`
- `/api/subscriptions/`
- `/admin/`
- `/subscription/expired`

**Rotas Permitidas quando Expirado:**
- `/settings` (para gerenciar assinatura)

### Webhook Validation

Os webhooks são validados automaticamente pelo dj-stripe usando o `DJSTRIPE_WEBHOOK_SECRET`.

---

## 🎨 UX Implementada

### Estados de Subscription

| Status | Comportamento |
|--------|---------------|
| **trialing** | ✅ Acesso completo + Banner com dias restantes |
| **active** | ✅ Acesso completo + Informações de próxima cobrança |
| **past_due** | ⚠️ Banner de urgência + Grace period de 3 dias |
| **canceled** | ❌ Bloqueio total + Opção de reativação |

### Fluxo de Trial

1. Usuário se cadastra
2. Adiciona cartão (via CheckoutForm)
3. Subscription criada com `trial_period_days=7`
4. Acesso liberado por 7 dias
5. Dia 7: Stripe cobra automaticamente
6. Se falhar: Status muda para `past_due` → Grace period de 3 dias
7. Após 3 dias sem pagamento: Status `canceled` → Bloqueio total

---

## 🛠️ Django Admin

### Gerenciamento via Admin

Acesse `/admin/` e você terá:

**Customer Admin:**
- Visualizar clientes Stripe
- Sincronizar dados do Stripe
- Ver histórico de pagamentos

**Subscription Admin:**
- Visualizar todas as assinaturas
- Ações em massa:
  - Cancelar subscription (at period end)
  - Reativar subscription
- Filtros por status, data, etc.

**Ações Disponíveis:**
```python
# No Django Admin
- Sync from Stripe (sincronizar dados)
- Cancel at period end (cancelar no fim do período)
- Reactivate subscription (reativar)
```

---

## 🧪 Testando

### Cartões de Teste Stripe

```
Sucesso: 4242 4242 4242 4242
Falha (generic): 4000 0000 0000 0002
Requer 3D Secure: 4000 0025 0000 3155

Expiry: Qualquer data futura (ex: 12/34)
CVC: Qualquer 3 dígitos (ex: 123)
```

### Testar Webhooks Localmente

Use Stripe CLI:
```bash
stripe listen --forward-to http://localhost:8000/api/subscriptions/webhooks/stripe/
```

### Simular Fim de Trial

Use o Stripe Dashboard:
1. Test Clocks → Create test clock
2. Avançar o relógio para 7 dias à frente
3. Observar a cobrança automática

---

## ✅ Checklist de Deploy

### Antes de ir para produção:

- [ ] Configurar `STRIPE_LIVE_MODE=True`
- [ ] Adicionar keys de produção (`STRIPE_LIVE_SECRET_KEY`, `STRIPE_LIVE_PUBLIC_KEY`)
- [ ] Criar Product e Price em modo live
- [ ] Configurar webhook de produção (URL pública)
- [ ] Testar fluxo completo em staging
- [ ] Configurar emails de notificação (trial ending, payment failed)
- [ ] Revisar configurações do Customer Portal
- [ ] Configurar SSL/HTTPS (obrigatório para Stripe)

---

## 📊 Monitoramento

### Métricas Importantes

Via Stripe Dashboard:
- Taxa de conversão (trial → pago)
- Taxa de churn (cancelamentos)
- Failed payments
- Revenue (MRR - Monthly Recurring Revenue)

Via Django Admin:
- Total de assinaturas ativas
- Subscriptions em trial
- Subscriptions past_due

---

## 🐛 Troubleshooting

### Problema: "No customer found"
**Solução:** Usuário não tem Customer criado no Stripe. O sistema cria automaticamente no primeiro checkout.

### Problema: "Webhook signature verification failed"
**Solução:** Verificar se `DJSTRIPE_WEBHOOK_SECRET` está correto no `.env`

### Problema: "Middleware bloqueia mesmo com subscription ativa"
**Solução:** Verificar se `has_active_subscription` property está funcionando. Testar:
```python
python manage.py shell
from apps.authentication.models import User
user = User.objects.get(email='teste@example.com')
print(user.has_active_subscription)
```

### Problema: "Stripe Elements não carrega"
**Solução:** Verificar se `STRIPE_TEST_PUBLIC_KEY` está configurado e sendo retornado pelo endpoint `/api/subscriptions/config/`

---

## 📚 Recursos Adicionais

- [Stripe Docs - Subscriptions](https://stripe.com/docs/billing/subscriptions/overview)
- [dj-stripe Docs](https://dj-stripe.github.io/dj-stripe/)
- [Stripe Elements React](https://stripe.com/docs/stripe-js/react)
- [Customer Portal Docs](https://stripe.com/docs/billing/subscriptions/integrating-customer-portal)

---

## 🎯 Próximos Passos Opcionais

1. **Emails Automáticos:**
   - Trial ending reminder (3 dias antes)
   - Payment failed notification
   - Subscription canceled confirmation

2. **Analytics:**
   - Dashboard de métricas de subscription
   - Relatório de churn
   - Previsão de MRR

3. **Features Avançadas:**
   - Múltiplos planos (se necessário no futuro)
   - Add-ons e extras
   - Descontos e cupons
   - Programa de afiliados

---

**Sistema implementado com sucesso! 🎉**

Para dúvidas ou problemas, consulte a documentação do Stripe ou abra uma issue no repositório.
