# Documentação de Sincronização e Resincronização com Pluggy

## Visão Geral

O sistema Finance Hub integra-se com a API Pluggy para sincronizar transações bancárias automaticamente. Este documento explica como funciona a sincronização e resincronização (manual) das transações.

## Conceitos Fundamentais

### Item Pluggy
Um **Item** é a representação de uma conexão com uma instituição financeira específica. É o ponto de entrada para acessar dados financeiros com consentimento do usuário.

**Características principais:**
- Criado através do Pluggy Connect Widget
- Coleta dados de até 365 dias quando criado pela primeira vez
- Suporta auto-sync a cada 12-24 horas (dependendo da assinatura)
- Armazena credenciais criptografadas com segurança
- Pode coletar múltiplos produtos financeiros (contas, cartões, investimentos, etc.)

## Fluxo de Sincronização

### 1. Sincronização Automática

O sistema possui sincronização automática que funciona de duas formas:

#### Via Webhooks
- Quando a Pluggy detecta novas transações, envia um webhook `transactions/created`
- O sistema processa o webhook e busca as novas transações automaticamente
- Implementado em: `backend/apps/banking/webhook_handler.py`

#### Via Job Agendado
- Executa periodicamente para contas ativas
- Verifica contas que não foram sincronizadas nas últimas 2 horas
- Implementado em: `backend/apps/banking/pluggy_sync_service.py`

### 2. Resincronização Manual

A resincronização manual é acionada pelo usuário através da interface e funciona assim:

```python
# backend/apps/banking/pluggy_views.py - PluggySyncAccountView
async def sync_account():
    # Sincroniza transações diretamente sem forçar atualização do Item
    # Isso evita triggerar status WAITING_USER_ACTION
    return await pluggy_sync_service.sync_account_transactions(account)
```

**Importante:** A resincronização manual **NÃO** força uma atualização do Item na Pluggy, pois isso pode causar o status `WAITING_USER_ACTION`, exigindo que o usuário faça login novamente no banco.

## Janelas de Tempo para Sincronização

O sistema usa janelas de tempo inteligentes para garantir que todas as transações sejam capturadas:

### Primeira Sincronização
- **Sandbox**: 365 dias
- **Produção/Trial**: 90 dias

### Sincronizações Incrementais
- **Sync muito recente** (< 24h): 7 dias de janela
- **Sync normal** (> 24h): mínimo 3 dias ou dias desde última sync + 1
- **Sync antiga** (> 30 dias): 30 dias

### Considerações de Timezone
- Busca 1 dia no futuro para capturar transações com problemas de timezone
- Considera diferenças UTC vs Brasil
- Implementado em: `pluggy_sync_service.py:_get_sync_from_date_safe()`

## Estados do Item e Tratamento

### Estados Ativos
- **UPDATING**: Conexão está sincronizando
- **UPDATED**: Sincronização concluída com sucesso
- **WAITING_USER_INPUT**: Requer interação do usuário (MFA)

### Estados de Erro
- **LOGIN_ERROR**: Falha na sincronização, requer novas credenciais
- **OUTDATED**: Sincronização anterior encontrou erros mas pode ser tentada novamente

### Tratamento Específico por Estado

#### WAITING_USER_ACTION / WAITING_USER_INPUT
```python
if item_status == 'WAITING_USER_ACTION':
    # Não tenta sincronizar
    # Retorna erro informando que precisa reautenticação
    return {
        'status': 'waiting_user_action',
        'message': 'Item requires user authentication'
    }
```

#### OUTDATED
```python
if item_status == 'OUTDATED':
    # Continua com a sincronização mas avisa
    logger.warning("Item is OUTDATED but continuing with sync")
    # Novas transações podem não estar disponíveis
```

#### LOGIN_ERROR
```python
if item_status == 'LOGIN_ERROR':
    # Não tenta sincronizar
    return {
        'status': 'login_error',
        'message': 'Invalid credentials'
    }
```

## Processamento de Transações

### Detecção de Duplicatas
```python
# Verifica se transação já existe pelo external_id
if Transaction.objects.filter(
    bank_account=account,
    external_id=str(external_id)
).exists():
    logger.info(f"Transaction {external_id} already exists, skipping")
    continue
```

### Mapeamento de Categorias
- O sistema mapeia categorias da Pluggy para categorias internas
- Implementado em: `backend/apps/banking/pluggy_category_mapper.py`
- Se não houver mapeamento, cria nova categoria automaticamente

### Atualização de Contadores
Após cada sincronização:
1. Recalcula total de transações do mês atual
2. Atualiza contador na empresa
3. Atualiza ResourceUsage para controle de limites do plano
4. Verifica se limites foram atingidos

## Tratamento de Erros

### Erros de API
- **PluggyAuthenticationError**: Problemas de autenticação com API Pluggy
- **Timeout**: Requests com timeout de 30 segundos
- **Rate Limiting**: Máximo 3 contas simultâneas, 0.5s delay entre contas

### Erros de Sincronização
```python
# Marca conta com erro se falhar
async def _mark_account_error(self, account: BankAccount, error_type: str):
    status_map = {
        'auth_error': 'error',
        'connection_error': 'error',
        'expired': 'expired'
    }
```

## Webhooks

### Eventos Processados
1. **item/created**: Novo item criado
2. **item/updated**: Status do item atualizado
3. **item/error**: Erro no item
4. **transactions/created**: Novas transações disponíveis

### Verificação de Assinatura
```python
def verify_pluggy_webhook_signature(payload: bytes, signature: str) -> bool:
    # Calcula HMAC SHA256 do payload
    # Compara com assinatura do header X-Pluggy-Signature
```

## Melhores Práticas

### Para Sincronização Manual
1. **NÃO** forçar atualização do Item (evita WAITING_USER_ACTION)
2. Usar janela de tempo expandida para capturar todas as transações
3. Sempre atualizar contadores após sincronização

### Para Tratamento de Erros
1. Verificar status do Item antes de sincronizar
2. Tratar cada tipo de erro apropriadamente
3. Informar usuário claramente sobre ações necessárias
4. Logar detalhadamente para debugging

### Para Performance
1. Limitar sincronizações simultâneas (máx. 3)
2. Usar paginação (500 transações por página)
3. Implementar rate limiting entre requests
4. Cachear dados quando possível

## Arquivos Relevantes

- `backend/apps/banking/pluggy_sync_service.py`: Serviço principal de sincronização
- `backend/apps/banking/pluggy_views.py`: Endpoints da API (incluindo resync manual)
- `backend/apps/banking/webhook_handler.py`: Processamento de webhooks
- `backend/apps/banking/pluggy_client.py`: Cliente HTTP para API Pluggy
- `backend/apps/banking/pluggy_category_mapper.py`: Mapeamento de categorias

## Logs e Monitoramento

O sistema usa logging extensivo com emojis para facilitar debugging:
- 🔄 Início de sincronização
- ✅ Operação bem-sucedida
- ❌ Erro
- ⚠️ Aviso
- 📊 Estatísticas
- 🕐 Timestamps
- 💰 Valores financeiros