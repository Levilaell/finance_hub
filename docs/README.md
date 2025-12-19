# CaixaHub - Documentacao Tecnica

Sistema de gestao financeira para PMEs brasileiras com integracao bancaria automatica, analise com IA e relatorios gerenciais.

## Indice

### Arquitetura
- [Visao Geral da Arquitetura](./architecture.md) - Stack, fluxo de dados, infraestrutura

### Funcionalidades

| Funcionalidade | Descricao | Documentacao |
|----------------|-----------|--------------|
| Autenticacao | Login, registro, JWT, recuperacao de senha | [auth.md](./features/auth.md) |
| Conexao Bancaria | Integracao Pluggy, sincronizacao de contas | [banking-connection.md](./features/banking-connection.md) |
| Transacoes | Listagem, categorizacao, regras automaticas | [transactions.md](./features/transactions.md) |
| Categorias | CRUD de categorias e subcategorias | [categories.md](./features/categories.md) |
| Contas a Pagar/Receber | Bills, pagamentos parciais, OCR de boletos | [bills.md](./features/bills.md) |
| Relatorios | DRE, fluxo de caixa, analise por categoria | [reports.md](./features/reports.md) |
| AI Insights | Analise financeira com IA, health score | [ai-insights.md](./features/ai-insights.md) |
| Assinaturas | Stripe, trial, planos | [subscriptions.md](./features/subscriptions.md) |
| Dashboard | Visao geral financeira | [dashboard.md](./features/dashboard.md) |

### API Reference

| Modulo | Endpoints | Documentacao |
|--------|-----------|--------------|
| Autenticacao | `/api/auth/*` | [auth-api.md](./api/auth.md) |
| Banking | `/api/banking/*` | [banking-api.md](./api/banking.md) |
| AI Insights | `/api/ai-insights/*` | [ai-insights-api.md](./api/ai-insights.md) |
| Subscriptions | `/api/subscriptions/*` | [subscriptions-api.md](./api/subscriptions.md) |
| Reports | `/api/reports/*` | [reports-api.md](./api/reports.md) |
| Companies | `/api/companies/*` | [companies-api.md](./api/companies.md) |

### Integracoes Externas
- [Pluggy](./features/banking-connection.md#integracao-pluggy) - Agregador bancario
- [Stripe](./features/subscriptions.md#integracao-stripe) - Pagamentos e assinaturas
- [OpenAI](./features/ai-insights.md#integracao-openai) - Analise com IA

---

## Stack Tecnologico

### Backend
- **Framework**: Django 4.x + Django Rest Framework
- **Banco de Dados**: PostgreSQL
- **Fila Assincrona**: Celery + Redis
- **Autenticacao**: JWT (SimpleJWT)

### Frontend
- **Framework**: Next.js 14 (App Router)
- **UI**: Tailwind CSS + Shadcn/ui
- **State**: Zustand + React Query
- **Graficos**: Recharts

### Infraestrutura
- **Deploy**: Railway
- **CDN/Storage**: (configuravel)

---

## Estrutura do Projeto

```
finance_hub/
├── backend/
│   ├── apps/
│   │   ├── authentication/   # Usuarios, login, JWT
│   │   ├── banking/          # Contas, transacoes, categorias, bills
│   │   ├── ai_insights/      # Analise com IA
│   │   ├── subscriptions/    # Stripe, trial
│   │   ├── companies/        # Dados da empresa
│   │   └── reports/          # Relatorios financeiros
│   └── core/                 # Settings, middleware, URLs
├── frontend/
│   ├── app/                  # Paginas (Next.js App Router)
│   │   ├── (auth)/           # Login, registro
│   │   └── (dashboard)/      # Aplicacao principal
│   ├── components/           # Componentes React
│   ├── services/             # API clients
│   ├── hooks/                # Custom hooks
│   └── store/                # Zustand store
└── docs/                     # Esta documentacao
```

---

## Quick Start para Desenvolvedores

### Pre-requisitos
- Python 3.11+
- Node.js 18+
- PostgreSQL
- Redis

### Variaveis de Ambiente Necessarias

```bash
# Backend
DJANGO_SECRET_KEY=xxx
DATABASE_URL=postgres://...
REDIS_URL=redis://...
PLUGGY_CLIENT_ID=xxx
PLUGGY_CLIENT_SECRET=xxx
STRIPE_SECRET_KEY=xxx
OPENAI_API_KEY=xxx

# Frontend
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=xxx
```

### Executar Localmente

```bash
# Backend
cd backend
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver

# Celery (outro terminal)
celery -A core worker -l info

# Frontend
cd frontend
npm install
npm run dev
```

---

## Convencoes do Projeto

### Nomenclatura
- **Models**: PascalCase singular (`Transaction`, `BankAccount`)
- **Endpoints**: kebab-case plural (`/transactions/`, `/bank-accounts/`)
- **Componentes React**: PascalCase (`TransactionsList.tsx`)
- **Hooks**: camelCase com prefixo `use` (`useBanking.ts`)
- **Services**: camelCase com sufixo `Service` (`bankingService`)

### Commits
```
feat(module): descricao curta
fix(module): descricao curta
docs(module): descricao curta
```

---

## Contato e Suporte

Para duvidas sobre a arquitetura ou implementacao, consulte esta documentacao ou entre em contato com a equipe de desenvolvimento.
