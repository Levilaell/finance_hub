# Correções Necessárias no Sistema de Pagamentos

## 🚨 Problemas Críticos Encontrados

### 1. **Webhook Events Faltando**
O sistema não está processando eventos importantes do Stripe:

```python
# Adicionar ao payment_service.py:
elif event_type == 'invoice.payment_succeeded':
    self._handle_invoice_payment_succeeded(event_data['data'])
elif event_type == 'customer.subscription.trial_will_end':
    self._handle_subscription_trial_will_end(event_data['data'])
elif event_type == 'payment_method.attached':
    self._handle_payment_method_attached(event_data['data'])
elif event_type == 'charge.failed':
    self._handle_charge_failed(event_data['data'])
```

### 2. **Dados do Cartão Não Salvos**
O webhook tenta acessar `payment_method_details` que não existe no evento:

```python
# Correção no _handle_checkout_completed:
# Buscar detalhes da sessão expandida
from .webhook_improvements import get_checkout_session_details
details = get_checkout_session_details(session.get('id'))
if details.get('payment_method'):
    # Salvar método de pagamento
```

### 3. **Cancelamento Não Integrado**
O cancelamento só atualiza o banco local:

```python
# Adicionar ao CancelSubscriptionView:
payment_service = PaymentService()
payment_service.cancel_subscription(company.subscription_id)
```

### 4. **Idempotency Check Faltando**
Webhooks podem ser processados múltiplas vezes:

```python
# Adicionar ao stripe_webhook view:
from .security_fixes import WebhookSecurity
if not WebhookSecurity.check_idempotency(event['id'], event['type']):
    return Response({'status': 'already_processed'})
```

### 5. **Rate Limiting Insuficiente**
Adicionar rate limiting para AI e outras operações:

```python
# No middleware antes de incrementar uso:
from .security_fixes import UsageLimitsFixes
if not UsageLimitsFixes.check_rate_limit(request.user.id, 'ai_request'):
    return JsonResponse({'error': 'Too many requests'}, status=429)
```

### 6. **Trial Check Ineficiente**
O middleware verifica trial em cada request:

```python
# Mover para task Celery (apps/companies/tasks.py):
@shared_task
def check_and_expire_trials():
    from apps.payments.payment_service import PaymentService
    service = PaymentService()
    service.check_trial_expiration()
```

### 7. **Proration Não Implementada**
Upgrade/downgrade não calcula valores proporcionais:

```python
# Adicionar ao UpgradeSubscriptionView:
from .security_fixes import SubscriptionValidation
proration = SubscriptionValidation.calculate_proration(
    company, new_plan, billing_cycle
)
```

### 8. **Histórico Incompleto**
Renovações não geram histórico:

```python
# Implementar handler invoice.payment_succeeded
# Ver webhook_improvements.py
```

## 📋 Checklist de Implementação

- [ ] Adicionar handlers para eventos faltantes
- [ ] Implementar idempotency check
- [ ] Integrar cancelamento com Stripe
- [ ] Adicionar rate limiting
- [ ] Mover trial check para Celery
- [ ] Implementar cálculo de proration
- [ ] Corrigir salvamento de métodos de pagamento
- [ ] Adicionar logs detalhados para auditoria

## 🔒 Melhorias de Segurança

1. **Validar metadata dos webhooks**
2. **Usar transações atômicas**
3. **Implementar retry com backoff**
4. **Adicionar monitoramento de falhas**
5. **Criar alerts para pagamentos falhos**

## ⚡ Performance

1. **Cache de limites de uso**
2. **Bulk operations para reset mensal**
3. **Índices no banco para queries frequentes**
4. **Queue para processamento assíncrono**