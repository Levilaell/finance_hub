# Banking Module - Pluggy Integration

## Visão Geral

Sistema de integração bancária com a API da Pluggy para conectar contas bancárias, sincronizar transações e calcular relatórios financeiros.

## Arquivos Principais

### 1. `pluggy_client.py`
Cliente para comunicação com a API da Pluggy. Gerencia autenticação e requisições.
- **Referência**: https://docs.pluggy.ai/docs/authentication

### 2. `models.py`
Modelos Django para armazenar dados bancários:
- `Connector`: Instituições financeiras disponíveis
- `BankConnection`: Conexões dos usuários com bancos
- `BankAccount`: Contas bancárias
- `Transaction`: Transações financeiras
- `SyncLog`: Logs de sincronização
- **Referência**: https://docs.pluggy.ai/docs/data-structure

### 3. `services.py`
Lógica de negócio para sincronização:
- `ConnectorService`: Gerencia conectores bancários
- `BankConnectionService`: Gerencia conexões e contas
- `TransactionService`: Sincroniza e analisa transações
- **Referência**: https://docs.pluggy.ai/docs/creating-an-use-case-from-scratch

### 4. `views.py`
Endpoints da API REST:
- `/api/banking/connectors/` - Listar bancos disponíveis
- `/api/banking/connections/` - Gerenciar conexões bancárias
- `/api/banking/accounts/` - Visualizar contas
- `/api/banking/transactions/` - Acessar transações
- **Referência**: https://docs.pluggy.ai/reference/

### 5. `webhooks.py`
Handlers para notificações em tempo real da Pluggy.
- **Referência**: https://docs.pluggy.ai/docs/webhooks

## Configuração

### 1. Variáveis de Ambiente

```bash
# .env
PLUGGY_CLIENT_ID=seu-client-id
PLUGGY_CLIENT_SECRET=seu-client-secret
PLUGGY_API_URL=https://api.pluggy.ai
PLUGGY_WEBHOOK_SECRET=seu-webhook-secret
WEBHOOK_BASE_URL=https://seudominio.com
```

### 2. Aplicar Migrações

```bash
python manage.py migrate banking
```

### 3. Sincronizar Conectores

```bash
# Via Django Admin ou API
POST /api/banking/connectors/sync/
```

## Fluxo de Uso

### 1. Conectar Banco

```python
# Frontend obtém token
GET /api/banking/connections/connect_token/

# Criar conexão
POST /api/banking/connections/
{
    "connector_id": 201,  # ID do banco
    "credentials": {
        "user": "12345678900",
        "password": "senha123"
    }
}
```

### 2. Sincronizar Dados

```python
# Sincronizar contas
POST /api/banking/connections/{id}/sync_accounts/

# Sincronizar transações
POST /api/banking/connections/{id}/sync_transactions/
```

### 3. Visualizar Dados

```python
# Listar contas
GET /api/banking/accounts/

# Listar transações
GET /api/banking/transactions/?date_from=2024-01-01&date_to=2024-12-31

# Resumo financeiro
GET /api/banking/transactions/summary/
```

## Webhooks

Configure a URL de webhook no Pluggy Dashboard apontando para:
```
https://seudominio.com/api/banking/webhooks/pluggy/
```

Eventos tratados:
- `item/created` - Conexão criada
- `item/updated` - Dados atualizados
- `item/error` - Erro na conexão
- `item/waiting_user_input` - MFA requerido

## Segurança

- Autenticação via API Keys (expiram em 2h)
- Connect Tokens para frontend (expiram em 30min)
- Verificação de assinatura em webhooks
- Soft delete para manter histórico

## Referências Principais

- **Documentação Pluggy**: https://docs.pluggy.ai/
- **API Reference**: https://docs.pluggy.ai/reference/
- **Autenticação**: https://docs.pluggy.ai/docs/authentication
- **Webhooks**: https://docs.pluggy.ai/docs/webhooks
- **Conectores**: https://docs.pluggy.ai/reference/connectors
- **Items (Conexões)**: https://docs.pluggy.ai/reference/items
- **Contas**: https://docs.pluggy.ai/reference/accounts
- **Transações**: https://docs.pluggy.ai/reference/transactions

## Próximos Passos

1. Implementar notificações para MFA
2. Adicionar cache para otimizar performance
3. Implementar categorização automática de transações
4. Criar dashboards e relatórios visuais no frontend
5. Adicionar suporte para múltiplas moedas