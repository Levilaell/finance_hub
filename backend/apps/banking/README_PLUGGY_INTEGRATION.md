# Integração Pluggy - Documentação

## Visão Geral

Esta documentação descreve a implementação da integração com a API Pluggy para extração de transações bancárias.

## Funcionalidades Implementadas

### 1. Handlers de Erro Específicos (`pluggy_error_handlers.py`)

Implementamos handlers específicos para cada tipo de erro da API Pluggy:

- **Erros de Autenticação**: `INVALID_CREDENTIALS`, `LOGIN_ERROR`
- **Erros de Autorização Open Finance**: `USER_AUTHORIZATION_NOT_GRANTED`, `USER_AUTHORIZATION_REVOKED`, `CONSENT_EXPIRED`
- **Erros de Rate Limit**: `RATE_LIMIT_EXCEEDED`, `423` (HTTP Locked)
- **Erros de Conectividade**: `CONNECTION_ERROR`, `TIMEOUT`, `SERVICE_UNAVAILABLE`
- **Erros de Dados**: `PARTIAL_SUCCESS`, `PRODUCT_NOT_AVAILABLE`

Cada handler retorna uma ação recomendada:
- `retry_immediately`: Para erros temporários de conexão
- `retry_with_backoff`: Para rate limits (respeita limites mensais do Open Finance)
- `require_user_action`: Para erros que necessitam reautenticação
- `renew_consent`: Para consentimentos expirados (renovação automática)

### 2. Renovação Automática de Consentimentos (`consent_renewal_service.py`)

Sistema automático para renovar consentimentos antes da expiração:

- **Verificação Diária**: Task Celery executada às 8h
- **Detecção Proativa**: Identifica consentimentos expirando em 7 dias
- **Renovação Automática**: Usa `update_item` da API Pluggy
- **Notificações**: Alerta usuários quando ação manual é necessária

### 3. Sincronização Otimizada de Transações

#### Fluxo de Sincronização:

1. **Primeira Sincronização**:
   - Open Finance: 365 dias (1 ano completo)
   - Sandbox: 365 dias
   - Produção/Trial: 90 dias (3 meses)

2. **Sincronizações Incrementais**:
   - Open Finance (< 24h): 1 dia (minimizar uso de rate limit)
   - Open Finance (< 7 dias): 7 dias
   - Open Finance (> 7 dias): 30 dias
   - Outros conectores: Janela adaptativa baseada na última sync

3. **Rate Limiting**:
   - Máximo 3 contas sincronizando simultaneamente
   - Delay de 0.5s entre sincronizações
   - Respeito aos limites mensais do Open Finance

#### Tratamento de Erros na Sincronização:

- Erros Pluggy são capturados e processados pelos handlers
- Status da conta é atualizado automaticamente
- Renovação de consentimento é agendada quando necessário
- Retry automático com backoff exponencial

## Configuração

### Variáveis de Ambiente Necessárias:

```env
# Credenciais Pluggy
PLUGGY_CLIENT_ID=seu_client_id
PLUGGY_CLIENT_SECRET=seu_client_secret
PLUGGY_BASE_URL=https://api.pluggy.ai
PLUGGY_CONNECT_URL=https://connect.pluggy.ai
PLUGGY_USE_SANDBOX=False

# Importante: Configurar no dashboard da Pluggy
PLUGGY_WEBHOOK_SECRET=seu_webhook_secret
PLUGGY_WEBHOOK_URL=https://seu-dominio.com/api/banking/pluggy/webhook/
```

### Tasks Celery Configuradas:

```python
# Sincronização de contas (a cada 4 horas)
'sync-pluggy-accounts': {
    'task': 'apps.banking.tasks.sync_all_pluggy_accounts',
    'schedule': crontab(minute=0, hour='*/4'),
}

# Verificação de consentimentos (diária às 8h)
'check-and-renew-consents': {
    'task': 'apps.banking.tasks.check_and_renew_consents',
    'schedule': crontab(hour=8, minute=0),
}
```

## Webhooks

Os webhooks processam eventos em tempo real:

- `item/created`: Nova conexão criada
- `item/updated`: Status da conexão atualizado
- `item/error`: Erro na conexão
- `transactions/created`: Novas transações disponíveis
- `item/waiting_user_action`: Reautenticação necessária

## Fluxo de Conexão Bancária

1. **Usuário inicia conexão**: Frontend solicita token via `/api/banking/pluggy/connect-token/`
2. **Pluggy Connect Widget**: Usuário autentica no banco
3. **Callback de sucesso**: Item criado, webhook recebido
4. **Sincronização inicial**: Busca transações do período configurado
5. **Sincronizações periódicas**: A cada 4 horas via Celery

## Melhores Práticas

1. **Sempre verificar status do item antes de sincronizar**
2. **Respeitar rate limits, especialmente para Open Finance**
3. **Usar janelas de tempo apropriadas para cada tipo de sync**
4. **Monitorar logs para identificar padrões de erro**
5. **Configurar webhook secret para segurança**

## Troubleshooting

### Erro: "Rate limit exceeded"
- Open Finance tem limite mensal por consentimento
- Aguardar próximo mês ou reduzir frequência de sync

### Erro: "Consent expired"
- Sistema tentará renovar automaticamente
- Se falhar, usuário precisará reconectar manualmente

### Erro: "Invalid credentials"
- Usuário precisa atualizar credenciais no banco
- Notificação será enviada automaticamente

## Próximos Passos

1. Implementar notificações por email/push
2. Adicionar suporte para Credit Card Bills
3. Implementar dashboard de monitoramento de erros
4. Adicionar métricas de sucesso de sincronização