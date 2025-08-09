# CLAUDE.md - Finance Hub

## Correções Realizadas

### 1. Erro ao Clicar em Relatórios

#### Problemas Identificados

1. **Erro 500 no Backend** - Endpoint `/api/reports/templates/`
   - **Causa**: No arquivo `backend/apps/reports/views_optimized.py`, linha 265, estava usando `request.user.company` ao invés de `self.request.user.company`
   - **Solução**: Corrigido para `self.request.user.company`

2. **Erro "Query data cannot be undefined" no Frontend**
   - **Causa 1**: O hook `useReportData` esperava dados no formato `{ results: [...] }`, mas o serviço retornava dados diretamente
   - **Causa 2**: A query key estava usando `selectedPeriod` que podia ser `undefined`, causando `["reports", null]`
   - **Soluções**: 
     - Modificado o `queryFn` para lidar com ambos os formatos de resposta (array direto ou objeto com `results`)
     - Adicionado verificação para usar query key apropriada quando `selectedPeriod` é undefined

### Arquivos Modificados

1. **Backend**: `/backend/apps/reports/views_optimized.py` (linha 265)
2. **Frontend**: `/frontend/hooks/useReportData.ts` (linhas 76-87 e 186)

### Comandos de Teste

Para verificar se as correções funcionam:

```bash
# Backend
cd backend
python manage.py runserver

# Frontend
cd frontend
npm run dev
```

### 2. Erro de Rate Limiting no Login (429 Too Many Requests)

#### Problema
- **Erro**: `rest_framework.exceptions.Throttled: Pedido foi limitado. Expected available in 671 seconds.`
- **Causa**: Sistema de rate limiting bloqueou o login após múltiplas tentativas falhas
- **Limite**: 10/hora em produção, 100/hora em desenvolvimento

#### Solução Aplicada
- Limpeza do cache Redis para resetar os contadores de rate limiting
- O throttling já estava desabilitado em `development.py` mas o cache mantinha os limites anteriores

#### Como Evitar no Futuro
1. **Para desenvolvimento**: Certifique-se de que `DJANGO_SETTINGS_MODULE=core.settings.development`
2. **Se bloqueado novamente**:
   ```bash
   python manage.py shell
   from django.core.cache import cache
   cache.clear()
   ```

### Comandos de Teste

Para verificar se as correções funcionam:

```bash
# Backend
cd backend
python manage.py runserver

# Frontend
cd frontend
npm run dev
```

### 3. Erro de Autenticação JWT após Login (401 Unauthorized)

#### Problema
- **Erro**: `rest_framework.exceptions.NotAuthenticated: As credenciais de autenticação não foram fornecidas.`
- **Causa**: Cookies JWT com `SameSite=None` e `Secure=False` podem não ser enviados corretamente pelos navegadores modernos

#### Solução Aplicada
- Alterado `JWT_COOKIE_SAMESITE` de `None` para `'Lax'` em `development.py`
- Isso permite que os cookies sejam enviados em requisições same-origin, que é o caso em desenvolvimento (localhost:3000 → localhost:8000)

#### Configuração Final
```python
JWT_COOKIE_SECURE = False  # HTTP em desenvolvimento
JWT_COOKIE_SAMESITE = 'Lax'  # Compatível com desenvolvimento local
JWT_COOKIE_DOMAIN = None  # Browser gerencia o domínio
```

### 4. Erro ao Conectar Banco (PluggyConnectView)

#### Problema 1
- **Erro**: `TypeError: PluggyConnectView.post() missing 1 required positional argument: 'request'`
- **Causa**: Uso incorreto de `@method_decorator` com o decorator `requires_plan_feature` que não foi projetado para ser usado com `method_decorator`

#### Solução Aplicada
- Removido `@method_decorator` e aplicado o decorator `requires_plan_feature` diretamente nos métodos
- Alterado em `backend/apps/banking/views.py`:
  - Linha 611: `PluggyConnectView.post()` 
  - Linha 663: `PluggyCallbackView.post()`
- De: `@method_decorator(requires_plan_feature('add_bank_account'))`
- Para: `@requires_plan_feature('add_bank_account')`

#### Problema 2
- **Erro**: `AttributeError: 'Company' object has no attribute 'can_add_bank_account'`
- **Causa**: Métodos ausentes no modelo Company que são necessários para verificação de limites do plano

#### Solução Aplicada
- Adicionado métodos faltantes em `backend/apps/companies/models.py`:
  - `can_add_bank_account()` - Verifica se pode adicionar mais contas bancárias
  - `check_plan_limits()` - Alias para check_limit para compatibilidade
  - `can_use_ai_insight()` - Verifica se pode usar AI insights
  - `get_usage_percentage()` - Calcula percentual de uso

#### Arquivos Modificados
- **Backend**: `/backend/apps/banking/views.py` (linhas 611 e 663)
- **Backend**: `/backend/apps/companies/models.py` (linhas 237-278)

### Próximos Passos

### 5. Erro 500 no Pluggy Connect (Decorator com APIView)

#### Problema
- **Erro 1**: `TypeError: PluggyConnectView.post() missing 1 required positional argument: 'request'`
- **Erro 2**: `NameError: name 'method_decorator' is not defined`
- **Endpoint**: `/api/banking/pluggy/connect-token/` e `/api/banking/pluggy/callback/`
- **Causa**: Decorator `@requires_plan_feature` incompatível com APIView devido ao timing de autenticação

#### Análise Detalhada
1. O decorator `requires_plan_feature` executa antes da autenticação DRF
2. Em APIView, a autenticação ocorre durante o `dispatch`, não antes do método
3. O decorator não consegue acessar `request.user` autenticado
4. Usar `@method_decorator` causa erro de argumentos faltando

#### Solução Aplicada
- **Arquivo**: `backend/apps/banking/views.py`
- **Método**: Movido a verificação de plano para dentro dos métodos `post()`
- **Alteração**: 
  ```python
  # Removido o decorator:
  # @requires_plan_feature('add_bank_account')
  
  # Adicionado verificação inline:
  def post(self, request):
      # Check plan feature
      if hasattr(request.user, 'company'):
          company = request.user.company
          if not company.can_add_bank_account():
              # Retorna erro com detalhes do limite
  ```

#### Arquivos Modificados
- `backend/apps/banking/views.py` - Removido decorator `@requires_plan_feature`, adicionada verificação inline em PluggyConnectView e PluggyCallbackView
- **Nota**: Mantido import de `method_decorator` pois ainda é usado para `csrf_exempt` em PluggyWebhookView (linha 1001)

### 6. Erro 500 no Pluggy Callback - Connector não encontrado

#### Problema
- **Erro**: `PluggyConnector.DoesNotExist` causando 500 Internal Server Error
- **Endpoint**: `/api/banking/pluggy/callback/`
- **Causa**: Quando um usuário conecta um banco via Pluggy, o connector_id retornado pode não existir no banco de dados

#### Análise Detalhada
1. O callback recebe um `item_id` do Pluggy após conexão bem-sucedida
2. Busca os detalhes do item na API do Pluggy
3. Tenta encontrar o connector no banco local usando `pluggy_id`
4. Se o connector não existe, lança `PluggyConnector.DoesNotExist` → 500 error

#### Solução Aplicada
- **Arquivo**: `backend/apps/banking/views.py`
- **Linha**: ~724-760
- **Alteração**: Implementado `get_or_create` para connectors
  - Se o connector não existe, busca detalhes na API Pluggy
  - Cria o connector automaticamente com os dados obtidos
  - Se falhar ao buscar da API, cria registro mínimo

```python
# Antes: Assumia que connector sempre existe
connector = PluggyConnector.objects.get(pluggy_id=connector_id)

# Depois: Cria se não existir
try:
    connector = PluggyConnector.objects.get(pluggy_id=connector_id)
except PluggyConnector.DoesNotExist:
    # Busca detalhes e cria connector
    connector_data = client.get_connector(connector_id)
    connector = PluggyConnector.objects.create(...)
```

### 7. Erro 500 no Pluggy Callback - Celery/Redis Connection Refused

#### Problema
- **Erro**: `kombu.exceptions.OperationalError: [Errno 61] Connection refused`
- **Endpoint**: `/api/banking/pluggy/callback/` e outros endpoints de sync
- **Causa**: Tentativa de enfileirar tarefas Celery quando Redis não está rodando

#### Análise Detalhada
1. O callback tenta enfileirar task de sincronização: `sync_bank_account.delay()`
2. Se Redis/Celery não está rodando, lança exceção de conexão
3. A exceção não era tratada, causando 500 Internal Server Error
4. Problema comum em desenvolvimento quando Redis não está configurado

#### Solução Aplicada
- **Arquivo**: `backend/apps/banking/views.py`
- **Múltiplas linhas**: Todos os `.delay()` calls
- **Alteração**: Wrapped all Celery task calls em try/except

```python
# Antes: Assumia que Celery sempre está disponível
task = sync_bank_account.delay(str(item.id))

# Depois: Trata erro de conexão graciosamente
try:
    task = sync_bank_account.delay(str(item.id))
    task_id = task.id
except Exception as celery_error:
    logger.warning(f"Could not queue sync task: {celery_error}")
    task_id = None
```

#### Locais Corrigidos
1. `ManualSyncView.post()` - linha ~179
2. `BankAccountSyncView.post()` - linha ~340
3. `PluggyCallbackView.post()` - linha ~810
4. `AccountSyncView.post()` - linha ~888
5. `PluggyWebhookView.post()` - linha ~1068

### 8. Sincronização de Transações sem Celery/Redis

#### Problema
- **Sintoma**: Clicar em "Sincronizar" mostra sucesso mas transações não são salvas
- **Erro no log**: `WARNING: Could not queue sync task: [Errno 61] Connection refused`
- **Endpoint**: `/api/banking/accounts/{id}/sync/`
- **Causa**: Sync depende de Celery/Redis para processar assincronamente, mas retorna sucesso mesmo quando a task não é enfileirada

#### Análise Detalhada
1. O endpoint `BankAccountSyncView.post()` tenta enfileirar uma task Celery
2. Se Redis não está rodando, a task não pode ser enfileirada
3. O código anterior apenas logava um warning e retornava sucesso
4. Resultado: Usuário vê "sucesso" mas nenhuma transação é sincronizada

#### Solução Aplicada
- **Arquivo**: `backend/apps/banking/views.py`
- **Linha**: ~343-388
- **Alteração**: Implementado fallback para sincronização síncrona
  - Tenta enfileirar task assíncrona via Celery (preferencial)
  - Se falhar, executa sincronização síncrona diretamente
  - Importa e usa `_sync_account` da tasks.py
  - Retorna erro apropriado se ambos métodos falharem

```python
# Fallback para sync síncrono quando Celery está indisponível
try:
    from apps.banking.tasks import _sync_account
    with PluggyClient() as client:
        sync_result = _sync_account(client, account)
        # Sync executado com sucesso de forma síncrona
except Exception as sync_error:
    # Retorna erro 503 se sync síncrono também falhar
```

#### Comportamento Esperado
- **Com Redis/Celery**: Sync assíncrono (rápido, não bloqueia)
- **Sem Redis/Celery**: Sync síncrono (pode demorar, mas funciona)
- **Ambos falham**: Retorna erro 503 com mensagem explicativa

### 9. Erro de Sincronização - Transações não sendo salvas (RESOLVIDO)

#### Problema
- **Sintoma**: Clicar em "Sincronizar" mostra sucesso mas transações não são salvas no banco
- **Erro inicial**: `column notifications.event_key does not exist` seguido de `current transaction is aborted`
- **Erro subsequente**: `null value in column "notification_type" violates not-null constraint`
- **Endpoint**: `/api/banking/accounts/{id}/sync/`
- **Causa**: Tabela notifications estava em estado inconsistente com campos de duas versões do modelo

#### Análise Detalhada
1. Durante o sync, código tenta criar uma notificação de "low balance"
2. Primeira tentativa: Campo `event_key` não existia na tabela
3. Segunda tentativa: Campo antigo `notification_type` ainda existia e requeria valor não-null
4. PostgreSQL abortava toda a transação após qualquer erro
5. Resultado: Sync parecia funcionar mas nenhuma transação era persistida

#### Solução Aplicada em 3 Etapas

**1. Adição de campos novos** (`0002_add_event_key.py`)
- Adicionados campos: `event`, `event_key`, `is_critical`, `metadata`, `delivery_status`, etc.
- Defaults temporários para permitir migração

**2. Limpeza de campos antigos** (`0003_cleanup_old_fields.py`)
- Removidos campos obsoletos: `notification_type`, `data`, `priority`, `email_sent`, etc.
- Tabela agora consistente com o modelo atual

**3. Ajustes no modelo**
- `backend/apps/notifications/models.py`: Defaults adicionados para migração
- Campo `event_key` temporariamente nullable

#### Comandos Executados
```bash
python manage.py migrate notifications 0002_add_event_key
python manage.py migrate notifications 0003_cleanup_old_fields
```

#### Teste de Validação
- ✅ Transações podem ser criadas e salvas no banco
- ✅ Notificações funcionam sem abortar transação
- ✅ Sync completa sem erros de banco de dados

#### Arquivos Modificados
- `backend/apps/notifications/models.py` - Adicionados defaults aos campos
- `backend/apps/notifications/migrations/0002_add_event_key.py` - Adiciona campos novos
- `backend/apps/notifications/migrations/0003_cleanup_old_fields.py` - Remove campos antigos

### 10. Erro de Sincronização - USER_INPUT_TIMEOUT em Ambiente Local

#### Problema
- **Sintoma**: Transações não sincronizam após MFA timeout do banco
- **Erro**: Item entra em `USER_INPUT_TIMEOUT` após 60 segundos esperando código de verificação
- **Causa Raiz**: Webhooks configurados para produção não chegam em localhost
- **Dashboard Pluggy**: Múltiplos eventos `item/waiting_user_action` seguidos de `item/error` com USER_INPUT_TIMEOUT

#### Análise Detalhada
1. **Ambiente Local sem Webhooks**:
   - Webhooks configurados: `https://seu-backend.railway.app/api/banking/webhooks/pluggy/`
   - Servidor local não recebe notificações de mudança de status
   - Sistema não detecta que item entrou em timeout

2. **Fluxo do Problema**:
   - Banco solicita autenticação adicional (MFA)
   - Pluggy envia webhook `item/waiting_user_action` (não recebido localmente)
   - Após 60 segundos sem resposta: `USER_INPUT_TIMEOUT`
   - Sistema local tenta sincronizar sem saber do timeout
   - API retorna apenas transações antigas, não as novas

#### Solução Aplicada
- **Arquivo**: `backend/apps/banking/views.py` - método `sync()`
- **Alteração**: Buscar status real do item antes de sincronizar
- **Verificações adicionadas**:
  - Fetch item status da API Pluggy antes de sincronizar
  - Detecta `USER_INPUT_TIMEOUT` no executionStatus
  - Retorna erro claro solicitando reconexão
  
- **Arquivo**: `backend/apps/banking/tasks.py` - método `_sync_account()`
- **Alteração**: Verificação de status antes de sincronizar transações

#### Soluções para Desenvolvimento Local

**Opção 1: Usar ngrok (Recomendado)**
```bash
# Instalar ngrok
brew install ngrok  # macOS
# ou baixar de https://ngrok.com

# Expor servidor local
ngrok http 8000

# Usar URL gerada no Pluggy Dashboard
# Ex: https://abc123.ngrok.io/api/banking/webhooks/pluggy/
```

**Opção 2: Polling Manual**
- Sistema agora verifica status real do item antes de cada sync
- Detecta timeouts mesmo sem receber webhooks

**Opção 3: Ambiente de Staging**
- Deploy em ambiente de desenvolvimento com URL pública
- Configurar webhooks para esse ambiente

#### Comandos de Teste
```bash
# Testar sincronização
curl -X POST http://localhost:8000/api/banking/accounts/{account-id}/sync/

# Resposta esperada para timeout:
{
  "success": false,
  "error_code": "AUTHENTICATION_TIMEOUT",
  "message": "Timeout de autenticação. O banco solicitou verificação adicional mas o tempo expirou.",
  "reconnection_required": true,
  "details": "Por favor, reconecte sua conta e insira o código de verificação em até 60 segundos."
}
```

#### Arquivos Modificados
- `backend/apps/banking/views.py` - Verificação de status antes de sync
- `backend/apps/banking/tasks.py` - Verificação em _sync_account()

### 10. Correções de Alta Prioridade Pluggy (Bugs Críticos e Segurança)

#### Bugs Críticos Corrigidos
1. **Bug de Paginação** - Faltava `page += 1` no loop de sincronização de transações (linha 416 em tasks.py)
2. **Idempotência de Webhooks** - Implementado sistema de event_id para prevenir duplicação (linhas 613-661 em tasks.py)
3. **Timeout Configurável** - API timeout agora configurável via settings (linha 33 em client.py)

#### Segurança - Criptografia de Parâmetros MFA
- **Problema**: Códigos MFA (2FA) eram armazenados em texto plano no campo `parameter`
- **Solução**: Implementado sistema de criptografia completo
  - Novo campo `encrypted_parameter` no modelo PluggyItem
  - Utiliza criptografia Fernet com chave derivada do SECRET_KEY
  - Métodos `get_mfa_parameter()` e `set_mfa_parameter()` para transparência
  - Migração automática de dados existentes
  - Compatibilidade retroativa mantida
- **Arquivos Modificados**:
  - `apps/banking/models.py` - Adicionado campo encrypted_parameter e métodos
  - `apps/banking/views.py` - Atualizado para usar métodos criptografados
  - `apps/banking/tasks.py` - Atualizado para usar métodos criptografados
  - `apps/banking/utils/encryption.py` - Criado serviço de criptografia
  - `apps/banking/migrations/0010_add_encrypted_parameter.py` - Migração aplicada

### Próximos Passos

- ✅ Módulo de Relatórios corrigido
- ✅ Rate limiting resolvido  
- ✅ Autenticação JWT corrigida
- ✅ Erro de conexão bancária corrigido (métodos Company)
- ✅ Erro 500 Pluggy Connect/Callback corrigido (verificação inline para APIView)
- ✅ Erro 500 Pluggy Callback - Connector não encontrado (auto-criação de connectors)
- ✅ Erro 500 Pluggy Callback - Celery/Redis connection (tratamento de erro gracioso)
- ✅ Sincronização de transações sem Celery/Redis (fallback síncrono implementado)
- ✅ **Erro de sincronização de transações DEFINITIVAMENTE RESOLVIDO** (migrações aplicadas, tabela limpa)
- ✅ **Banco de dados consistente** (campos obsoletos removidos, modelo atualizado)
- ✅ **USER_INPUT_TIMEOUT em ambiente local** (verificação de status implementada)
- ✅ **Segurança MFA** - Parâmetros MFA agora criptografados no banco de dados
- **Para desenvolvimento local**: Considerar usar ngrok para receber webhooks
- **Importante**: Servidor backend reiniciado e funcionando
- **Opcional mas recomendado**: Iniciar Redis para melhor performance (`redis-server`)
- **Opcional**: Iniciar Celery worker para processamento assíncrono (`celery -A core worker -l info`)
- Reconectar conta bancária e inserir código MFA em até 60 segundos
- Testar sincronização após reconexão bem-sucedida
- Considerar script para popular connectors do Pluggy no banco