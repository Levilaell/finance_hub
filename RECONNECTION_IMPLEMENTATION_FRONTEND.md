# Implementação da Reconexão - Frontend

## Fluxo Implementado

### 1. Detecção de WAITING_USER_ACTION

Quando o usuário clica em "Sincronizar", o sistema detecta automaticamente quando o banco requer reautenticação:

```javascript
// Em handleSyncAccount
if (error.response?.data?.error_code === 'WAITING_USER_ACTION') {
  setReconnectError({
    accountId,
    message: error.response.data.message || 'O banco está solicitando que você faça login novamente.'
  });
  toast.warning('Reconexão necessária para continuar sincronizando');
}
```

### 2. Dialog de Reconexão

Um modal é exibido informando o usuário sobre a necessidade de reconexão:

- Mensagem clara explicando que é um processo normal de segurança
- Informação de que os dados anteriores serão mantidos
- Botão para iniciar o processo de reconexão

### 3. Processo de Reconexão

Quando o usuário clica em "Reconectar Conta":

1. **Geração do Token**: O sistema chama o endpoint `/reconnect/` para obter um token de reconexão
2. **Armazenamento do Item ID**: O `item_id` é armazenado no sessionStorage para ser usado pelo Pluggy Connect
3. **Abertura do Pluggy Connect**: O widget é aberto com o parâmetro `updateItem`

```javascript
const handleReconnectAccount = async (accountId: string) => {
  // Chamar endpoint de reconexão
  const result = await bankingService.reconnectPluggyAccount(accountId);
  
  // Armazenar item_id para updateItem
  sessionStorage.setItem('pluggy_update_item', item_id);
  
  // Abrir Pluggy Connect para reconexão
  setPluggyConnectToken(connect_token);
  setIsConnecting(true);
};
```

### 4. Parâmetro updateItem

O `updateItem` é passado para o Pluggy Connect para indicar que é uma atualização de Item existente:

```javascript
<PluggyConnectModal
  connectToken={pluggyConnectToken}
  updateItem={sessionStorage.getItem('pluggy_update_item') || undefined}
  onSuccess={...}
/>
```

### 5. Indicadores Visuais

Contas com `status === 'sync_error'` mostram:

- Aviso amarelo indicando que reconexão é necessária
- Botão "Reconectar" em vez de "Sincronizar"
- Ícone de link para deixar clara a ação

## Componentes Modificados

### Backend (já implementado)
- `/api/banking/pluggy/accounts/{id}/status/` - Verifica status da conta
- `/api/banking/pluggy/accounts/{id}/reconnect/` - Gera token de reconexão

### Frontend
1. **banking.service.ts**
   - Adicionado método `reconnectPluggyAccount()`
   - Atualizado tipo de retorno de `getPluggyAccountStatus()`

2. **accounts/page.tsx**
   - Adicionado estados para controle de reconexão
   - Implementado `handleReconnectAccount()`
   - Adicionado dialog de reconexão
   - Modificado `handleSyncAccount()` para detectar WAITING_USER_ACTION
   - Adicionados indicadores visuais para contas com erro

3. **pluggy-connect-widget.tsx**
   - Adicionado suporte para prop `updateItem`
   - Passado `updateItem` na configuração do Pluggy Connect

4. **pluggy-connect-iframe.tsx**
   - Adicionado suporte para prop `updateItem`
   - Incluído `updateItem` nos parâmetros da URL do iframe

## Teste do Fluxo

1. Encontre uma conta com status WAITING_USER_ACTION ou sync_error
2. Clique em "Sincronizar" ou "Reconectar"
3. Se receber erro WAITING_USER_ACTION, o dialog de reconexão aparecerá
4. Clique em "Reconectar Conta"
5. O Pluggy Connect abrirá para reautenticação
6. Após login bem-sucedido, a conta será sincronizada automaticamente

## Observações

- O `updateItem` é crucial para que o Pluggy atualize o Item existente em vez de criar um novo
- O sessionStorage é usado para passar o `item_id` entre o processo de reconexão
- O token de reconexão é limpo após o uso para evitar conflitos
- O fluxo funciona tanto com o widget SDK quanto com o modo iframe