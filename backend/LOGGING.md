# Sistema de Logging - Finance Hub

## 📁 Estrutura de Arquivos de Log

Todos os logs são salvos em `backend/logs/`:

### Logs Gerais

| Arquivo | Nível | Descrição | Rotação |
|---------|-------|-----------|---------|
| `django.log` | INFO+ | Logs gerais do Django | 15MB, 10 backups |
| `errors.log` | ERROR+ | **Todos os erros do sistema** | 15MB, 10 backups |

### Logs Específicos de Webhooks

| Arquivo | Nível | Descrição | Rotação |
|---------|-------|-----------|---------|
| `webhooks.log` | DEBUG+ | Todos os webhooks recebidos e processados | 10MB, 5 backups |
| `webhook_errors.log` | ERROR+ | **Apenas erros de webhooks** | 20MB, 10 backups |

### Logs do Celery

| Arquivo | Nível | Descrição | Rotação |
|---------|-------|-----------|---------|
| `celery_errors.log` | ERROR+ | **Erros em tasks Celery** | 20MB, 10 backups |

### Logs Banking/Pluggy

| Arquivo | Nível | Descrição | Rotação |
|---------|-------|-----------|---------|
| `banking.log` | DEBUG+ | Operações do módulo banking | 10MB, 5 backups |
| `pluggy.log` | DEBUG+ | Chamadas à API Pluggy | 10MB, 5 backups |

### Logs de Segurança

| Arquivo | Nível | Descrição | Rotação |
|---------|-------|-----------|---------|
| `security.log` | INFO+ | Eventos de segurança | 50MB, 20 backups |
| `security.json` | INFO+ | Eventos de segurança (JSON) | 50MB, 20 backups |

## 🔍 Como Revisar Erros

### Ver todos os erros do sistema

```bash
# Últimos 50 erros
tail -50 backend/logs/errors.log

# Erros em tempo real
tail -f backend/logs/errors.log

# Buscar erro específico
grep "BankConnection" backend/logs/errors.log
```

### Ver apenas erros de webhooks

```bash
# Últimos erros de webhooks
tail -50 backend/logs/webhook_errors.log

# Filtrar por tipo de evento
grep "item/updated" backend/logs/webhook_errors.log

# Erros das últimas 24h
find backend/logs/webhook_errors.log -mtime -1 -exec cat {} \;
```

### Ver erros do Celery

```bash
# Últimos erros de tasks
tail -50 backend/logs/celery_errors.log

# Tasks que falharam
grep "ERROR" backend/logs/celery_errors.log | grep "process_"

# Ver retry de tasks
grep "Retry" backend/logs/celery_errors.log
```

## 📊 Exemplos de Logs

### Log Normal de Webhook (webhooks.log)

```
[INFO] 2025-11-14 10:30:45 [apps.banking.webhooks:82] Received webhook: item/updated for item 2f3d1039 (eventId: evt-123)
[INFO] 2025-11-14 10:30:45 [apps.banking.webhooks:141] Webhook item/updated accepted and queued. Response time: 45.23ms
```

### Log de Erro de Webhook (webhook_errors.log)

```
[ERROR] 2025-11-14 10:35:12 [apps.banking.tasks:155] Error handling item update: BankConnection matching query does not exist.
Traceback (most recent call last):
  File "apps/banking/tasks.py", line 35, in process_item_updated
    connection = BankConnection.objects.get(pluggy_item_id=item_id)
django.core.exceptions.ObjectDoesNotExist: BankConnection matching query does not exist.
```

### Log de Erro Celery (celery_errors.log)

```
[ERROR] 2025-11-14 10:40:01 [celery.worker.job:59] Task apps.banking.tasks.process_item_updated[abc-123] raised unexpected: ConnectionError('Redis connection failed')
```

## 🚀 No Railway (Produção)

### Opção 1: Persistir logs em volume (Recomendado)

Railway não persiste arquivos por padrão. Para salvar logs:

1. **Criar volume no Railway**:
   - Settings → Volumes → Add Volume
   - Mount Path: `/app/backend/logs`
   - Size: 1GB

2. **Acessar logs**:
   ```bash
   railway run bash
   cd backend/logs
   ls -lh
   tail -f webhook_errors.log
   ```

### Opção 2: Serviço de Logging Externo

Para produção robusta, considere:

- **Sentry** (erros + tracking): https://sentry.io
- **Papertrail** (logs centralizados): https://papertrailapp.com
- **Logtail** (logs + search): https://logtail.com

Configuração Sentry (já parcialmente implementado):

```python
# .env
SENTRY_DSN=https://...@sentry.io/...

# Sentry captura automaticamente todos os ERROR+
```

## 🔧 Configuração Personalizada

Para mudar níveis de log por ambiente:

```python
# .env.development
DJANGO_LOG_LEVEL=DEBUG  # Mais verboso

# .env.production
DJANGO_LOG_LEVEL=INFO   # Menos verboso
```

## 📝 Formato dos Logs

### Formato `detailed` (usado em erros)

```
[NIVEL] timestamp [modulo:linha] mensagem
[ERROR] 2025-11-14 10:30:45 [apps.banking.tasks:155] Error handling item update
```

### Formato `verbose` (usado em logs gerais)

```
NIVEL timestamp modulo process thread mensagem
INFO 2025-11-14 10:30:45 banking.tasks 12345 67890 Processing webhook
```

### Formato `json` (usado em security.json)

```json
{
  "asctime": "2025-11-14 10:30:45",
  "name": "security",
  "levelname": "WARNING",
  "message": "Failed login attempt from IP 192.168.1.1"
}
```

## 🎯 Dicas de Uso

### 1. Monitorar erros em tempo real

```bash
# Ver todos os erros em tempo real
tail -f backend/logs/errors.log

# Apenas erros críticos
tail -f backend/logs/errors.log | grep "CRITICAL\|ERROR"
```

### 2. Estatísticas de erros

```bash
# Contar erros por tipo
grep "ERROR" backend/logs/webhook_errors.log | cut -d' ' -f5 | sort | uniq -c

# Erros mais comuns
grep "ERROR" backend/logs/errors.log | awk '{print $NF}' | sort | uniq -c | sort -rn | head -10
```

### 3. Filtrar por período

```bash
# Erros de hoje
grep "2025-11-14" backend/logs/errors.log

# Erros entre 10h e 11h
grep "2025-11-14 10:" backend/logs/errors.log
```

### 4. Exportar para análise

```bash
# Salvar erros das últimas 24h em CSV
grep "ERROR" backend/logs/errors.log | awk -F'[][]' '{print $2","$4","$6}' > erros.csv
```

## ⚡ Rotação Automática

Os logs rotacionam automaticamente quando atingem o tamanho máximo:

- Arquivo atual: `webhook_errors.log`
- Rotacionado 1: `webhook_errors.log.1`
- Rotacionado 2: `webhook_errors.log.2`
- ...
- Rotacionado N: `webhook_errors.log.N` (deletado quando excede backupCount)

## 🔐 Segurança

Os logs **NÃO devem** conter:
- ✅ Senhas são filtradas automaticamente (via `SensitiveDataFilter`)
- ✅ Tokens são mascarados
- ✅ User agents maliciosos são filtrados
- ⚠️ Sempre revise logs antes de compartilhar

## 📚 Referências

- Configuração: [backend/core/settings/logging.py](backend/core/settings/logging.py)
- Filtros: [backend/core/filters.py](backend/core/filters.py)
- Django Logging: https://docs.djangoproject.com/en/stable/topics/logging/
