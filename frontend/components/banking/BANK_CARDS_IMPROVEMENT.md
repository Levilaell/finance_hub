# Melhorias nos Cards de Conta Bancária

## Visão Geral

Redesenhamos os componentes de cards de conta bancária com foco em **simplicidade** e **informações essenciais** para o usuário.

## Novos Componentes

### 1. `BankAccountCard`
Card principal com todas as informações da conta.

**Características:**
- **Saldo em destaque**: Tamanho grande (2xl) e posição proeminente
- **Status visual intuitivo**: Ícones e cores que comunicam o estado instantaneamente
- **Ações rápidas**: Botão de sincronização diretamente no card
- **Informações contextuais**: Última sincronização mostrada de forma relativa (ex: "5min atrás")
- **Visual limpo**: Apenas informações essenciais visíveis

**Estados de Status:**
- ✅ **Sincronizado** (verde): Tudo funcionando
- 🔄 **Sincronizando** (azul): Atualizando dados
- ⚠️ **Ação necessária** (laranja): Precisa de intervenção do usuário
- 🚫 **Erro** (vermelho): Problema de conexão
- 🕐 **Desatualizado** (cinza): Dados antigos

### 2. `BankAccountCardCompact`
Versão compacta para listas densas.

**Características:**
- **Layout horizontal**: Otimizado para listas
- **Informações mínimas**: Nome, banco, tipo e saldo
- **Indicador de status**: Ícone pequeno mas visível
- **Interação rápida**: Clique para gerenciar

### 3. `BankAccountsList`
Container completo para listar contas.

**Características:**
- **Cards de resumo**: Saldo total, contas bancárias e cartões
- **Dois modos de visualização**: Cards ou lista compacta
- **Agrupamento inteligente**: Separa contas bancárias de cartões
- **Estado vazio**: Guia o usuário a conectar primeira conta

### 4. `SyncStatusIndicator`
Indicador global de sincronização.

**Características:**
- **Status agregado**: Mostra estado de todas as contas
- **Ação global**: Botão "Sincronizar tudo"
- **Feedback visual**: Cores e ícones comunicam estado geral
- **Responsivo**: Adapta texto em telas menores

## Princípios de Design

### 1. Hierarquia Visual
- **Primário**: Saldo (maior elemento visual)
- **Secundário**: Nome da conta e banco
- **Terciário**: Status e última sincronização
- **Quaternário**: Ações e detalhes adicionais

### 2. Cores e Estados
```typescript
// Estados visuais
const statusColors = {
  synced: 'green',      // Sucesso
  syncing: 'blue',      // Processando
  error: 'red',         // Erro
  warning: 'orange',    // Atenção necessária
  neutral: 'gray'       // Inativo/desatualizado
};
```

### 3. Feedback Instantâneo
- Animações de loading (spinner)
- Mudanças de cor em hover
- Estados desabilitados durante ações
- Tooltips com informações extras

### 4. Responsividade
- Cards adaptam de 2 colunas para 1 em mobile
- Textos abreviam em telas pequenas
- Ações secundárias ocultam labels em mobile

## Exemplo de Uso

```tsx
import { BankAccountsList } from '@/components/banking/bank-accounts-list';
import { SyncStatusIndicator } from '@/components/banking/sync-status-indicator';

function AccountsPage() {
  const { accounts, syncAccount, syncAllAccounts } = useBankAccounts();
  
  return (
    <div>
      {/* Indicador global no header */}
      <header>
        <SyncStatusIndicator
          totalAccounts={accounts.length}
          syncedAccounts={accounts.filter(a => a.item?.status === 'UPDATED').length}
          errorAccounts={accounts.filter(a => a.item?.status === 'ERROR').length}
          syncingAccounts={syncingAccounts.length}
          onSyncAll={syncAllAccounts}
        />
      </header>

      {/* Lista de contas */}
      <BankAccountsList
        accounts={accounts}
        onSync={syncAccount}
        onManageConnection={openConnectionManager}
        onAddConnection={openPluggyConnect}
        syncingAccountIds={syncingAccounts}
      />
    </div>
  );
}
```

## Melhorias Implementadas

### 1. Simplicidade
- ✅ Removido número da conta (informação secundária)
- ✅ Consolidado badges de status em ícones
- ✅ Simplificado ações para apenas as essenciais
- ✅ Reduzido ruído visual

### 2. Informação
- ✅ Saldo em destaque absoluto
- ✅ Status visual instantâneo
- ✅ Tempo desde última sync
- ✅ Totalizadores no topo

### 3. Ações Rápidas
- ✅ Sincronizar direto no card
- ✅ Resolver problemas com 1 clique
- ✅ Gerenciar conta ao clicar no card

### 4. Performance
- ✅ Componentes otimizados
- ✅ Lazy loading de imagens
- ✅ Estados de loading granulares

## Próximos Passos

1. **Animações**: Adicionar transições suaves entre estados
2. **Gráficos**: Mini gráficos de evolução do saldo
3. **Insights**: Cards de insights financeiros
4. **Personalização**: Permitir reordenar e favoritar contas