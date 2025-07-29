# Banking App - Integração Pluggy

## Visão Geral

O app Banking do CaixaHub integra com a API da Pluggy para conectar contas bancárias via Open Banking, sincronizar transações e fornecer insights financeiros automatizados.

## Funcionalidades Implementadas

### 1. Autenticação e Tokens
- ✅ Autenticação com CLIENT_ID/CLIENT_SECRET
- ✅ Cache de API key por 23 horas
- ✅ Refresh automático de tokens expirados
- ✅ Geração de Connect Token para widget

### 2. Conexões Bancárias (Items)
- ✅ Criação de conexões via Pluggy Connect
- ✅ Suporte a OAuth para Open Finance
- ✅ Atualização de credenciais (LOGIN_ERROR)
- ✅ Suporte a MFA (Multi-Factor Authentication)
- ✅ Exclusão de conexões com revogação de consentimento

### 3. Sincronização de Dados
- ✅ Sincronização manual e automática
- ✅ Retry logic para erros temporários
- ✅ Paginação de transações
- ✅ Tratamento de erros por conta/transação
- ✅ Histórico detalhado de sincronizações

### 4. Webhooks
- ✅ Endpoint para receber notificações da Pluggy
- ✅ Validação de assinatura webhook
- ✅ Processamento assíncrono de eventos
- ✅ Suporte a eventos: item/updated, item/error, transactions/*

### 5. Open Finance
- ✅ Suporte a fluxo OAuth
- ✅ Modelo de Consent para gerenciar consentimentos
- ✅ Verificação de validade de consentimento
- ✅ Atualização automática de consent durante sync

### 6. Categorização
- ✅ Uso de categorias fornecidas pela Pluggy
- ✅ Suporte a categorias customizadas
- ✅ Bulk categorization de transações

## Endpoints da API

### Conexões Bancárias
- `POST /api/banking/connections/create_connect_token/` - Criar token para widget
- `POST /api/banking/connections/create_from_item/` - Criar conexão de item existente
- `POST /api/banking/connections/{id}/sync/` - Sincronizar manualmente
- `POST /api/banking/connections/{id}/update_credentials/` - Atualizar credenciais
- `POST /api/banking/connections/{id}/update_mfa/` - Enviar código MFA
- `GET /api/banking/connections/{id}/consent/` - Ver detalhes do consentimento
- `DELETE /api/banking/connections/{id}/` - Deletar conexão

### Webhooks
- `POST /api/banking/webhooks/pluggy/` - Receber notificações da Pluggy

## Configurações Necessárias

```python
# .env
PLUGGY_CLIENT_ID=seu_client_id
PLUGGY_CLIENT_SECRET=seu_client_secret
PLUGGY_BASE_URL=https://api.pluggy.ai
PLUGGY_USE_SANDBOX=True  # False em produção
PLUGGY_WEBHOOK_SECRET=seu_webhook_secret
BACKEND_URL=https://api.caixahub.com.br  # Para webhooks
```

## Fluxo de Integração

### 1. Conectar Conta Bancária
```javascript
// Frontend
1. Solicitar Connect Token
2. Abrir Pluggy Connect Widget
3. Usuário autentica no banco
4. Receber itemId no callback
5. Criar conexão no backend
```

### 2. Sincronização Automática
- Webhooks notificam mudanças em tempo real
- Task periódica verifica conexões a cada 12 horas
- Retry automático para erros temporários

### 3. Tratamento de Erros
- **LOGIN_ERROR**: Solicitar novas credenciais via widget
- **WAITING_USER_INPUT**: Solicitar código MFA
- **OUTDATED**: Retry automático até 2 vezes
- **ERROR**: Log detalhado e notificação

## Modelos de Dados

### BankConnection
- Representa uma conexão com instituição financeira
- Mapeia para Item na Pluggy
- Estados: UPDATING, UPDATED, LOGIN_ERROR, etc.

### Account
- Conta bancária ou cartão de crédito
- Sincroniza saldo e metadados

### Transaction
- Transação financeira
- Categorização automática via Pluggy
- Suporte a categorias customizadas

### Consent
- Consentimento Open Finance
- Produtos autorizados
- Validade e revogação

## Tasks Celery

### sync_bank_connection
- Sincroniza uma conexão específica
- Retry logic para erros temporários
- Atualiza accounts, transactions e consent

### auto_sync_connections
- Executa a cada 12 horas
- Sincroniza conexões elegíveis

### process_webhook_event
- Processa eventos webhook assincronamente
- Trigger sincronizações conforme necessário

## Melhores Práticas

1. **Segurança**
   - Nunca expor CLIENT_SECRET no frontend
   - Validar webhooks com assinatura
   - HTTPS obrigatório para OAuth redirect

2. **Performance**
   - Cache de API key
   - Paginação de transações
   - Processamento assíncrono

3. **Confiabilidade**
   - Retry logic para erros temporários
   - Histórico detalhado de sincronizações
   - Tratamento gracioso de erros

## Troubleshooting

### Conexão não sincroniza
1. Verificar status da conexão
2. Checar logs de sincronização
3. Validar credenciais na Pluggy

### Webhook não funciona
1. Verificar URL configurada
2. Validar assinatura webhook
3. Checar logs do Celery

### Erro de autenticação
1. Verificar CLIENT_ID/SECRET
2. Limpar cache de API key
3. Verificar ambiente (sandbox/produção)