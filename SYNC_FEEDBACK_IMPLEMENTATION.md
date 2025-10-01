# Implementação de Feedback de Sincronização em Tempo Real

## Problema Resolvido

**Antes:** Quando o usuário clicava em "Sincronizar", aparecia imediatamente um toast "Transações sincronizadas!", mas a sincronização real levava 20+ segundos para terminar.

**Agora:** O sistema mostra feedback progressivo em tempo real sobre o status da sincronização:
- "Iniciando sincronização..."
- "Conectando ao banco..."
- "Carregando contas..."
- "Sincronizando transações..."
- "Sincronização concluída!"

## Arquitetura da Solução

### 1. Backend - Sincronização Assíncrona

#### Endpoint Modificado: `POST /api/banking/connections/{id}/sync_transactions/`

**Comportamento Anterior:**
- Triggava update no Pluggy
- Esperava 2-3 segundos
- Tentava buscar transações
- Retornava "sucesso" (mesmo que sincronização ainda estivesse em andamento)

**Novo Comportamento:**
- Trigga update no Pluggy via `trigger_manual_sync()`
- Retorna **imediatamente** com status inicial
- Cliente usa polling para monitorar progresso

**Resposta:**
```json
{
  "message": "Synchronization initiated",
  "sync_status": "SYNC_TRIGGERED",
  "item_status": "UPDATING",
  "requires_action": false
}
```

#### Novo Endpoint: `GET /api/banking/connections/{id}/check_status/`

Verifica o status atual da sincronização consultando o Pluggy em tempo real.

**Resposta:**
```json
{
  "status": "UPDATING",
  "execution_status": "TRANSACTIONS_IN_PROGRESS",
  "is_syncing": true,
  "sync_complete": false,
  "requires_action": false,
  "last_updated_at": "2025-09-30T10:30:00Z"
}
```

#### Status do Pluggy

**Status do Item:**
- `UPDATING`: Sincronizando com o banco
- `UPDATED`: Sincronização concluída com sucesso
- `LOGIN_ERROR`: Erro de login (credenciais inválidas)
- `WAITING_USER_INPUT`: Aguardando MFA do usuário
- `OUTDATED`: Dados desatualizados, pode retentar
- `ERROR`: Erro genérico

**Execution Status (fases da sincronização):**
- `LOGIN_IN_PROGRESS`: Conectando ao banco
- `ACCOUNTS_IN_PROGRESS`: Carregando contas
- `TRANSACTIONS_IN_PROGRESS`: Sincronizando transações
- `SUCCESS`: Execução completa com sucesso
- `PARTIAL_SUCCESS`: Sucesso parcial
- `ERROR`: Erro na execução
- `INVALID_CREDENTIALS`: Credenciais inválidas

### 2. Frontend - Sistema de Polling

#### Hook Personalizado: `useSyncStatus`

Criado em `/frontend/hooks/useSyncStatus.ts`, este hook gerencia:

1. **Polling Automático**: Verifica status a cada 3 segundos
2. **Mensagens Progressivas**: Mapeia execution_status para mensagens amigáveis
3. **Detecção de Conclusão**: Para polling quando sync_complete=true
4. **Timeout**: 60 segundos máximo
5. **Tratamento de Erros**: Detecta e reporta erros

**Uso:**
```typescript
const { syncStatus, startPolling, stopPolling } = useSyncStatus(connectionId);

// Iniciar sincronização
startPolling();

// Status contém:
// - isPolling: boolean
// - message: string (mensagem amigável)
// - isComplete: boolean
// - hasError: boolean
```

#### Fluxo no Frontend

**accounts/page.tsx:**

1. Usuário clica em "Sincronizar"
2. Frontend chama `syncConnectionTransactions()`
3. Exibe toast: "Iniciando sincronização..."
4. Inicia polling com `startPolling()`
5. useEffect monitora mudanças em `syncStatus`
6. Toast é atualizado com mensagens progressivas
7. Quando `isComplete=true`, recarrega dados

**Mensagens Progressivas:**

```typescript
const executionMessages = {
  'LOGIN_IN_PROGRESS': 'Conectando ao banco...',
  'ACCOUNTS_IN_PROGRESS': 'Carregando contas...',
  'TRANSACTIONS_IN_PROGRESS': 'Sincronizando transações...',
  'SUCCESS': 'Sincronização concluída com sucesso!',
  'PARTIAL_SUCCESS': 'Sincronização parcialmente concluída',
  'ERROR': 'Erro na sincronização',
  'INVALID_CREDENTIALS': 'Credenciais inválidas',
};
```

### 3. Webhooks (Fallback Assíncrono)

Os webhooks do Pluggy continuam funcionando em background:

- `item/login_succeeded`: Login bem-sucedido
- `item/updated`: Item atualizado
- `transactions/created`: Novas transações
- `transactions/updated`: Transações atualizadas

Esses webhooks atualizam o banco de dados mesmo se o usuário sair da página.

## Diagrama de Fluxo

```
┌──────────┐         ┌──────────┐         ┌──────────┐         ┌──────────┐
│ Usuário  │         │ Frontend │         │ Backend  │         │  Pluggy  │
└────┬─────┘         └────┬─────┘         └────┬─────┘         └────┬─────┘
     │                    │                    │                    │
     │ Clica "Sincronizar"│                    │                    │
     ├───────────────────>│                    │                    │
     │                    │                    │                    │
     │                    │ POST sync_transactions                 │
     │                    ├───────────────────>│                    │
     │                    │                    │                    │
     │                    │                    │ PATCH /items/{id}  │
     │                    │                    ├───────────────────>│
     │                    │                    │                    │
     │                    │                    │ 200 OK (immediate) │
     │                    │                    │<───────────────────┤
     │                    │                    │                    │
     │                    │ Response: initiated│                    │
     │                    │<───────────────────┤                    │
     │                    │                    │                    │
     │ Toast: "Iniciando" │                    │                    │
     │<───────────────────┤                    │                    │
     │                    │                    │                    │
     │                    │ [Polling Loop]     │                    │
     │                    │ GET check_status   │                    │
     │                    ├───────────────────>│                    │
     │                    │                    │                    │
     │                    │                    │ GET /items/{id}    │
     │                    │                    ├───────────────────>│
     │                    │                    │ Status: UPDATING   │
     │                    │                    │<───────────────────┤
     │                    │                    │                    │
     │                    │ Status: UPDATING   │                    │
     │                    │ Exec: LOGIN_IN_...  │                    │
     │                    │<───────────────────┤                    │
     │                    │                    │                    │
     │ Toast: "Conectando"│                    │                    │
     │<───────────────────┤                    │                    │
     │                    │                    │                    │
     │                    │ [Wait 3s]          │                    │
     │                    │ GET check_status   │                    │
     │                    ├───────────────────>│                    │
     │                    │                    │ GET /items/{id}    │
     │                    │                    ├───────────────────>│
     │                    │                    │ Status: UPDATING   │
     │                    │                    │<───────────────────┤
     │                    │ Exec: TRANSACTIONS │                    │
     │                    │<───────────────────┤                    │
     │                    │                    │                    │
     │ Toast: "Sincroniz..."│                  │                    │
     │<───────────────────┤                    │                    │
     │                    │                    │                    │
     │                    │ [Wait 3s]          │                    │
     │                    │ GET check_status   │                    │
     │                    ├───────────────────>│                    │
     │                    │                    │ GET /items/{id}    │
     │                    │                    ├───────────────────>│
     │                    │                    │ Status: UPDATED    │
     │                    │                    │<───────────────────┤
     │                    │ Status: UPDATED    │                    │
     │                    │ Exec: SUCCESS      │                    │
     │                    │ sync_complete: true│                    │
     │                    │<───────────────────┤                    │
     │                    │                    │                    │
     │ Toast: "Concluída!"│                    │                    │
     │<───────────────────┤                    │                    │
     │                    │                    │                    │
     │                    │ GET /accounts/     │                    │
     │                    ├───────────────────>│                    │
     │ Dados atualizados  │ Updated data       │                    │
     │<───────────────────┤<───────────────────┤                    │
```

## Tratamento de Casos Especiais

### MFA Requerido
```json
{
  "sync_status": "MFA_REQUIRED",
  "requires_action": true,
  "mfa_parameter": { ... }
}
```
Toast: "Ação necessária: verifique suas credenciais ou autenticação"

### Credenciais Inválidas
```json
{
  "sync_status": "CREDENTIALS_REQUIRED",
  "requires_action": true
}
```
Toast: "Ação necessária: verifique suas credenciais"

### Timeout (60 segundos)
Toast: "Tempo limite excedido. Tente novamente."

### Erro Genérico
Toast: "Erro ao sincronizar transações"

## Benefícios

1. **Transparência**: Usuário sabe exatamente o que está acontecendo
2. **Confiança**: Não há mais mensagens de sucesso prematuras
3. **Experiência**: Feedback progressivo mantém usuário informado
4. **Robustez**: Sistema trata erros e timeouts adequadamente
5. **Performance**: Polling eficiente (apenas quando necessário)

## Configurações

### Intervalos de Polling
- **Intervalo**: 3 segundos (ajustável em `useSyncStatus.ts`)
- **Timeout**: 60 segundos (ajustável em `useSyncStatus.ts`)

### Delay de Recarga
- **Após Sincronização**: 1.5 segundos (para garantir que backend processou)

## Testes Recomendados

1. **Fluxo Normal**: Sincronização bem-sucedida
2. **Múltiplas Contas**: Sincronizar todas as contas
3. **MFA**: Banco que requer autenticação adicional
4. **Erro de Login**: Credenciais inválidas
5. **Timeout**: Sincronização que demora muito
6. **Navegação**: Sair da página durante sincronização
7. **Webhook**: Verificar que webhooks ainda funcionam em background

## Arquivos Modificados/Criados

### Backend
- ✏️ `backend/apps/banking/views.py` - Endpoints modificados
- ✏️ `backend/apps/banking/serializers.py` - Corrigido para nova estrutura de categorias
- ✏️ `backend/apps/banking/services.py` - Corrigido para nova estrutura de categorias
- ✏️ `backend/apps/banking/admin.py` - Corrigido para nova estrutura de categorias

### Frontend
- ✏️ `frontend/services/banking.service.ts` - Método checkConnectionStatus
- ✏️ `frontend/app/(dashboard)/accounts/page.tsx` - Lógica de polling
- ✨ `frontend/hooks/useSyncStatus.ts` - Hook personalizado de polling

## Próximos Passos Potenciais

1. **WebSockets**: Substituir polling por WebSockets para feedback instantâneo
2. **Notificações Push**: Notificar usuário quando sincronização terminar (mesmo fora da página)
3. **Histórico de Sincronização**: Mostrar log visual de sincronizações anteriores
4. **Progress Bar**: Barra de progresso visual ao invés de apenas texto
5. **Sincronização em Background**: Sistema de filas para sincronizações agendadas
