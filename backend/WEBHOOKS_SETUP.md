# Configuração de Webhooks da Pluggy

## Arquitetura de Processamento Assíncrono

### Problema Resolvido

A Pluggy possui requisitos estritos para entrega de webhooks:
- **Timeout**: 5 segundos para resposta com status 2XX
- **Retries**: Até 3 tentativas com intervalo de 1 minuto
- **Perda**: Após 3 falhas, o webhook é **permanentemente perdido**

Anteriormente, o webhook handler processava tudo de forma **síncrona**, causando:
- Timeouts ao fazer múltiplas chamadas à API da Pluggy
- Sincronização de contas e transações demorando > 5 segundos
- Webhooks não entregues aparecendo no dashboard da Pluggy

### Solução Implementada

O sistema agora utiliza **Celery** para processamento assíncrono:

1. **Webhook Handler** (`webhooks.py`):
   - Valida assinatura (< 50ms)
   - Verifica idempotência via `eventId`
   - **Retorna 200 OK imediatamente** (< 100ms)
   - Despacha task Celery assíncrona

2. **Celery Tasks** (`tasks.py`):
   - Processam os eventos em background workers
   - Fazem retry automático em caso de falha (3x)
   - Executam sincronização de contas e transações

## Arquivos Modificados

### 1. `backend/apps/banking/webhooks.py`
- Removido processamento síncrono
- Adicionado logging de tempo de resposta
- Delegação para tasks Celery
- Resposta imediata com 200 OK

### 2. `backend/apps/banking/tasks.py` (NOVO)
Tasks Celery para processar cada tipo de evento:
- `process_item_updated` - Item atualizado
- `process_item_created` - Item criado
- `process_item_error` - Erro no item
- `process_item_deleted` - Item deletado
- `process_item_mfa` - MFA necessário
- `process_item_login_succeeded` - Login bem-sucedido
- `process_transactions_created` - Transações criadas
- `process_transactions_updated` - Transações atualizadas
- `process_transactions_deleted` - Transações deletadas
- `process_connector_status` - Status do conector

## Configuração do Ambiente

### Requisitos

1. **Redis** - Broker de mensagens do Celery
   - Necessário para enfileirar tasks
   - Configure via variável `REDIS_URL`

2. **Celery Worker** - Processa tasks em background
   - Já configurado no `Procfile`
   - Configuração em `backend/core/celery.py`

### Variáveis de Ambiente

```bash
# Redis para Celery
REDIS_URL=redis://localhost:6379/0

# Pluggy Webhook Secret (opcional mas recomendado)
PLUGGY_WEBHOOK_SECRET=seu_webhook_secret_aqui
```

## Deploy no Railway

### Verificar se o Worker está Rodando

No Railway, você precisa ter **2 serviços** rodando:

1. **Web** - Servidor Django/Gunicorn
   ```
   web: gunicorn core.wsgi:application --bind 0.0.0.0:$PORT
   ```

2. **Worker** - Celery worker para processar webhooks
   ```
   worker: celery -A core worker --loglevel=info --concurrency=2
   ```

### Como Configurar no Railway

#### Opção 1: Multiple Processes (Recomendado para Railway)

Railway permite criar múltiplos serviços. Configure:

1. Acesse o projeto no Railway
2. Vá em Settings → Deploy
3. Adicione um novo serviço "Worker"
4. Configure o comando de start: `celery -A core worker --loglevel=info --concurrency=2`

#### Opção 2: Process Manager (Alternativa)

Se Railway não suportar múltiplos serviços, use Honcho ou similar:

```bash
pip install honcho
honcho start
```

### Verificar Logs

Para verificar se os webhooks estão sendo processados:

```bash
railway logs
```

Procure por logs como:
```
[INFO] Webhook item/updated accepted and queued for processing. Response time: 45.23ms
[INFO] [TASK] Processing item_updated for item abc123
[INFO] [TASK] Successfully processed update for connection xyz
```

## Monitoramento

### Métricas de Performance

O webhook handler agora registra:
- **Tempo de resposta** em milissegundos
- **Event type** recebido
- **Task dispatched** (confirmação de enfileiramento)

Exemplo de log:
```
Webhook item/updated accepted and queued for processing. Task dispatched: True. Response time: 52.34ms
```

### Verificar se Webhooks estão Falhando

1. **Dashboard Pluggy**: Verifique eventos com tentativas múltiplas
2. **Logs Railway**: Procure por erros nas tasks Celery
3. **Redis**: Verifique se há tasks pendentes

```bash
# Conectar ao Redis e verificar filas
redis-cli
> LLEN celery  # Ver número de tasks na fila
```

## Testes Locais

### 1. Iniciar Redis

```bash
docker run -d -p 6379:6379 redis:alpine
# ou
redis-server
```

### 2. Iniciar Celery Worker

```bash
cd backend
celery -A core worker --loglevel=info
```

### 3. Iniciar Django

```bash
python manage.py runserver
```

### 4. Testar Webhook

Use o comando de teste:
```bash
python manage.py test_webhook
```

Ou envie um webhook manual:
```bash
curl -X POST http://localhost:8000/api/banking/webhooks/pluggy/ \
  -H "Content-Type: application/json" \
  -d '{
    "event": "item/updated",
    "itemId": "test-item-123",
    "eventId": "test-event-456"
  }'
```

Você deve ver:
1. Resposta imediata (< 100ms)
2. Log no servidor Django: "Webhook accepted and queued"
3. Log no Celery worker: "[TASK] Processing item_updated"

## Troubleshooting

### Problema: Webhooks ainda aparecem como não entregues

**Causas possíveis:**
1. Worker do Celery não está rodando
2. Redis não está acessível
3. Erro na configuração do Railway

**Solução:**
```bash
# Verificar se worker está rodando
railway logs | grep "celery worker"

# Verificar conexão com Redis
railway logs | grep "redis"

# Verificar variáveis de ambiente
railway variables
```

### Problema: Tasks não estão sendo processadas

**Causas possíveis:**
1. Redis não configurado
2. Worker não autodescobriu as tasks

**Solução:**
```bash
# Reiniciar worker
railway restart worker

# Verificar se tasks estão registradas
celery -A core inspect registered
```

### Problema: Tempo de resposta ainda > 5s

**Causas possíveis:**
1. Validação de assinatura muito lenta
2. Cache Redis lento
3. Problema de rede

**Solução:**
- Verifique logs de tempo de resposta
- Considere desabilitar validação de assinatura temporariamente para teste
- Verifique latência do Redis

## Recursos Adicionais

- [Documentação Pluggy - Webhooks](https://docs.pluggy.ai/docs/webhooks)
- [Celery Documentation](https://docs.celeryproject.org/)
- [Railway Docs - Background Workers](https://docs.railway.app/)

## Resumo das Mudanças

✅ **Antes**: Processamento síncrono, timeouts frequentes
✅ **Depois**: Processamento assíncrono, resposta < 100ms
✅ **Benefícios**:
- Webhooks sempre entregues com sucesso
- Processamento confiável via Celery
- Retry automático em caso de falhas
- Melhor rastreabilidade com logs detalhados
