# Próximos Passos no Frontend - Reconexão

## Situação Atual

O backend está recebendo webhooks `item/waiting_user_action` corretamente, indicando que o banco está pedindo reautenticação do usuário.

## O que o Frontend deve fazer:

### 1. Na Resposta de Erro da Sincronização

Quando o usuário clica em "Sincronizar" e recebe erro, verificar:

```javascript
// Se a resposta contém error_code === 'WAITING_USER_ACTION'
if (errorResponse.error_code === 'WAITING_USER_ACTION') {
  // Mostrar mensagem específica
  showReconnectionRequired({
    message: errorResponse.message,
    reconnectionUrl: errorResponse.reconnection_url
  });
}
```

### 2. Implementar Modal/Interface de Reconexão

```javascript
// Componente de Reconexão
const ReconnectionModal = ({ account, visible, onClose }) => {
  const [loading, setLoading] = useState(false);
  
  const handleReconnect = async () => {
    setLoading(true);
    
    try {
      // 1. Obter token de reconexão
      const response = await fetch(`/api/banking/pluggy/accounts/${account.id}/reconnect/`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${getAuthToken()}`,
          'Content-Type': 'application/json'
        }
      });
      
      const data = await response.json();
      
      if (data.success) {
        // 2. Abrir Pluggy Connect com o token
        const connectOptions = {
          connectToken: data.data.connect_token,
          updateItem: data.data.item_id, // IMPORTANTE!
          
          onSuccess: (itemData) => {
            // Reconexão bem-sucedida
            message.success('Conta reconectada com sucesso!');
            onClose();
            // Sincronizar novamente
            syncAccount(account.id);
          },
          
          onError: (error) => {
            message.error('Erro ao reconectar: ' + error.message);
          }
        };
        
        // Iniciar Pluggy Connect
        const pluggyConnect = new PluggyConnect(connectOptions);
        pluggyConnect.init();
      }
    } catch (error) {
      message.error('Erro ao gerar token de reconexão');
    } finally {
      setLoading(false);
    }
  };
  
  return (
    <Modal
      title="Reconexão Necessária"
      visible={visible}
      onCancel={onClose}
      footer={[
        <Button key="cancel" onClick={onClose}>
          Cancelar
        </Button>,
        <Button
          key="reconnect"
          type="primary"
          loading={loading}
          onClick={handleReconnect}
        >
          Reconectar Conta
        </Button>
      ]}
    >
      <Alert
        message="O banco está solicitando que você faça login novamente"
        description="Isso é normal e acontece periodicamente por questões de segurança. Seus dados e transações anteriores serão mantidos."
        type="info"
        showIcon
      />
    </Modal>
  );
};
```

### 3. Verificar Status Antes de Sincronizar (Opcional)

Para uma experiência ainda melhor, verificar o status antes:

```javascript
// Antes de sincronizar
const checkAndSync = async (accountId) => {
  // 1. Verificar status
  const statusResponse = await fetch(`/api/banking/pluggy/accounts/${accountId}/status/`);
  const statusData = await statusResponse.json();
  
  if (statusData.data.needs_reconnection) {
    // Mostrar modal de reconexão diretamente
    setShowReconnectionModal(true);
  } else {
    // Proceder com sincronização normal
    await syncAccount(accountId);
  }
};
```

### 4. Indicadores Visuais

Adicionar indicadores nas contas que precisam reconexão:

```javascript
// Na lista de contas
{accounts.map(account => (
  <AccountCard key={account.id}>
    <AccountInfo>
      <h3>{account.nickname}</h3>
      <p>{account.bank_provider.name}</p>
    </AccountInfo>
    
    {account.needs_reconnection && (
      <Badge status="warning" text="Reconexão necessária" />
    )}
    
    <Button 
      onClick={() => handleSync(account)}
      danger={account.needs_reconnection}
    >
      {account.needs_reconnection ? 'Reconectar' : 'Sincronizar'}
    </Button>
  </AccountCard>
))}
```

## Fluxo Completo

1. **Usuário clica em Sincronizar**
2. **Backend detecta WAITING_USER_ACTION**
3. **Frontend recebe erro com `error_code: 'WAITING_USER_ACTION'`**
4. **Frontend mostra modal/interface de reconexão**
5. **Usuário clica em "Reconectar"**
6. **Frontend chama POST `/reconnect/` para obter token**
7. **Frontend abre Pluggy Connect com o token**
8. **Usuário faz login no banco**
9. **Pluggy Connect retorna sucesso**
10. **Frontend sincroniza transações automaticamente**

## Exemplo de Resposta de Erro

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

## Notas Importantes

1. **Sempre passar `updateItem` no Pluggy Connect** - isso garante que está atualizando o Item existente
2. **Mostrar mensagens claras** - o usuário precisa entender que é normal e seguro
3. **Sincronizar automaticamente após reconexão** - melhor experiência
4. **Considerar notificações** - avisar usuário quando contas precisam reconexão

## Teste Rápido

Para testar o fluxo:

1. Encontre uma conta com status OUTDATED ou WAITING_USER_ACTION
2. Tente sincronizar
3. Deve receber erro com `error_code: 'WAITING_USER_ACTION'`
4. Implemente o modal de reconexão
5. Teste o fluxo completo

O backend está pronto e funcionando. Agora é só implementar a interface no frontend!