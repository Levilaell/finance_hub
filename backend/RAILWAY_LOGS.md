# Como Ver Logs no Railway - Guia Prático

## 🚀 Opção 1: Dashboard Railway (Sem Setup)

### Ver Logs em Tempo Real

1. Acesse https://railway.app/dashboard
2. Clique no projeto **finance_hub**
3. Selecione o serviço (web, celery-1, celery-2)
4. Clique na aba **"Deployments"**
5. Clique no deployment ativo (verde)
6. Aba **"Logs"**

### Filtros Úteis

No campo de busca do dashboard:

```
ERROR                    # Todos os erros
webhook                  # Logs de webhooks
[TASK]                   # Processamento Celery
process_item_updated     # Task específica
BankConnection           # Erros de conexão
```

### Limitações

- ⚠️ Mostra apenas logs recentes (~últimas horas)
- ⚠️ Não persiste após restart/deploy
- ⚠️ Difícil fazer análise profunda

---

## 💻 Opção 2: Railway CLI (Recomendado)

### Instalação

```bash
# Instalar CLI
npm install -g @railway/cli

# Login (abre navegador)
railway login

# Linkar ao projeto (na pasta do projeto)
cd /path/to/finance_hub
railway link
```

### Comandos Básicos

```bash
# Ver logs em tempo real (tail -f)
railway logs --follow

# Últimos 100 logs
railway logs

# Filtrar por serviço
railway logs --service web
railway logs --service celery-1

# Exportar para arquivo
railway logs > logs.txt
railway logs --service web > logs_web.txt

# Últimas 24h (se disponível)
railway logs --since 24h

# Buscar erro específico
railway logs | grep ERROR
railway logs | grep "webhook"
```

### Script Helper

Use o script incluído:

```bash
# Tornar executável (Unix/Mac)
chmod +x backend/scripts/view_logs.sh

# Ver erros gerais
./backend/scripts/view_logs.sh errors

# Erros de webhooks
./backend/scripts/view_logs.sh webhook-errors

# Logs em tempo real
./backend/scripts/view_logs.sh live

# Conectar ao container
./backend/scripts/view_logs.sh ssh

# Exportar tudo
./backend/scripts/view_logs.sh export
```

---

## 📁 Opção 3: Persistir Logs com Volume (Produção)

### Por que usar Volume?

- ✅ Logs persistem entre deploys
- ✅ Acesso a arquivos de log completos
- ✅ Análise offline possível
- ✅ Rotação automática funciona

### Setup (5 minutos)

#### 1. Criar Volume

**No Dashboard Railway:**

1. Projeto → Serviço **web**
2. **Settings** → **Volumes** → **New Volume**
3. Configurar:
   ```
   Mount Path: /app/backend/logs
   Size: 1 GB
   ```
4. Clicar **Add**
5. Aguardar deploy (1-2 min)

#### 2. Verificar

```bash
# Conectar ao container
railway run bash

# Verificar se volume está montado
ls -lh /app/backend/logs

# Deve mostrar os arquivos:
# errors.log
# webhook_errors.log
# celery_errors.log
# webhooks.log
# banking.log
# pluggy.log
```

### Comandos com Volume

```bash
# Conectar e navegar
railway run bash
cd backend/logs

# Ver últimos erros
tail -50 errors.log

# Erros de webhooks
tail -50 webhook_errors.log

# Seguir em tempo real
tail -f webhook_errors.log

# Buscar padrão
grep "item/updated" webhooks.log

# Contar erros
grep -c "ERROR" errors.log

# Últimos 100 erros com contexto
tail -100 errors.log | grep -B 2 -A 2 "ERROR"

# Exportar para local
railway run "cat backend/logs/errors.log" > errors_local.log
```

### Análise Offline

```bash
# Baixar arquivo de log
railway run "cat backend/logs/webhook_errors.log" > webhook_errors_$(date +%Y%m%d).log

# Analisar localmente
grep "ERROR" webhook_errors_*.log
grep "process_item_updated" webhook_errors_*.log | wc -l

# Erros por hora
grep "ERROR" webhook_errors_*.log | cut -d' ' -f2-3 | cut -d: -f1 | sort | uniq -c
```

---

## 🎯 Opção 4: Serviço Externo (Produção Avançada)

### Sentry (Erros + Stack Traces)

**Melhor para:** Rastreamento de erros, alertas

#### Setup Rápido:

1. Criar conta: https://sentry.io (grátis 5k eventos/mês)
2. Criar projeto Django
3. Copiar DSN
4. Adicionar no Railway:
   ```bash
   # Settings → Variables
   SENTRY_DSN=https://abc@o123.ingest.sentry.io/456
   ```
5. Redeploy

#### Benefícios:

- ✅ Captura automática de exceções
- ✅ Stack trace completo
- ✅ Contexto de requisição
- ✅ Alertas por email/Slack
- ✅ Performance monitoring
- ✅ Release tracking

### Better Stack (Logs Completos)

**Melhor para:** Logs estruturados, análise, search

#### Setup:

1. Criar conta: https://betterstack.com/logs
2. Criar source "Django"
3. Copiar token
4. Instalar:
   ```bash
   pip install logtail-python
   ```
5. Configurar em `logging.py`:
   ```python
   'logtail': {
       'level': 'INFO',
       'class': 'logtail.LogtailHandler',
       'source_token': os.getenv('LOGTAIL_SOURCE_TOKEN'),
   }
   ```

#### Benefícios:

- ✅ Search poderoso
- ✅ Retention longa (30+ dias)
- ✅ Dashboards customizados
- ✅ Integração Slack/Discord
- ✅ SQL queries nos logs

---

## 📊 Comparação de Opções

| Método | Facilidade | Custo | Retenção | Análise | Alertas |
|--------|-----------|-------|----------|---------|---------|
| Dashboard | ⭐⭐⭐⭐⭐ | Grátis | Horas | ⭐ | ❌ |
| CLI | ⭐⭐⭐⭐ | Grátis | Horas | ⭐⭐ | ❌ |
| Volume | ⭐⭐⭐ | +$5/mês | Ilimitado* | ⭐⭐⭐⭐ | ❌ |
| Sentry | ⭐⭐⭐⭐ | Grátis/Pago | 90 dias | ⭐⭐⭐⭐⭐ | ✅ |
| Better Stack | ⭐⭐⭐ | Pago | 30+ dias | ⭐⭐⭐⭐⭐ | ✅ |

*Limitado ao tamanho do volume (1GB = ~milhões de linhas)

---

## 🎯 Recomendação Final

### **Para Desenvolvimento:**
- Railway CLI: `railway logs --follow`

### **Para Produção (Startup):**
- Volume (1GB) + Railway CLI
- Sentry (grátis) para erros críticos

### **Para Produção (Escala):**
- Sentry (pago) + Better Stack
- Alertas automáticos
- Análise avançada

---

## 🔧 Troubleshooting

### "railway: command not found"

```bash
npm install -g @railway/cli
railway login
```

### "Failed to link project"

```bash
cd /path/to/finance_hub
railway link
# Selecione o projeto na lista
```

### "Volume não aparece"

1. Verificar se volume foi criado: Settings → Volumes
2. Aguardar deploy completo
3. Verificar mount path: `/app/backend/logs`

### "Arquivos de log vazios"

1. Verificar se aplicação está logando:
   ```bash
   railway logs | grep ERROR
   ```
2. Verificar permissões:
   ```bash
   railway run "ls -la /app/backend/logs"
   ```

---

## 📚 Recursos

- [Railway CLI Docs](https://docs.railway.app/develop/cli)
- [Railway Volumes](https://docs.railway.app/reference/volumes)
- [Sentry Django](https://docs.sentry.io/platforms/python/guides/django/)
- [Better Stack](https://betterstack.com/docs/logs/python/)

---

## 🆘 Suporte

Se encontrar problemas:

1. Verificar se serviço está rodando: Dashboard → Service
2. Ver logs raw: `railway logs`
3. Testar conexão: `railway run bash`
4. Verificar variáveis: `railway variables`
