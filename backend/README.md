# Finance Hub - Backend

API Django para gerenciamento financeiro com integração Open Banking (Pluggy) e pagamentos (Stripe).

## 🚀 Quick Start

### Desenvolvimento Local

1. **Setup do ambiente:**
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# OU
venv\Scripts\activate  # Windows

pip install -r requirements.txt
```

2. **Configurar variáveis de ambiente:**
```bash
cp .env.example .env
# Editar .env com suas credenciais
```

3. **Iniciar o servidor:**
```bash
python manage.py migrate
python manage.py runserver
```

### Deploy para Produção (Railway)

Ver [`DEPLOY.md`](../DEPLOY.md) na raiz do projeto.

**Quick deploy:**
```bash
# Testar configuração antes de deploy
./test-deploy.sh

# Deploy para Railway
railway up
```

## 📁 Estrutura

```
backend/
├── apps/                    # Apps Django
│   ├── authentication/      # Autenticação JWT
│   ├── banking/            # Integração Pluggy
│   ├── companies/          # Gestão de empresas
│   ├── reports/            # Relatórios financeiros
│   └── subscriptions/      # Stripe subscriptions
├── core/                   # Configurações Django
│   ├── settings/
│   │   ├── base.py        # Configurações base
│   │   ├── development.py # Desenvolvimento
│   │   └── production.py  # Produção
│   ├── middleware.py      # Middlewares custom
│   ├── wsgi.py           # WSGI entry point
│   └── urls.py           # URL routing
├── start.sh              # Script de inicialização (Railway)
├── railway.json          # Configuração Railway
├── test-deploy.sh        # Teste de configuração
├── requirements.txt      # Dependências Python
└── .env.example         # Template de env vars
```

## 🔧 Scripts Disponíveis

### `start.sh`
Script de inicialização para produção (Railway):
- ✅ Valida env vars obrigatórias
- ✅ Testa conexão com database
- ✅ Executa migrations
- ✅ Coleta static files
- ✅ Inicia Gunicorn com configurações otimizadas

### `test-deploy.sh`
Testa configuração de produção localmente:
```bash
./test-deploy.sh
```

## 🔐 Variáveis de Ambiente

### Essenciais
```bash
DJANGO_SECRET_KEY=        # Secret key do Django
DATABASE_URL=             # PostgreSQL connection string
JWT_SECRET_KEY=          # Secret para JWT tokens
FRONTEND_URL=            # URL do frontend (CORS)
```

### Stripe (Pagamentos)
```bash
STRIPE_TEST_SECRET_KEY=
STRIPE_TEST_PUBLIC_KEY=
STRIPE_WEBHOOK_SECRET=
STRIPE_DEFAULT_PRICE_ID=
```

### Pluggy (Open Banking)
```bash
PLUGGY_CLIENT_ID=
PLUGGY_CLIENT_SECRET=
PLUGGY_WEBHOOK_URL=
```

Ver `.env.example` para lista completa.

## 🔍 Endpoints Principais

### Autenticação
- `POST /api/auth/register/` - Registro de usuário
- `POST /api/auth/login/` - Login (retorna JWT)
- `POST /api/auth/refresh/` - Refresh token

### Banking (Pluggy)
- `GET /api/banking/accounts/` - Listar contas bancárias
- `GET /api/banking/transactions/` - Listar transações
- `POST /api/banking/sync/` - Sincronizar dados
- `POST /api/banking/webhooks/pluggy/` - Webhook do Pluggy

### Subscriptions (Stripe)
- `GET /api/subscriptions/status/` - Status da assinatura
- `POST /api/subscriptions/checkout/` - Criar checkout
- `POST /api/subscriptions/portal/` - Portal do cliente
- `POST /stripe/webhook/` - Webhook do Stripe

### Reports
- `GET /api/reports/dashboard/` - Dashboard financeiro
- `GET /api/reports/transactions/` - Relatório de transações
- `POST /api/reports/export/` - Exportar relatório (PDF/Excel)

## 🧪 Testes

```bash
# Rodar todos os testes
python manage.py test

# Testar app específico
python manage.py test apps.banking

# Com coverage
coverage run --source='.' manage.py test
coverage report
```

## 🐛 Troubleshooting

### Erro: "DJANGO_SECRET_KEY not set"
```bash
# Gerar secret key
python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'
```

### Erro: "Database connection failed"
```bash
# Verificar DATABASE_URL
python manage.py check --database default

# Testar PostgreSQL local
psql $DATABASE_URL
```

### Migrations não aplicadas
```bash
python manage.py showmigrations
python manage.py migrate --verbosity 3
```

## 📚 Documentação

- [Django Rest Framework](https://www.django-rest-framework.org/)
- [Simple JWT](https://django-rest-framework-simplejwt.readthedocs.io/)
- [Pluggy API](https://docs.pluggy.ai/)
- [Stripe API](https://stripe.com/docs/api)
- [dj-stripe](https://dj-stripe.dev/)

## 🤝 Contribuindo

1. Criar branch: `git checkout -b feature/nova-funcionalidade`
2. Commit: `git commit -m 'feat: adiciona nova funcionalidade'`
3. Push: `git push origin feature/nova-funcionalidade`
4. Abrir Pull Request

## 📝 Convenções

- **Commits:** Conventional Commits (feat, fix, docs, etc)
- **Code Style:** PEP 8 (use `black` para formatação)
- **Imports:** isort para ordenação
- **Type Hints:** Usar quando possível
