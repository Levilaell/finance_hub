# Sistema de Banking - Frontend

## Visão Geral

O sistema de banking do CaixaHub permite que usuários conectem suas contas bancárias via Open Banking usando a integração com Pluggy, visualizem saldos, transações e recebam insights financeiros automatizados.

## Arquitetura

### Estrutura de Arquivos

```
frontend/
├── types/
│   └── banking.ts              # Tipos TypeScript para banking
├── services/
│   └── banking.service.ts      # Serviço de API
├── hooks/
│   ├── use-bank-connections.ts # Hook para conexões bancárias
│   ├── use-bank-accounts.ts    # Hook para contas
│   ├── use-bank-transactions.ts # Hook para transações
│   └── use-pluggy-connect.ts   # Hook para Pluggy Connect
├── components/banking/
│   ├── bank-connection-card.tsx # Card de conexão bancária
│   ├── connect-bank-dialog.tsx  # Dialog para conectar banco
│   ├── account-summary-cards.tsx # Cards de resumo
│   └── mfa-dialog.tsx          # Dialog para MFA
└── app/(dashboard)/accounts/
    └── page.tsx                # Página principal de contas

```

## Componentes

### BankConnectionCard
Exibe uma conexão bancária com suas contas associadas.

```tsx
<BankConnectionCard
  connection={connection}
  onSync={handleSync}
  onDelete={handleDelete}
  onUpdateCredentials={handleUpdateCredentials}
  onUpdateMFA={handleUpdateMFA}
  isLoading={isLoading}
/>
```

### ConnectBankDialog
Modal para conectar nova conta bancária via Pluggy Connect.

```tsx
<ConnectBankDialog
  open={open}
  onOpenChange={setOpen}
  onSuccess={handleSuccess}
/>
```

### AccountSummaryCards
Cards de resumo mostrando saldo total, cartões e patrimônio.

```tsx
<AccountSummaryCards
  summary={summary}
  isLoading={isLoading}
/>
```

### MFADialog
Dialog para inserir código de autenticação em duas etapas.

```tsx
<MFADialog
  open={open}
  onOpenChange={setOpen}
  onSubmit={handleSubmit}
  institutionName="Banco do Brasil"
/>
```

## Hooks

### useBankConnections
Gerencia conexões bancárias.

```tsx
const {
  connections,
  isLoading,
  syncConnection,
  deleteConnection,
  createConnection,
  hasConnectionErrors,
} = useBankConnections();
```

### useBankAccounts
Gerencia contas bancárias e resumo.

```tsx
const {
  accounts,
  accountsByType,
  summary,
  totals,
  isLoading,
} = useBankAccounts();
```

### useBankTransactions
Gerencia transações com filtros e categorização.

```tsx
const {
  transactions,
  statistics,
  filters,
  updateFilters,
  bulkCategorize,
  aiCategorize,
} = useBankTransactions();
```

### usePluggyConnect
Integração com Pluggy Connect widget.

```tsx
const {
  openConnect,
  updateConnection,
  closeConnect,
  isConnecting,
} = usePluggyConnect({
  onSuccess: (itemId) => console.log('Connected:', itemId),
  onError: (error) => console.error('Error:', error),
});
```

## Fluxo de Conexão

1. **Usuário clica em "Conectar conta"**
   - Abre ConnectBankDialog
   - Lista instituições disponíveis

2. **Usuário seleciona banco**
   - Cria Connect Token via API
   - Abre Pluggy Connect widget

3. **Usuário autentica no banco**
   - Insere credenciais
   - Completa MFA se necessário

4. **Conexão estabelecida**
   - Recebe itemId do Pluggy
   - Cria conexão no backend
   - Inicia sincronização

5. **Sincronização de dados**
   - Busca contas e saldos
   - Importa transações
   - Atualiza UI

## Estados da Conexão

- `LOGIN_IN_PROGRESS`: Conectando ao banco
- `UPDATING`: Sincronizando dados
- `UPDATED`: Sincronização completa
- `LOGIN_ERROR`: Credenciais inválidas
- `WAITING_USER_INPUT`: Aguardando MFA
- `OUTDATED`: Dados desatualizados
- `ERROR`: Erro na conexão

## Tratamento de Erros

### Login Error
```tsx
if (connection.status === 'LOGIN_ERROR') {
  // Solicita atualização de credenciais
  updateConnection(connection.pluggy_item_id);
}
```

### MFA Required
```tsx
if (connection.status === 'WAITING_USER_INPUT') {
  // Abre dialog para código MFA
  setShowMFADialog(true);
}
```

### Sync Error
```tsx
if (error) {
  toast.error('Erro ao sincronizar conta');
  // Retry logic implementado no hook
}
```

## Segurança

1. **Tokens seguros**
   - Connect Token expira em 30 minutos
   - Usado apenas no cliente

2. **Sem credenciais no frontend**
   - Credenciais processadas apenas pelo Pluggy
   - Backend não armazena senhas

3. **HTTPS obrigatório**
   - OAuth redirect deve usar HTTPS
   - Webhooks validados com assinatura

## Performance

1. **Cache com React Query**
   - Stale time: 60s para conexões
   - Stale time: 30s para transações

2. **Paginação**
   - Transações paginadas (50 por página)
   - Lazy loading de detalhes

3. **Otimizações**
   - Debounce em filtros de busca
   - Memoização de cálculos pesados

## Customização

### Temas
```tsx
// Cores baseadas na instituição
style={{ backgroundColor: institution.primary_color || '#6366f1' }}
```

### Idioma
```tsx
// Pluggy Connect em português
language: 'pt'
```

### Sandbox
```tsx
// Habilitar bancos de teste em dev
includeSandbox: process.env.NODE_ENV === 'development'
```

## Troubleshooting

### Widget não abre
1. Verificar se SDK carregou
2. Checar token válido
3. Console para erros

### Sincronização falha
1. Verificar status da conexão
2. Checar logs no backend
3. Tentar sync manual

### MFA não funciona
1. Verificar código correto
2. Timeout do código (5 min)
3. Solicitar novo código