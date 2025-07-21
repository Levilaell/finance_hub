# Resumo da Integração Stripe

## O que foi implementado:

### 1. Modelo de Dados Atualizado
- Adicionados campos `stripe_price_id_monthly` e `stripe_price_id_yearly` no modelo `SubscriptionPlan`
- Migração criada e aplicada com sucesso

### 2. Comandos de Gerenciamento
- `list_plans_for_stripe`: Lista planos atuais e gera código para atualização
- `update_stripe_prices`: Atualiza IDs de preços do Stripe (precisa dos IDs reais)

### 3. Método update_subscription Implementado
- Agora o StripeGateway tem implementação completa de `update_subscription`
- Suporta proration (cobrança proporcional) automática
- Retorna payment intent se houver valor adicional a pagar

### 4. Checkout Atualizado
- Usa o ID de preço correto baseado no ciclo de cobrança (mensal/anual)
- Cria cliente Stripe automaticamente se não existir
- Validação de IDs de preço configurados

## Próximos Passos:

### 1. Atualizar Planos com IDs do Stripe
Execute no shell do Django (`python manage.py shell`):

```python
from apps.companies.models import SubscriptionPlan

# Starter
plan = SubscriptionPlan.objects.get(slug='starter')
plan.stripe_price_id_monthly = 'price_XXX'  # Substitua pelo ID real
plan.stripe_price_id_yearly = 'price_YYY'   # Substitua pelo ID real
plan.save()

# Professional
plan = SubscriptionPlan.objects.get(slug='professional')
plan.stripe_price_id_monthly = 'price_XXX'  # Substitua pelo ID real
plan.stripe_price_id_yearly = 'price_YYY'   # Substitua pelo ID real
plan.save()

# Enterprise
plan = SubscriptionPlan.objects.get(slug='enterprise')
plan.stripe_price_id_monthly = 'price_XXX'  # Substitua pelo ID real
plan.stripe_price_id_yearly = 'price_YYY'   # Substitua pelo ID real
plan.save()
```

### 2. Configurar Webhooks do Stripe
No dashboard do Stripe:
1. Vá para Developers > Webhooks
2. Adicione endpoint: `https://seudominio.com/api/payments/stripe/webhook/`
3. Selecione os eventos:
   - `checkout.session.completed`
   - `customer.subscription.created`
   - `customer.subscription.updated`
   - `customer.subscription.deleted`
   - `invoice.payment_succeeded`
   - `invoice.payment_failed`

### 3. Atualizar Variáveis de Ambiente
Adicione no `.env`:
```
STRIPE_WEBHOOK_SECRET=whsec_XXX  # Do dashboard do Stripe
```

### 4. Implementar Handlers de Webhook Faltantes
Os seguintes handlers precisam ser implementados em `/backend/apps/payments/views.py`:
- `checkout.session.completed`: Ativar assinatura após pagamento
- `customer.subscription.updated`: Atualizar status da assinatura
- `invoice.payment_failed`: Lidar com falhas de pagamento

## Como Funciona o Fluxo:

### Upgrade de Plano
1. Usuário clica em "Fazer Upgrade"
2. Sistema cria Stripe Checkout Session com o preço correto (mensal/anual)
3. Usuário é redirecionado para página de pagamento do Stripe
4. Após pagamento, webhook ativa a assinatura
5. Usuário é redirecionado de volta ao dashboard

### Downgrade de Plano
1. Sistema usa `update_subscription` com proration
2. Crédito é aplicado automaticamente na próxima fatura
3. Mudança acontece imediatamente

### Desconto Anual
- Stripe gerencia automaticamente quando você configura preços diferentes
- Sistema seleciona o `stripe_price_id_yearly` quando billing_cycle='yearly'
- Desconto de 16% já está configurado nos planos