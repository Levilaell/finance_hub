# Configuração do Celery Beat no Railway

## ⚡ Quick Start (5 minutos)

1. **Railway Dashboard** → Seu projeto → **"+ New Service"**
2. **GitHub Repo** → mesmo repositório
3. **Nome:** `celery-beat`
4. **Settings** → **Deploy** → **Start Command:**
   ```bash
   cd backend && bash celery_beat.sh
   ```
5. **Variáveis:** Copie do serviço Worker (ou use Shared Variables)
6. **Deploy** → Verificar logs

**Logs esperados:**
```
✅ REDIS_URL is configured
✅ Redis connection successful
📅 Starting Celery Beat
```

---

## Problema

Os **Insights com IA** não estão sendo atualizados automaticamente porque o **Celery Beat** (scheduler de tasks periódicas) não está rodando.

### O que está rodando atualmente:
- ✅ **Web Service** - Django + Gunicorn
- ✅ **Celery Worker** - Processa tasks assíncronas
- ❌ **Celery Beat** - **FALTANDO!** - Agenda e dispara tasks periódicas

### Por que isso é necessário:
O Celery Beat é o componente responsável por executar tasks agendadas no `beat_schedule` (definido em `backend/core/celery.py`). Sem ele:
- ✅ O primeiro insight é gerado (quando o usuário ativa)
- ❌ Os insights semanais nunca são gerados automaticamente
- ❌ A limpeza de insights antigos nunca roda

---

## Solução: Adicionar Serviço Celery Beat no Railway

### Passo 1: Criar Novo Serviço no Railway

1. Acesse seu projeto no [Railway Dashboard](https://railway.app)
2. Clique em **"+ New Service"**
3. Selecione **"GitHub Repo"** (o mesmo repositório do projeto)
4. Nomeie o serviço: **`celery-beat`**

### Passo 2: Configurar Variáveis de Ambiente

O serviço Celery Beat precisa das mesmas variáveis de ambiente do backend. Copie as seguintes variáveis do serviço **Web** ou **Worker**:

```bash
DATABASE_URL
REDIS_URL
DJANGO_SECRET_KEY
OPENAI_API_KEY
PLUGGY_CLIENT_ID
PLUGGY_CLIENT_SECRET
STRIPE_TEST_SECRET_KEY
STRIPE_WEBHOOK_SECRET
```

**Ou** use **Shared Variables** para compartilhar as variáveis entre todos os serviços.

### Passo 3: Configurar Comando de Start

No serviço `celery-beat`, configure o **Start Command**:

```bash
cd backend && chmod +x celery_beat.sh && bash celery_beat.sh
```

**Ou**, se preferir sem o script:

```bash
cd backend && celery -A core beat --loglevel=info --scheduler django_celery_beat.schedulers:DatabaseScheduler
```

### Passo 4: Configurar Build Command (opcional)

Se necessário, configure o **Build Command**:

```bash
cd backend && pip install -r requirements.txt
```

### Passo 5: Deploy

1. Clique em **"Deploy"**
2. Aguarde o serviço iniciar
3. Verifique os logs para confirmar que está rodando

---

## Verificação

### Verificar logs do Celery Beat

Você deve ver mensagens como:

```
📅 Starting Celery Beat Scheduler
✅ DATABASE_URL is configured
✅ REDIS_URL is configured
✅ Redis connection successful
📅 Starting Celery Beat
⏰ Scheduled tasks will run according to beat_schedule
```

### Verificar tasks agendadas

As seguintes tasks devem aparecer nos logs:

1. **`generate-weekly-ai-insights`** - Roda toda segunda às 8h
2. **`cleanup-old-ai-insights`** - Roda todo domingo às 3h

---

## Arquitetura Final

Após a configuração, você terá 3 serviços rodando:

```
┌─────────────────────────────────────────────────────┐
│                    Railway Project                  │
├─────────────────────────────────────────────────────┤
│                                                     │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────┐│
│  │  Web Service │  │Celery Worker │  │Celery Beat││
│  │              │  │              │  │           ││
│  │   Gunicorn   │  │ Processa     │  │ Agenda    ││
│  │   + Django   │  │ Tasks        │  │ Tasks     ││
│  └──────────────┘  └──────────────┘  └───────────┘│
│         │                 │                │       │
│         └─────────────────┴────────────────┘       │
│                         │                          │
│                         ▼                          │
│              ┌──────────────────┐                  │
│              │  Redis (Broker)  │                  │
│              └──────────────────┘                  │
│                                                     │
└─────────────────────────────────────────────────────┘
```

---

## Workaround Temporário

Enquanto o Celery Beat não estiver configurado, os usuários podem:

1. **Gerar manualmente** uma nova análise clicando no botão **"Gerar Nova Análise"** (aparece quando o insight tem mais de 7 dias)
2. Usar o endpoint `/api/ai-insights/regenerate/` via API

---

## Troubleshooting

### Celery Beat não inicia

**Erro**: `ModuleNotFoundError: No module named 'celery'`

**Solução**: Certifique-se de que o build command está instalando as dependências:
```bash
cd backend && pip install -r requirements.txt
```

---

### Tasks não executam

**Problema**: Celery Beat está rodando mas as tasks não executam

**Solução**: Verifique se:
1. O REDIS_URL está configurado corretamente
2. O Celery Worker está rodando
3. O fuso horário está correto (configurado como `America/Sao_Paulo` em `core/celery.py`)

---

### Como testar localmente

Para testar o Celery Beat localmente:

```bash
cd backend

# Terminal 1: Redis (se não estiver rodando)
redis-server

# Terminal 2: Celery Worker
celery -A core worker --loglevel=info

# Terminal 3: Celery Beat
bash celery_beat.sh
```

---

## Referências

- [Documentação Celery Beat](https://docs.celeryq.dev/en/stable/userguide/periodic-tasks.html)
- [Django Celery Beat](https://django-celery-beat.readthedocs.io/)
- [Railway Docs](https://docs.railway.app/)
