# Implementação de Reconexão para WAITING_USER_ACTION

## Visão Geral

Implementamos um fluxo completo para lidar com situações onde o banco exige reautenticação do usuário (WAITING_USER_ACTION). Isso resolve o problema de sincronização quando Items ficam OUTDATED.

## Novos Endpoints

### 1. Verificar Status da Conta
```
GET /api/banking/pluggy/accounts/{account_id}/status/
```

**Resposta quando precisa reconexão:**
```json
{
  "success": true,
  "data": {
    "account_id": 28,
    "external_id": "0414b113-227f-472c-aae2-b48bf4b4f0d1",
    "status": "active",
    "item_status": "WAITING_USER_ACTION",
    "item_error": null,
    "needs_reconnection": true,
    "reconnection_message": "O banco está solicitando que você faça login novamente para continuar sincronizando.",
    "reconnection_url": "/api/banking/pluggy/accounts/28/reconnect/",
    "last_sync": "2025-07-23T02:00:00Z",
    "balance": 1234.56
  }
}
```

### 2. Gerar Token de Reconexão
```
POST /api/banking/pluggy/accounts/{account_id}/reconnect/
```

**Resposta:**
```json
{
  "success": true,
  "data": {
    "connect_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "connect_url": "https://connect.pluggy.ai",
    "item_id": "a0beeaac-806b-410f-b814-fbb8fe517d54",
    "current_status": "WAITING_USER_ACTION",
    "expires_at": "2025-07-23T03:30:00Z",
    "message": "Use este token para reconectar sua conta bancária"
  }
}
```

### 3. Resposta de Erro na Sincronização
Quando a sincronização falha por WAITING_USER_ACTION:

```json
{
  "success": false,
  "error": "Reautenticação necessária",
  "error_code": "WAITING_USER_ACTION",
  "message": "O banco está solicitando que você faça login novamente. Por favor, reconecte sua conta.",
  "reconnection_required": true,
  "reconnection_url": "/api/banking/pluggy/accounts/28/reconnect/"
}
```

## Fluxo de Implementação no Frontend

### 1. Verificar Status Antes de Sincronizar

```javascript
// Verificar status da conta
async function checkAccountStatus(accountId) {
  try {
    const response = await fetch(`/api/banking/pluggy/accounts/${accountId}/status/`);
    const data = await response.json();
    
    if (data.data.needs_reconnection) {
      // Mostrar botão/modal de reconexão
      showReconnectionModal(data.data);
      return false;
    }
    
    return true; // Pode sincronizar
  } catch (error) {
    console.error('Erro ao verificar status:', error);
    return false;
  }
}
```

### 2. Lidar com Erro de Sincronização

```javascript
// Sincronizar conta
async function syncAccount(accountId) {
  try {
    const response = await fetch(`/api/banking/pluggy/accounts/${accountId}/sync/`, {
      method: 'POST'
    });
    
    if (!response.ok) {
      const error = await response.json();
      
      // Verificar se precisa reconexão
      if (error.error_code === 'WAITING_USER_ACTION') {
        handleReconnectionNeeded(accountId, error);
        return;
      }
      
      throw new Error(error.message);
    }
    
    const data = await response.json();
    showSuccess(`${data.data.transactions_synced} transações sincronizadas`);
    
  } catch (error) {
    showError('Erro ao sincronizar: ' + error.message);
  }
}
```

### 3. Implementar Reconexão

```javascript
// Reconectar conta
async function reconnectAccount(accountId) {
  try {
    // 1. Obter token de reconexão
    const response = await fetch(`/api/banking/pluggy/accounts/${accountId}/reconnect/`, {
      method: 'POST'
    });
    const data = await response.json();
    
    // 2. Abrir Pluggy Connect com o token
    const connectOptions = {
      connectToken: data.data.connect_token,
      includeSandbox: data.data.sandbox_mode,
      onSuccess: (itemData) => {
        // Sucesso - atualizar UI
        showSuccess('Conta reconectada com sucesso!');
        // Sincronizar transações
        syncAccount(accountId);
      },
      onError: (error) => {
        showError('Erro ao reconectar: ' + error.message);
      }
    };
    
    // 3. Iniciar Pluggy Connect
    const pluggyConnect = new PluggyConnect(connectOptions);
    pluggyConnect.init();
    
  } catch (error) {
    showError('Erro ao gerar token de reconexão: ' + error.message);
  }
}
```

### 4. UI/UX Recomendada

```html
<!-- Modal de Reconexão -->
<div class="reconnection-modal">
  <div class="modal-content">
    <h3>Reconexão Necessária</h3>
    <p>{{ reconnectionMessage }}</p>
    
    <div class="bank-info">
      <img src="{{ bank.logo }}" alt="{{ bank.name }}">
      <span>{{ bank.name }}</span>
    </div>
    
    <div class="actions">
      <button @click="reconnectAccount(accountId)" class="btn-primary">
        Reconectar Agora
      </button>
      <button @click="closeModal" class="btn-secondary">
        Mais Tarde
      </button>
    </div>
    
    <p class="info">
      <i class="icon-info"></i>
      A reconexão é segura e suas transações anteriores serão mantidas.
    </p>
  </div>
</div>
```

## Monitoramento e Notificações

### Comando Django para Verificar Contas
```bash
# Verificar quais contas precisam reconexão
python manage.py check_reconnection_needed

# Com notificações (implementar sistema de notificação)
python manage.py check_reconnection_needed --notify
```

### Webhook Handler
O sistema já processa webhooks `item/waiting_user_action` automaticamente e atualiza o status das contas.

## Estados e Mensagens

### Estados que Requerem Reconexão:
- **WAITING_USER_ACTION**: "O banco está solicitando que você faça login novamente"
- **LOGIN_ERROR**: "Suas credenciais bancárias expiraram"
- **OUTDATED**: "A conexão com o banco está desatualizada"

### Fluxo Completo:
1. Usuário tenta sincronizar
2. Sistema detecta OUTDATED e tenta atualizar Item
3. Banco retorna WAITING_USER_ACTION
4. Sistema informa usuário que precisa reconectar
5. Usuário clica em "Reconectar"
6. Sistema gera token e abre Pluggy Connect
7. Usuário faz login no banco
8. Item é atualizado para UPDATED
9. Sincronização continua normalmente

## Considerações de Segurança

1. **Rate Limiting**: Endpoints têm rate limiting
   - Status: 10 requisições/hora
   - Reconexão: 5 requisições/hora

2. **Validação**: Apenas o dono da conta pode reconectar

3. **Tokens**: Expiram em 30 minutos

4. **Logs**: Todas as tentativas de reconexão são logadas