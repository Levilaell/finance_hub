# Sincronização com Autenticação Bancária

## Nova Funcionalidade

Agora, sempre que o usuário clicar em "Sincronizar", o sistema explica que o BANCO está solicitando autenticação e abre o Pluggy Connect para garantir acesso às transações mais recentes.

## Como Funciona

### 1. Usuário Clica em "Sincronizar"
- Sistema mostra dialog explicativo
- Mensagem clara: "Seu banco está solicitando que você faça login"
- Explica por que isso é necessário (segurança bancária)

### 2. Autenticação no Banco
- Usuário clica em "Autenticar no Banco"
- Pluggy Connect abre com o parâmetro `updateItem`
- Usuário faz login no site oficial do banco
- Item é atualizado para status UPDATED

### 3. Sincronização Automática
- Após autenticação bem-sucedida, sistema aguarda 2 segundos
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

## Mensagens Claras sobre Segurança

O sistema deixa claro que:
- É o BANCO que está solicitando autenticação
- Isso é uma medida de segurança normal
- Faz parte do protocolo Open Banking
- O usuário será direcionado ao site oficial do banco

## Experiência do Usuário

1. **Antes**: Clique em sincronizar → 0 transações (se OUTDATED)
2. **Agora**: 
   - Clique em sincronizar
   - Dialog explicativo sobre segurança bancária
   - Clique em "Autenticar no Banco"
   - Login no site oficial do banco
   - Transações sincronizadas automaticamente

## Observações

- Se usuário fechar o Pluggy Connect sem completar, nada acontece
- SessionStorage é limpo após uso ou cancelamento
- Funciona tanto com widget SDK quanto iframe
- Mensagens claras informam cada etapa do processo