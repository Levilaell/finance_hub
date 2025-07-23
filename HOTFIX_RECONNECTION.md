# HOTFIX - Implementação Rápida de Reconexão (Produção)

## Problema
- Usuários não conseguem sincronizar quando banco pede reautenticação
- Erro: `WAITING_USER_ACTION`
- Transações novas não são sincronizadas

## Solução Imediata (Backend já está pronto)

### 1. No Frontend - Detectar o Erro

```javascript
// Quando sincronizar falhar, verificar o erro
const handleSyncError = (error) => {
  if (error.error_code === 'WAITING_USER_ACTION') {
    // Mostrar botão de reconexão
    showReconnectButton(error.reconnection_url);
  }
};
```

### 2. Implementar Botão de Reconexão

```javascript
const handleReconnect = async (accountId) => {
  try {
    // Chamar endpoint de reconexão
    const response = await api.post(`/api/banking/pluggy/accounts/${accountId}/reconnect/`);
    const { connect_token, item_id } = response.data.data;
    
    // Abrir Pluggy Connect
    const pluggyConnect = new PluggyConnect({
      connectToken: connect_token,
      updateItem: item_id, // IMPORTANTE!
      onSuccess: () => {
        alert('Conta reconectada! Sincronizando...');
        window.location.reload(); // Recarregar para sincronizar
      },
      onError: (err) => {
        alert('Erro ao reconectar: ' + err.message);
      }
    });
    
    pluggyConnect.init();
  } catch (error) {
    alert('Erro ao gerar token de reconexão');
  }
};
```

### 3. UI Mínima (Exemplo React)

```jsx
// Se receber erro WAITING_USER_ACTION
{syncError && syncError.error_code === 'WAITING_USER_ACTION' && (
  <div className="alert alert-warning">
    <p>{syncError.message}</p>
    <button 
      className="btn btn-primary"
      onClick={() => handleReconnect(accountId)}
    >
      Reconectar Conta
    </button>
  </div>
)}
```

## Endpoints Disponíveis

### Verificar Status (GET)
```
GET /api/banking/pluggy/accounts/{id}/status/
```

Retorna:
```json
{
  "data": {
    "needs_reconnection": true,
    "reconnection_message": "O banco está solicitando login"
  }
}
```

### Gerar Token de Reconexão (POST)
```
POST /api/banking/pluggy/accounts/{id}/reconnect/
```

Retorna:
```json
{
  "data": {
    "connect_token": "eyJ0eXAi...",
    "item_id": "a0beeaac-806b-410f-b814-fbb8fe517d54"
  }
}
```

## Teste Rápido em Produção

1. Encontre uma conta que não está sincronizando
2. Verifique o console - deve ter erro `WAITING_USER_ACTION`
3. Implemente o botão de reconexão
4. Teste com um usuário

## Mensagem para Usuários

```
"Seu banco está solicitando que você faça login novamente por questões de segurança. 
Isso é normal e acontece periodicamente. 
Clique em 'Reconectar' para continuar sincronizando suas transações."
```

## Código Mínimo Completo (Copiar e Colar)

```javascript
// Adicionar no componente de sincronização
const [reconnectError, setReconnectError] = useState(null);

// Modificar função de sync
const syncAccount = async (accountId) => {
  try {
    const response = await api.post(`/api/banking/pluggy/accounts/${accountId}/sync/`);
    // sucesso...
  } catch (error) {
    if (error.response?.data?.error_code === 'WAITING_USER_ACTION') {
      setReconnectError({
        accountId,
        message: error.response.data.message
      });
    }
  }
};

// Função de reconexão
const reconnectAccount = async (accountId) => {
  try {
    const res = await api.post(`/api/banking/pluggy/accounts/${accountId}/reconnect/`);
    const { connect_token, item_id } = res.data.data;
    
    window.PluggyConnect.init({
      connectToken: connect_token,
      updateItem: item_id,
      onSuccess: () => location.reload(),
      onError: (e) => alert('Erro: ' + e.message)
    });
  } catch (e) {
    alert('Erro ao reconectar');
  }
};

// No render
{reconnectError && (
  <div style={{padding: 20, background: '#fff3cd', border: '1px solid #ffeaa7'}}>
    <p>{reconnectError.message}</p>
    <button onClick={() => reconnectAccount(reconnectError.accountId)}>
      Reconectar Conta Bancária
    </button>
  </div>
)}
```

## Deploy Imediato

1. Adicione o código acima
2. Teste localmente
3. Deploy em produção
4. Monitore os logs

O backend já está 100% pronto e testado. Só precisa implementar a interface no frontend!