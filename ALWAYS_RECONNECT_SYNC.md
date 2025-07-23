# Sincronização Sempre Atualizada

## Nova Funcionalidade

Agora, sempre que o usuário clicar em "Sincronizar", o sistema abre o Pluggy Connect para garantir que o Item seja atualizado antes de buscar transações.

## Como Funciona

### 1. Usuário Clica em "Sincronizar"
- Sistema abre imediatamente o Pluggy Connect
- Mensagem: "Abrindo conexão com o banco para sincronizar..."

### 2. Atualização do Item
- Pluggy Connect abre com o parâmetro `updateItem`
- Usuário pode precisar fazer login (se banco solicitar)
- Item é atualizado para status UPDATED

### 3. Sincronização Automática
- Após sucesso no Pluggy Connect, sistema aguarda 2 segundos
- Sincroniza automaticamente as transações
- Mostra resultado: quantidade de transações sincronizadas

## Benefícios

1. **Garantia de Dados Atualizados**: Item sempre é atualizado antes de sincronizar
2. **Sem Items OUTDATED**: Evita problema de Items desatualizados
3. **Fluxo Simplificado**: Um clique para atualizar e sincronizar
4. **Transparência**: Usuário sabe que está atualizando a conexão

## Fluxo Técnico

```javascript
// 1. handleSyncAccount agora chama handleReconnectAccount
const handleSyncAccount = async (accountId: string) => {
  toast.info('Abrindo conexão com o banco para sincronizar...');
  await handleReconnectAccount(accountId);
};

// 2. handleReconnectAccount abre Pluggy Connect
// - Gera token de reconexão
// - Armazena accountId no sessionStorage
// - Abre widget com updateItem

// 3. No callback de sucesso do Pluggy Connect
// - Detecta que é uma reconexão
// - Aguarda 2 segundos
// - Sincroniza automaticamente
// - Mostra resultado ao usuário
```

## Experiência do Usuário

1. **Antes**: Clique em sincronizar → 0 transações (se OUTDATED)
2. **Agora**: Clique em sincronizar → Pluggy Connect → Login (se necessário) → Transações sincronizadas

## Observações

- Se usuário fechar o Pluggy Connect sem completar, nada acontece
- SessionStorage é limpo após uso ou cancelamento
- Funciona tanto com widget SDK quanto iframe
- Mensagens claras informam cada etapa do processo