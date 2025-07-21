# Investigação do Webhook Pluggy - Resultados

## Problema Identificado

O webhook não estava sincronizando as transações quando recebia o evento `transactions/created` devido a um erro no código.

### Erro Encontrado

No arquivo `pluggy_views.py`, linha 564, o código estava chamando:
```python
await sync_service.sync_account(account.id)
```

Mas o método correto é:
```python
await sync_service.sync_account_transactions(account)
```

## Correção Aplicada

✅ O erro foi corrigido no arquivo `/apps/banking/pluggy_views.py`

## Comandos de Debug Criados

Para ajudar na investigação e testes futuros, foram criados os seguintes comandos:

### 1. `debug_webhook_sync.py`
Debug completo de contas e webhooks:
```bash
# Debug uma conta específica
python manage.py debug_webhook_sync --account-id <ID>

# Verificar configuração do webhook na Pluggy
python manage.py debug_webhook_sync --account-id <ID> --check-webhook

# Verificar status do item na Pluggy
python manage.py debug_webhook_sync --account-id <ID> --check-item

# Forçar sincronização manual
python manage.py debug_webhook_sync --account-id <ID> --sync-now
```

### 2. `test_webhook_production.py`
Testar webhook com dados reais de produção:
```bash
# Testar evento de novas transações
python manage.py test_webhook_production --account-id <ID>

# Testar outros eventos
python manage.py test_webhook_production --account-id <ID> --event item/updated
python manage.py test_webhook_production --account-id <ID> --event account/updated

# Usar URL customizada
python manage.py test_webhook_production --account-id <ID> --webhook-url https://seu-dominio.com/api/banking/pluggy/webhook/
```

## Checklist de Verificação

Para garantir que o webhook está funcionando corretamente:

### 1. Verificar Configuração do Webhook
```bash
# Configurar/atualizar webhook
python manage.py setup_pluggy_webhook --force
```

### 2. Verificar Variáveis de Ambiente
Certifique-se de que as seguintes variáveis estão configuradas:
- `PLUGGY_WEBHOOK_SECRET`: Secret fornecido pela Pluggy para validar assinatura
- `BACKEND_URL`: URL pública do backend (em produção)

### 3. Verificar Conta Bancária
A conta deve ter:
- `external_id`: ID da conta na Pluggy
- `pluggy_item_id`: ID do item (conexão) na Pluggy
- `is_active`: True
- `status`: 'active'

### 4. Testar Webhook Localmente
```bash
# Simular evento de transações
python manage.py test_pluggy_webhook transactions/created --account-id <external_id_da_conta>
```

### 5. Verificar Logs
```bash
# Em produção, verificar logs do webhook
tail -f logs/django.log | grep "Pluggy webhook"
```

## Fluxo Correto do Webhook

1. **Pluggy envia webhook** → Backend recebe em `/api/banking/pluggy/webhook/`
2. **Verificação de assinatura** → Valida `X-Pluggy-Signature` com HMAC-SHA256
3. **Processamento do evento**:
   - Para `transactions/created`:
     - Busca conta pelo `external_id` (accountId do evento)
     - Chama `sync_account_transactions(account)`
     - Sincroniza transações e atualiza saldo
4. **Resposta** → HTTP 200 (sucesso) ou 500 (erro)

## Próximos Passos

1. **Testar em produção** após o deploy da correção
2. **Monitorar logs** para confirmar que webhooks estão chegando
3. **Verificar sincronização automática** quando novas transações aparecerem
4. **Considerar implementar**:
   - Retry logic para falhas temporárias
   - Métricas de sucesso/falha de webhooks
   - Alertas para falhas recorrentes

## Comandos Úteis para Produção

```bash
# Verificar status de todas as contas Pluggy
python manage.py debug_webhook_sync

# Forçar sincronização de uma conta específica
python manage.py debug_webhook_sync --account-id <ID> --sync-now

# Testar webhook manualmente
python manage.py test_webhook_production --account-id <ID>
```