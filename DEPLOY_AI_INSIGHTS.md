# 🚀 Deploy AI Insights no Railway

Este guia cobre o deploy da funcionalidade de **Insights com IA** no Railway.

---

## 📋 **Pré-requisitos**

1. ✅ Código commitado no Git
2. ✅ OpenAI API Key (obter em https://platform.openai.com/api-keys)
3. ✅ Railway CLI ou acesso ao Dashboard

---

## 🔧 **Configuração no Railway**

### **1. Adicionar Variáveis de Ambiente**

No Railway Dashboard, adicione:

```bash
# OpenAI (OBRIGATÓRIO para Insights com IA)
OPENAI_API_KEY=sk-proj-...
```

### **2. Services Necessários**

Seu Railway precisa ter **3 services**:

#### **a) Web (Django)**
- Já existe ✅
- Comando: `gunicorn core.wsgi:application`
- Porta: 8000

#### **b) Celery Worker** ⚠️ **NOVO**
- **Precisa criar este service**
- Comando: `celery -A core worker --loglevel=info`
- Mesmo código do Django
- Mesmo banco/Redis

#### **c) Celery Beat** ⚠️ **NOVO**
- **Precisa criar este service**
- Comando: `celery -A core beat --loglevel=info`
- Mesmo código do Django
- Mesmo banco/Redis

---

## 📦 **Criar Services no Railway**

### **Opção 1: Via Dashboard (Recomendado)**

1. **No projeto Railway, clique em "New Service"**

2. **Para Celery Worker:**
   - Selecione o mesmo repositório Git
   - Nome: `celery-worker`
   - Start Command: `celery -A core worker --loglevel=info`
   - Variables: Compartilhe as mesmas variáveis do Django (Database, Redis, etc)

3. **Para Celery Beat:**
   - Selecione o mesmo repositório Git
   - Nome: `celery-beat`
   - Start Command: `celery -A core beat --loglevel=info`
   - Variables: Compartilhe as mesmas variáveis do Django

### **Opção 2: Via Procfile (Alternativa)**

Crie arquivo `Procfile` na raiz do backend:

```
web: gunicorn core.wsgi:application --bind 0.0.0.0:$PORT
worker: celery -A core worker --loglevel=info
beat: celery -A core beat --loglevel=info
```

Railway detectará automaticamente.

---

## 🔄 **Passos do Deploy**

### **1. Commit e Push**

```bash
git add .
git commit -m "Adiciona Insights com IA"
git push origin main
```

### **2. Railway Auto-Deploy**

Railway fará automaticamente:
- ✅ Build do novo código
- ✅ Rodará migrations (`python manage.py migrate`)
- ✅ Restart dos services

### **3. Verificar Logs**

No Railway Dashboard:
- **Web**: Logs devem mostrar Django rodando
- **Worker**: `celery@... ready.`
- **Beat**: `Scheduler: Sending due task...`

---

## ✅ **Checklist Pós-Deploy**

### **1. Verificar Migrations**

Acesse o Terminal do service **Web** no Railway:

```bash
python manage.py showmigrations ai_insights
```

Deve mostrar:
```
ai_insights
 [X] 0001_initial
```

Se não rodou, execute manualmente:
```bash
python manage.py migrate ai_insights
```

### **2. Testar API**

```bash
# Verificar config
curl https://seu-app.railway.app/api/ai-insights/insights/config/ \
  -H "Authorization: Bearer <seu_token>"
```

### **3. Verificar Celery Beat**

No Railway Dashboard > celery-beat > Logs:

Deve aparecer algo como:
```
Scheduler: Sending due task generate-weekly-ai-insights
```

---

## 📊 **Monitoramento**

### **Logs Importantes**

**Django (Web):**
```
✅ Successfully generated insight <id> for user <email>
❌ Error generating insight for user <id>: <error>
```

**Celery Worker:**
```
✅ Task apps.ai_insights.tasks.generate_insight_for_user succeeded
❌ Task apps.ai_insights.tasks.generate_insight_for_user failed
```

**Celery Beat:**
```
✅ Scheduler: Sending due task generate-weekly-ai-insights
```

---

## 🐛 **Troubleshooting**

### **Erro: "OpenAI API key not configured"**
- ✅ Adicione `OPENAI_API_KEY` nas variáveis de ambiente
- ✅ Redeploy o service

### **Insights não estão sendo gerados semanalmente**
- ✅ Verifique se `celery-beat` está rodando
- ✅ Verifique logs do `celery-beat`
- ✅ Timezone correto: `America/Sao_Paulo`

### **Task fica pendente e não executa**
- ✅ Verifique se `celery-worker` está rodando
- ✅ Verifique se Redis está acessível
- ✅ Logs do worker mostram conexão com Redis

### **Erro ao gerar insights**
- ✅ Verifique saldo da conta OpenAI
- ✅ Verifique se API key é válida
- ✅ Logs mostrarão erro detalhado

---

## 💰 **Custos**

### **Railway**
- **Celery Worker**: ~$5-10/mês (service adicional)
- **Celery Beat**: ~$5/mês (service adicional leve)

### **OpenAI**
- **GPT-4o mini**: ~$0.15 por 1M tokens de input
- **Estimativa**: ~1000-2000 tokens por análise
- **Custo por usuário/mês**: ~$0.001 (4 análises)
- **100 usuários/mês**: ~$0.10

**Total estimado**: ~$10-15/mês adicionais

---

## 🎯 **Estrutura Final no Railway**

```
Seu Projeto Railway
│
├── 📦 web (Django)
│   ├── Comando: gunicorn core.wsgi
│   ├── Porta: 8000
│   └── Vars: DB, REDIS, OPENAI_API_KEY, etc
│
├── 📦 celery-worker (Novo)
│   ├── Comando: celery -A core worker
│   └── Vars: DB, REDIS, OPENAI_API_KEY, etc
│
├── 📦 celery-beat (Novo)
│   ├── Comando: celery -A core beat
│   └── Vars: DB, REDIS, OPENAI_API_KEY, etc
│
├── 🗄️ postgres (Banco)
└── 🔴 redis (Cache/Queue)
```

---

## 📝 **Comandos Úteis**

### **Testar geração manual (via Django shell)**

No Railway Terminal (service Web):

```python
python manage.py shell

from django.contrib.auth import get_user_model
from apps.ai_insights.services.insight_generator import InsightGenerator

User = get_user_model()
user = User.objects.get(email='seu@email.com')

generator = InsightGenerator(user)
insight = generator.generate(force=True)

print(f"Score: {insight.health_score}")
print(f"Status: {insight.health_status}")
```

### **Verificar tasks agendadas**

```bash
celery -A core inspect scheduled
```

### **Forçar execução de task**

```python
from apps.ai_insights.tasks import generate_weekly_insights
generate_weekly_insights.delay()
```

---

## ✅ **Está pronto para deploy!**

1. Commit e push
2. Adicione `OPENAI_API_KEY` no Railway
3. Crie services `celery-worker` e `celery-beat`
4. Verifique logs
5. Teste ativando insights em `/ai-insights`

**Qualquer dúvida, cheque os logs do Railway!** 🚀
