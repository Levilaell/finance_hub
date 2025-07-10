# Guia de Integração Pluggy

Este documento descreve como configurar e testar a integração bancária com Pluggy no sistema Caixa Digital.

## Configuração

### 1. Variáveis de Ambiente

Adicione as seguintes variáveis ao arquivo `.env` do backend:

```bash
# Pluggy API Credentials
PLUGGY_CLIENT_ID=seu_client_id_aqui
PLUGGY_CLIENT_SECRET=seu_client_secret_aqui

# Optional: Pluggy API URL (default: https://api.pluggy.ai)
PLUGGY_BASE_URL=https://api.pluggy.ai

# Optional: Pluggy Connect URL (default: https://connect.pluggy.ai)
PLUGGY_CONNECT_URL=https://connect.pluggy.ai
```

### 2. Instalação de Dependências

As dependências já estão incluídas no `requirements.txt`:
- `httpx` - Cliente HTTP assíncrono
- `django-ratelimit` - Rate limiting para endpoints

## Arquitetura da Integração

### Backend

1. **Cliente Pluggy** (`pluggy_client.py`):
   - Cliente assíncrono para a API da Pluggy
   - Autenticação automática com tokens
   - Métodos para conectores, items, contas e transações

2. **Views Pluggy** (`pluggy_views.py`):
   - Endpoints REST para o frontend
   - Rate limiting configurado
   - Callbacks para Pluggy Connect

3. **Serviço de Sincronização** (`pluggy_sync_service.py`):
   - Sincronização de transações
   - Mapeamento de tipos de transação
   - Atualização de saldos

### Frontend

1. **Página de Contas** (`/accounts`):
   - Lista contas conectadas
   - Botão para conectar via Pluggy
   - Opções de sincronização manual

2. **Serviço Pluggy** (`pluggy.service.ts`):
   - Integração com Pluggy Connect
   - Gerenciamento de callbacks
   - Carregamento do SDK

3. **Handler de Conexão** (`pluggy-connect-handler.tsx`):
   - Escuta eventos do Pluggy Connect
   - Processa conexões bem-sucedidas
   - Tratamento de erros

## Fluxo de Conexão

### 1. Usuário Inicia Conexão

```typescript
// Frontend - accounts/page.tsx
const handleConnectBank = async (provider) => {
  const usePluggy = confirm('Conectar com banco real usando Pluggy?');
  
  const result = await bankingService.connectBankAccount({
    bank_code: provider.code,
    use_pluggy: usePluggy
  });
  
  if (result.data?.status === 'pluggy_connect_required') {
    // Abre Pluggy Connect
    const pluggyUrl = `${result.data.connect_url}?connectToken=${result.data.connect_token}`;
    window.open(pluggyUrl, '_blank');
  }
};
```

### 2. Usuário Completa Conexão no Pluggy

O usuário:
1. Seleciona o banco
2. Insere credenciais
3. Completa autenticação (MFA se necessário)
4. Pluggy cria o "item"

### 3. Callback Processa Conexão

```python
# Backend - pluggy_views.py
class PluggyItemCallbackView(APIView):
    def post(self, request):
        item_id = request.data.get('item_id')
        
        # Busca dados do item
        item = await client.get_item(item_id)
        
        # Busca contas
        accounts = await client.get_accounts(item_id)
        
        # Cria contas no banco de dados
        for account_data in accounts:
            BankAccount.objects.create(
                company=company,
                pluggy_item_id=item_id,
                external_account_id=account_data['id'],
                # ... outros campos
            )
```

### 4. Sincronização de Transações

```python
# Backend - pluggy_sync_service.py
class PluggySyncService:
    def sync_account_transactions(self, account):
        # Busca transações da Pluggy
        transactions = await client.get_transactions(
            account.external_account_id,
            from_date=last_sync_date,
            to_date=today
        )
        
        # Processa e salva transações
        for tx_data in transactions:
            Transaction.objects.create(
                bank_account=account,
                external_id=tx_data['id'],
                # ... mapeamento de campos
            )
```

## Endpoints da API

### Bancos Disponíveis
```
GET /api/banking/pluggy/banks/
```

### Criar Token de Conexão
```
POST /api/banking/pluggy/connect-token/
```

### Callback de Conexão
```
POST /api/banking/pluggy/callback/
{
  "item_id": "item-123",
  "connector_name": "Banco do Brasil"
}
```

### Sincronizar Conta
```
POST /api/banking/pluggy/accounts/{account_id}/sync/
```

### Status da Conta
```
GET /api/banking/pluggy/accounts/{account_id}/status/
```

### Desconectar Conta
```
DELETE /api/banking/pluggy/accounts/{account_id}/disconnect/
```

## Testando a Integração

### 1. Teste Manual do Cliente

```bash
cd backend
python test_pluggy_connection.py
```

Este script testa:
- Autenticação com Pluggy
- Listagem de bancos
- Criação de token

### 2. Testes Unitários

```bash
# Testes do cliente Pluggy
python manage.py test apps.banking.tests.test_pluggy_integration

# Testes do serviço de sincronização
python manage.py test apps.banking.tests.test_pluggy_sync

# Testes do fluxo completo
python manage.py test apps.banking.tests.test_connect_flow
```

### 3. Teste no Frontend

1. Acesse `/accounts`
2. Clique em "Conectar via Open Banking"
3. Selecione um banco
4. Clique em "Conectar com [Banco]"
5. Complete o fluxo no Pluggy Connect

## Modo Desenvolvimento

Para desenvolvimento sem credenciais Pluggy:

1. O sistema usa dados mockados quando as credenciais não estão configuradas
2. Bancos de teste são retornados
3. Conexões simuladas são criadas

## Tratamento de Erros

### Erros Comuns

1. **Token Expirado**:
   - O sistema renova automaticamente
   - Se falhar, usuário precisa reconectar

2. **Credenciais Inválidas**:
   - Pluggy Connect mostra erro
   - Usuário pode tentar novamente

3. **Banco Indisponível**:
   - Verificar status em `health_status`
   - Informar usuário sobre indisponibilidade

### Logs

Logs importantes para debug:

```python
# Backend
logger.info(f"Pluggy item created: {item_id}")
logger.error(f"Error syncing account {account_id}: {e}")

# Frontend
console.log('Pluggy event:', event.data);
console.error('Error processing Pluggy item:', error);
```

## Webhooks (Opcional)

Para atualizações em tempo real, configure webhooks:

```python
# Criar webhook
await client.create_webhook(
    url='https://seu-dominio.com/api/banking/pluggy/webhook/',
    events=['item/updated', 'transactions/created']
)
```

## Segurança

1. **Tokens**: Nunca exponha tokens no frontend
2. **HTTPS**: Sempre use HTTPS em produção
3. **Rate Limiting**: Configurado nos endpoints
4. **Validação**: Sempre valide item_id pertence ao usuário

## Suporte

- Documentação Pluggy: https://docs.pluggy.ai/
- Dashboard Pluggy: https://dashboard.pluggy.ai/
- Suporte: support@pluggy.ai