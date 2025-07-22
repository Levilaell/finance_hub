# 🔧 Integrações Pendentes

## Funcionalidades Criadas mas Não Totalmente Integradas

### 1. **Increment Usage Safe** (`security_fixes.py`)
```python
# Substituir em transaction create/update:
company.current_month_transactions += 1  # ATUAL
# Por:
from apps.payments.security_fixes import UsageLimitsFixes
if not UsageLimitsFixes.increment_usage_safe(company, 'transactions'):
    return error_response
```

### 2. **Retry com Backoff** (`security_fixes.py`)
```python
# Usar em operações críticas:
from apps.payments.security_fixes import WebhookRetry
result = WebhookRetry.retry_with_backoff(
    lambda: stripe.checkout.Session.retrieve(session_id),
    max_retries=3
)
```

### 3. **Cache de Limites** (`security_fixes.py`)
```python
# No middleware ou views:
from apps.payments.security_fixes import UsageLimitsCache
limits = UsageLimitsCache.get_cached_limits(company.id)
# Após atualizar uso:
UsageLimitsCache.invalidate_cache(company.id)
```

### 4. **Funções Helper não Usadas** (`webhook_improvements.py`)
- `get_checkout_session_details()` - Poderia ser usada em mais lugares
- Classes de handlers poderiam ser importadas no payment_service

### 5. **Monitoramento Avançado**
Adicionar integração com:
- Sentry para erros
- Datadog/New Relic para métricas
- Slack/Discord para alertas críticos

### 6. **Índices do Banco**
Criar índices para queries frequentes:
```sql
CREATE INDEX idx_company_subscription_status ON companies_company(subscription_status);
CREATE INDEX idx_company_trial_ends ON companies_company(trial_ends_at);
CREATE INDEX idx_payment_history_company_date ON companies_paymenthistory(company_id, transaction_date);
```

### 7. **Testes Unitários**
Criar testes para:
- Todos os novos handlers de webhook
- Lógica de proration
- Rate limiting
- Idempotency

## 📝 Como Implementar

1. **Para o increment_usage_safe**: Buscar todos os lugares que incrementam contadores
2. **Para retry logic**: Aplicar em todas as chamadas para APIs externas
3. **Para cache**: Integrar no middleware e invalidar quando necessário
4. **Para monitoramento**: Configurar serviços externos e adicionar hooks

## 🎯 Prioridade

1. 🔴 **Alta**: Increment usage safe (evita race conditions)
2. 🟡 **Média**: Cache de limites (performance)
3. 🟢 **Baixa**: Retry logic (já tem logs, pode fazer retry manual)