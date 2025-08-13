# Correções do Sistema de Pagamentos e Assinaturas

## 🚀 Resumo das Correções Aplicadas

### 1. **Sincronização de Preços** ✅
- **Problema**: Preços desincronizados entre backend (R$ 29,90), frontend (R$ 49) e Stripe (R$ 49)
- **Solução**: Padronizado todos os preços para R$ 49/149/349
- **Arquivos Modificados**:
  - `backend/apps/companies/management/commands/create_subscription_plans.py`
  - `frontend/app/pricing/page.tsx`

### 2. **IDs de Preço do Stripe** ✅
- **Problema**: Sistema criava preços dinamicamente ao invés de usar IDs pré-configurados
- **Solução**: Implementado uso de price IDs do Stripe (price_1RnPVfPFS...)
- **Arquivos Modificados**:
  - `backend/apps/payments/services/payment_gateway.py`
  - `backend/apps/payments/services/subscription_service.py`
  - `backend/apps/companies/models.py` (adicionados métodos helper)

### 3. **Metadata de Webhooks** ✅
- **Problema**: Webhook procurava `subscription_metadata` mas checkout criava apenas `metadata`
- **Solução**: Corrigido para procurar metadata em múltiplos locais
- **Arquivo Modificado**:
  - `backend/apps/payments/services/webhook_handler.py`

### 4. **Validações de Limites** ✅
- **Problema**: Não havia validação consistente de limites do plano
- **Solução**: Implementadas validações robustas, especialmente para downgrade
- **Arquivo Modificado**:
  - `backend/apps/payments/services/subscription_service.py`

### 5. **Fluxo de Downgrade** ✅
- **Problema**: Downgrade não validava se dados excediam limites do novo plano
- **Solução**: Adicionado método `validate_downgrade()` com verificações completas
- **Arquivo Modificado**:
  - `backend/apps/payments/services/subscription_service.py`

## 📋 Como Aplicar as Correções

### Passo 1: Atualizar os Planos no Banco de Dados

```bash
# Opção 1: Criar planos do zero (se não existirem)
python manage.py create_subscription_plans

# Opção 2: Sincronizar planos existentes (recomendado)
python manage.py sync_subscription_plans --dry-run  # Ver o que será mudado
python manage.py sync_subscription_plans           # Aplicar mudanças
```

### Passo 2: Verificar Configuração

```bash
# Verificar planos no Django shell
python manage.py shell
```

```python
from apps.companies.models import SubscriptionPlan

# Verificar preços
for plan in SubscriptionPlan.objects.all():
    print(f"{plan.name}:")
    print(f"  Monthly: R$ {plan.price_monthly} - ID: {plan.stripe_price_id_monthly}")
    print(f"  Yearly: R$ {plan.price_yearly} - ID: {plan.stripe_price_id_yearly}")
    print(f"  Has Stripe IDs: {plan.has_stripe_ids()}")
```

### Passo 3: Testar Fluxos

#### Teste de Criação de Assinatura
```bash
# 1. Acessar página de preços
http://localhost:3000/pricing

# 2. Selecionar plano e criar checkout
# 3. Verificar logs do backend para confirmar uso de price IDs
tail -f logs/django.log | grep "Using Stripe price ID"
```

#### Teste de Upgrade/Downgrade
```python
# No Django shell
from apps.payments.services.subscription_service import SubscriptionService
from apps.companies.models import Company, SubscriptionPlan

company = Company.objects.get(id=1)
new_plan = SubscriptionPlan.objects.get(slug='professional')

# Testar validação de downgrade
can_downgrade, reason = SubscriptionService.validate_downgrade(
    company, 
    company.subscription.plan, 
    new_plan
)
print(f"Can downgrade: {can_downgrade}")
print(f"Reason: {reason}")
```

## 🔍 Verificações de Integridade

### 1. Verificar Sincronização de Preços

```sql
-- No PostgreSQL
SELECT name, price_monthly, price_yearly, 
       stripe_price_id_monthly, stripe_price_id_yearly
FROM subscription_plans
ORDER BY display_order;
```

Valores esperados:
| Plano | Mensal | Anual | ID Mensal | ID Anual |
|-------|--------|-------|-----------|----------|
| Starter | 49.00 | 490.00 | price_1RkePtPFS... | price_1RnPVfPFS... |
| Professional | 149.00 | 1490.00 | price_1RkeQgPFS... | price_1RnPVRPFS... |
| Enterprise | 349.00 | 3490.00 | price_1RkeMJPFS... | price_1RnPV8PFS... |

### 2. Verificar Webhooks

```bash
# Monitorar webhooks em tempo real
tail -f logs/webhooks.log

# Verificar processamento de checkout.session.completed
grep "checkout.session.completed" logs/webhooks.log
```

### 3. Verificar Limites de Uso

```python
# No Django shell
from apps.companies.models import Company

company = Company.objects.get(id=1)
usage = company.get_usage_summary()
print(usage)

# Saída esperada:
# {
#   'transactions': {'used': 150, 'limit': 500, 'percentage': 30.0},
#   'ai_requests': {'used': 0, 'limit': 0, 'percentage': 0},
#   'bank_accounts': {'used': 1, 'limit': 1, 'percentage': 100.0}
# }
```

## ⚠️ Pontos de Atenção

1. **Ambientes de Produção**: 
   - Certifique-se de que os IDs de preço correspondem ao ambiente (test/live)
   - Use `stripe_test_clock` para testar ciclos de billing

2. **Migrações Existentes**:
   - Se já existem assinaturas ativas, cuidado ao alterar preços
   - Considere grandfathering para clientes existentes

3. **Cache**:
   - Limpe o cache após atualizar planos
   ```bash
   python manage.py clear_cache
   redis-cli FLUSHDB  # Se usar Redis
   ```

4. **Monitoramento**:
   - Configure alertas para falhas de webhook
   - Monitore taxa de conversão de checkout
   - Acompanhe métricas de downgrade

## 📊 Métricas de Sucesso

Após aplicar as correções, você deve observar:

- ✅ 100% dos checkouts usando price IDs do Stripe
- ✅ 0 erros de metadata em webhooks
- ✅ 0 downgrades inválidos (excedendo limites)
- ✅ Preços consistentes em todas as camadas
- ✅ Logs mostrando "Using Stripe price ID" ao invés de "using dynamic pricing"

## 🆘 Troubleshooting

### Problema: "No Stripe price ID for plan"
**Solução**: Execute `python manage.py sync_subscription_plans`

### Problema: "Missing metadata in checkout session"
**Solução**: Verifique se o webhook está recebendo eventos completos do Stripe

### Problema: "Downgrade not allowed: Current transactions exceed limit"
**Solução**: Este é o comportamento esperado. Oriente o usuário a reduzir uso antes do downgrade

### Problema: Preços ainda desincronizados
**Solução**: 
1. Verificar cache do frontend: `npm run build`
2. Limpar cache do Django: `python manage.py clear_cache`
3. Reiniciar servidores

## 📝 Próximos Passos Recomendados

1. **Implementar Feature Flags**: Sistema dinâmico de features baseado em planos
2. **Adicionar Métricas**: Dashboard de conversão e churn
3. **Melhorar UX de Limites**: Mostrar barras de progresso de uso
4. **Implementar Grandfathering**: Proteger planos antigos de clientes existentes
5. **Adicionar Testes E2E**: Testes automatizados de todo o fluxo de pagamento