## 🎯 O que é Sentry?

**Sentry** é uma plataforma de monitoramento de erros e performance que captura, organiza e te alerta sobre todos os bugs que acontecem em produção.

### Por que usar?

**Sem Sentry:**
```
ERROR: BankConnection matching query does not exist.
```
😕 Você não sabe quando, quem, o que causou...

**Com Sentry:**
```
BankConnection.DoesNotExist
apps/banking/tasks.py:35 in process_item_updated

Stack Trace:
  → connection = BankConnection.objects.get(pluggy_item_id=item_id)

Context:
  - item_id: "2f3d1039-abc-123"
  - event_type: "item/updated"
  - User: levi@email.com (ID: 123)
  - Environment: production
  - Time: 2025-11-14 10:35:12 BRT
  - Breadcrumbs:
    1. Webhook received from Pluggy
    2. Task queued (Celery)
    3. Task started processing
    4. Database query failed ← ERRO
```

---

## 🚀 Setup Rápido (5 minutos)

### 1. Criar Conta Sentry

1. Acesse https://sentry.io/signup/
2. Clique em **"Start Free"**
3. Use seu email ou GitHub
4. **Plano Free**: 5.000 eventos/mês (suficiente!)

### 2. Criar Projeto

1. Dashboard → **Create Project**
2. **Platform**: Django
3. **Alert frequency**: Default
4. **Project name**: `finance-hub-backend`
5. **Team**: Default

### 3. Copiar DSN

Após criar o projeto, você verá:

```
SENTRY_DSN=https://abc123xyz@o123456.ingest.sentry.io/789012
```

**Copie esse valor!**

### 4. Configurar no Railway

No Railway Dashboard:

1. Projeto → Serviço **web**
2. **Variables** → **New Variable**
3. Nome: `SENTRY_DSN`
4. Valor: Colar o DSN copiado
5. **Add**

Faça o mesmo para os workers Celery (celery-1, celery-2).

### 5. Deploy

```bash
# Commit e push (já está configurado no código)
git add .
git commit -m "Enable Sentry error tracking"
git push origin main
```

O Railway vai fazer deploy automaticamente.

### 6. Testar

Gere um erro de propósito:

```bash
# Via Railway CLI
railway run python backend/manage.py shell

# No shell Python
>>> from apps.banking.models import BankConnection
>>> BankConnection.objects.get(id='teste-erro')  # Vai gerar erro
```

Em **5 segundos**, você verá o erro no Sentry dashboard!

---

## 📊 O que o Sentry Captura

### ✅ Captura Automática

- **Exceções não tratadas** em views, tasks, signals
- **Stack traces completos** com linhas de código
- **Variáveis locais** no momento do erro
- **Request data**: URL, método, headers, body
- **User info**: Email, ID (se autenticado)
- **Breadcrumbs**: Logs antes do erro
- **Server context**: OS, Python, packages

### 🎯 Exemplos Reais

#### **Erro de Webhook:**
```python
# apps/banking/tasks.py
def process_item_updated(item_id, payload):
    connection = BankConnection.objects.get(pluggy_item_id=item_id)
    # ↑ Se não existir, Sentry captura automaticamente
```

**Você vê no Sentry:**
- Qual `item_id` causou o erro
- Qual usuário estava conectado
- Payload completo do webhook
- Stack trace apontando linha exata

#### **Erro de API:**
```python
# apps/banking/pluggy_client.py
response = requests.post(url, json=data)
response.raise_for_status()  # Se falhar, Sentry captura
```

**Você vê no Sentry:**
- URL chamada
- Status code recebido
- Request body enviado
- Response body retornado

---

## 🔧 Recursos Avançados (Opcional)

### Capturar Mensagens Customizadas

```python
from core.sentry import capture_message, add_breadcrumb

# Adicionar breadcrumb (rastro de eventos)
add_breadcrumb(
    message='Webhook recebido da Pluggy',
    category='webhook',
    data={'event_type': 'item/updated', 'item_id': item_id}
)

# Capturar mensagem (não é erro, mas importante)
capture_message('Sync concluído com sucesso', level='info')
```

### Capturar Exceções Manualmente

```python
from core.sentry import capture_exception

try:
    risky_operation()
except SpecificError as e:
    # Log no Sentry com contexto extra
    capture_exception(e, extra={
        'item_id': item_id,
        'user_id': user.id,
        'retry_count': 3
    })
    # Continua a execução ou faz fallback
```

### Performance Monitoring

Já está configurado! Sentry captura automaticamente:

- **Tempo de resposta** de views
- **Queries SQL** lentas
- **Chamadas HTTP** externas
- **Tasks Celery** demoradas

Ver em: Dashboard → **Performance**

---

## 📧 Notificações

### Configurar Alertas

1. Sentry → **Alerts** → **Create Alert**
2. **When**: An issue is first seen
3. **Then**: Send notification to Email
4. **Save Rule**

### Integrar com Slack (Recomendado)

1. Settings → **Integrations** → **Slack**
2. **Add Workspace**
3. Escolher canal (ex: `#erros-producao`)
4. Agora erros aparecem no Slack instantaneamente!

---

## 🎛️ Painel Sentry

### Issues (Erros)

**Dashboard → Issues**

Você vê:
- ✅ Erros agrupados por tipo
- ✅ Frequência (quantas vezes aconteceu)
- ✅ Último ocorrido
- ✅ Usuários afetados
- ✅ Status (novo, em progresso, resolvido)

### Ações em Issues

- **Assign**: Atribuir a alguém
- **Resolve**: Marcar como resolvido
- **Ignore**: Ignorar (se é esperado)
- **Merge**: Agrupar issues duplicadas

### Performance

**Dashboard → Performance**

- Transações mais lentas
- Queries SQL problemáticas
- Endpoints com timeout
- Tasks Celery demoradas

### Releases

Rastreie deploys:

```bash
# No CI/CD ou manualmente
export SENTRY_AUTH_TOKEN=seu_token
sentry-cli releases new $(git rev-parse HEAD)
sentry-cli releases set-commits $(git rev-parse HEAD) --auto
sentry-cli releases finalize $(git rev-parse HEAD)
```

Agora você sabe qual deploy introduziu qual bug!

---

## 💰 Planos e Limites

### Free (Recomendado para começar)

- ✅ **5.000 eventos/mês**
- ✅ 1 projeto
- ✅ 90 dias de retenção
- ✅ Performance monitoring (100 transações/mês)
- ❌ Sem SSO
- ❌ Sem SLA

**Suficiente?** Para ~10.000 requests/dia, sim!

### Team ($26/mês)

- ✅ **50.000 eventos/mês**
- ✅ Projetos ilimitados
- ✅ 90 dias de retenção
- ✅ Performance monitoring (1k transações/mês)

### Business ($80/mês)

- ✅ **500.000 eventos/mês**
- ✅ Performance monitoring (10k transações/mês)
- ✅ SSO, SLA

---

## 🔍 Exemplos de Uso

### Debugging Webhook Não Entregue

1. **Problema**: Webhook aparece como não entregue no Pluggy
2. **Sentry**: Buscar por `webhook` ou `process_item_updated`
3. **Ver erro**: "Connection timeout to Pluggy API"
4. **Solução**: Aumentar timeout ou retry

### Identificar Padrão de Erros

1. **Sentry → Issues**
2. **Filtrar**: `apps.banking.tasks`
3. **Ver gráfico**: Pico de erros às 10h
4. **Descobrir**: Banco faz manutenção às 10h
5. **Solução**: Adicionar retry nesses horários

### Encontrar Usuários Afetados

1. **Issue específica**
2. **Aba "Users"**
3. Ver lista de usuários que encontraram o erro
4. Notificar proativamente

---

## ⚙️ Configuração Avançada

### Filtrar Dados Sensíveis

Já configurado em `core/sentry.py`:

```python
def before_send_handler(event, hint):
    # Remove senhas, tokens, etc
    if 'password' in event['request']['data']:
        event['request']['data']['password'] = '[Filtered]'
    return event
```

### Ignorar Erros Comuns

Já configurado:

```python
ignore_errors=[
    'PermissionDenied',  # Acesso negado (esperado)
    'NotAuthenticated',  # Não autenticado (esperado)
    'Throttled',         # Rate limit (esperado)
]
```

### Ambientes Separados

```bash
# Railway - Production
SENTRY_DSN=https://prod@sentry.io/123
DJANGO_ENV=production

# Localhost - Development
SENTRY_DSN=https://dev@sentry.io/456
DJANGO_ENV=development
```

Isso cria **2 projetos** no Sentry (prod e dev).

---

## 🎯 Checklist Pós-Setup

- [ ] DSN configurado no Railway
- [ ] Deploy feito com sucesso
- [ ] Teste de erro capturado no Sentry
- [ ] Alertas por email configurados
- [ ] Slack integrado (opcional)
- [ ] Time convidado para o projeto (opcional)

---

## 🆘 Troubleshooting

### "Eventos não aparecem no Sentry"

```bash
# Verificar se DSN está configurado
railway variables | grep SENTRY_DSN

# Ver logs
railway logs | grep sentry

# Testar manualmente
railway run python -c "from core.sentry import init_sentry; init_sentry(); 1/0"
```

### "Muitos eventos (excedeu limite)"

1. **Filtrar erros não críticos**:
   ```python
   # Em core/sentry.py
   ignore_errors=['UmaExcecaoEspecifica']
   ```

2. **Reduzir sample rate**:
   ```python
   traces_sample_rate=0.1  # 10% das transações
   ```

3. **Upgrade de plano** (se necessário)

### "Dados sensíveis aparecendo"

Adicionar em `before_send_handler`:

```python
sensitive_fields = ['meu_campo_secreto']
for field in sensitive_fields:
    if field in data:
        data[field] = '[Filtered]'
```

---

## 📚 Recursos

- [Sentry Django Docs](https://docs.sentry.io/platforms/python/guides/django/)
- [Sentry Performance](https://docs.sentry.io/product/performance/)
- [Best Practices](https://docs.sentry.io/platforms/python/best-practices/)
- [Sentry Status](https://status.sentry.io/)

---

## 🎉 Próximos Passos

1. ✅ Configurar DSN no Railway
2. ✅ Fazer deploy
3. ✅ Testar captura de erro
4. 📧 Configurar alertas por email
5. 💬 Integrar com Slack (opcional)
6. 📊 Explorar Performance Monitoring
7. 🚀 Configurar Releases (opcional)

---

**Com Sentry, você nunca mais vai perder um erro em produção!** 🎯
