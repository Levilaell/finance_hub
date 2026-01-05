# ⚡ Setup Rápido: Celery Beat no Railway

## 🎯 Problema

Você já tem o **Celery Worker** rodando, mas falta o **Celery Beat** (scheduler).

```
Atualmente:
✅ Worker → Processa tasks (webhooks funcionam)
❌ Beat   → Agenda tasks periódicas (insights semanais NÃO funcionam)
```

---

## 🚀 Solução: 5 Passos Rápidos

### 1. Acesse o Railway Dashboard
- Vá para https://railway.app
- Abra seu projeto

### 2. Crie Novo Serviço
- Clique em **"+ New Service"**
- Selecione **"GitHub Repo"**
- Escolha o mesmo repositório do projeto
- **Nome do serviço:** `celery-beat`

### 3. Configure Start Command

Na aba **Settings** → **Deploy** do novo serviço:

**Start Command:**
```bash
cd backend && bash celery_beat.sh
```

### 4. Copie Variáveis de Ambiente

**Opção A - Usar Shared Variables (Recomendado):**
- Se você já usa Shared Variables, o Beat vai pegar automaticamente

**Opção B - Copiar Manualmente:**

Copie estas variáveis do serviço **Worker** ou **Web**:
```
DATABASE_URL
REDIS_URL
DJANGO_SECRET_KEY
OPENAI_API_KEY
PLUGGY_CLIENT_ID
PLUGGY_CLIENT_SECRET
```

### 5. Deploy

- Clique em **"Deploy"**
- Aguarde 1-2 minutos
- Verifique os logs

---

## ✅ Como Saber se Funcionou

### Logs que você DEVE ver:

```
📅 Starting Celery Beat Scheduler
✅ DATABASE_URL is configured
✅ REDIS_URL is configured
✅ Redis connection successful
📅 Starting Celery Beat
⏰ Scheduled tasks will run according to beat_schedule
```

### Tasks agendadas:

Após o deploy, você terá 2 tasks automáticas:

1. **`generate-weekly-ai-insights`**
   - Roda: **Segunda-feira às 8h** (horário de Brasília)
   - Gera insights para todos os usuários

2. **`cleanup-old-ai-insights`**
   - Roda: **Domingo às 3h** (horário de Brasília)
   - Remove insights com +1 ano

---

## 🧪 Testar Manualmente (Opcional)

Se quiser testar antes de segunda-feira:

1. Acesse o **Railway Shell** do serviço Web
2. Execute:

```python
from apps.ai_insights.tasks import generate_weekly_insights
generate_weekly_insights.delay()
```

3. Verifique os logs do **Worker** (não do Beat)
4. O insight deve aparecer no frontend em ~30 segundos

---

## 🔧 Troubleshooting

### Beat não inicia

**Erro:** `bash: celery_beat.sh: Permission denied`

**Solução:** O script já foi marcado como executável. Se mesmo assim der erro, use:
```bash
cd backend && celery -A core beat --loglevel=info
```

---

### Beat inicia mas tasks não executam

**Verificações:**

1. ✅ Redis está acessível?
   - Veja logs do Beat, deve ter: `✅ Redis connection successful`

2. ✅ Worker está rodando?
   - Beat agenda, Worker executa. Precisa dos dois.

3. ✅ Fuso horário correto?
   - Configurado como `America/Sao_Paulo` em `core/celery.py:43`

---

## 📊 Arquitetura Final

```
┌────────────────────────────────────────────┐
│           Railway Services                 │
├────────────────────────────────────────────┤
│                                            │
│  ┌─────────┐  ┌─────────┐  ┌───────────┐ │
│  │   Web   │  │  Worker │  │   Beat    │ │
│  │ Django  │  │ Celery  │  │  Celery   │ │
│  └─────────┘  └─────────┘  └───────────┘ │
│       │            │              │       │
│       └────────────┴──────────────┘       │
│                    │                      │
│              ┌─────▼─────┐                │
│              │   Redis   │                │
│              └───────────┘                │
│                                            │
└────────────────────────────────────────────┘
```

---

## 🎉 Resultado Esperado

Após configurar:

1. ✅ Insights são gerados **automaticamente** toda semana
2. ✅ Usuários não precisam clicar em "Gerar Nova Análise"
3. ✅ Sistema limpa insights antigos automaticamente
4. ✅ Loading infinito não acontece mais (já foi corrigido no código também)

---

## ⚠️ Workaround Temporário

Enquanto você não configura o Beat, os usuários podem:

- Clicar no botão **"Gerar Nova Análise"** que aparece quando o insight está desatualizado (>7 dias)
- O frontend agora mostra um aviso amarelo quando o insight está velho

---

**Precisa de ajuda? Veja documentação completa em:** `docs/CELERY_BEAT_SETUP.md`
