# Estrutura do Projeto CaixaHub

## 📁 Estrutura de Diretórios

```
finance_management/
├── backend/                    # API Django REST Framework
│   ├── apps/                  # Aplicações Django
│   │   ├── authentication/    # Autenticação JWT + 2FA
│   │   ├── banking/          # Integração bancária (Pluggy)
│   │   ├── categories/       # Categorização de transações
│   │   ├── companies/        # Multi-tenancy
│   │   ├── notifications/    # Notificações e WebSocket
│   │   ├── payments/         # Pagamentos (Stripe/MercadoPago)
│   │   └── reports/          # Relatórios financeiros
│   ├── core/                 # Configurações Django
│   ├── media/               # Uploads de usuários
│   ├── staticfiles/         # Arquivos estáticos coletados
│   ├── templates/           # Templates de email
│   └── tests/               # Testes organizados
│       ├── e2e/            # Testes end-to-end
│       ├── integration/    # Testes de integração
│       ├── performance/    # Testes de performance
│       └── security/       # Testes de segurança
│
├── frontend/                  # Aplicação Next.js 14
│   ├── app/                  # App Router do Next.js
│   │   ├── (auth)/          # Páginas de autenticação
│   │   │   ├── login/       # Login
│   │   │   ├── register/    # Registro
│   │   │   └── verify/      # Verificação de email
│   │   ├── (dashboard)/     # Área logada
│   │   │   ├── accounts/    # Contas bancárias
│   │   │   ├── categories/  # Categorias
│   │   │   ├── dashboard/   # Dashboard principal
│   │   │   ├── reports/     # Relatórios
│   │   │   ├── settings/    # Configurações
│   │   │   └── transactions/# Transações
│   │   └── banking/         # Integração bancária
│   ├── components/          # Componentes React
│   │   ├── accounts/       # Componentes de contas
│   │   ├── banking/        # Widgets bancários
│   │   ├── layouts/        # Layouts da aplicação
│   │   └── ui/            # Componentes UI (shadcn)
│   ├── hooks/              # Custom React hooks
│   ├── lib/               # Utilitários
│   ├── services/          # Serviços de API
│   │   ├── auth.service.ts
│   │   ├── banking.service.ts
│   │   ├── categories.service.ts
│   │   ├── dashboard.service.ts
│   │   ├── notifications.service.ts
│   │   ├── pluggy.service.ts
│   │   └── reports.service.ts
│   ├── store/             # Estado global (Zustand)
│   └── types/             # TypeScript types
│
├── nginx/                 # Configurações Nginx
├── scripts/               # Scripts de automação
├── docker-compose.yml     # Orquestração de containers
├── Makefile              # Comandos automatizados
└── README.md             # Documentação principal
```

## 🔧 Stack Tecnológica

### Backend
- **Framework**: Django 5.0.1 + Django REST Framework 3.14.0
- **Banco de Dados**: PostgreSQL 15 + Redis
- **Autenticação**: JWT (djangorestframework-simplejwt)
- **Tarefas Assíncronas**: Celery + Redis
- **WebSocket**: Django Channels
- **Testes**: pytest + Factory Boy

### Frontend
- **Framework**: Next.js 14.2.5 (App Router)
- **UI Library**: React 18 + TypeScript
- **Estilização**: TailwindCSS + shadcn/ui
- **Estado**: Zustand
- **Requisições**: Axios + React Query
- **Formulários**: React Hook Form + Zod

### Infraestrutura
- **Containerização**: Docker + Docker Compose
- **Proxy Reverso**: Nginx
- **CI/CD**: GitHub Actions (preparado)
- **Monitoramento**: Sentry (preparado)

## 📊 Status do Desenvolvimento

### ✅ Implementado (90%+)

#### Backend (95%)
- Sistema de autenticação completo (JWT + 2FA)
- Multi-tenancy com isolamento de dados
- Integração com Pluggy
- Categorização automática (regras + IA)
- Sistema de notificações em tempo real
- Geração de relatórios
- 728+ testes automatizados

#### Frontend (90%)
- Todas as páginas principais implementadas
- Integração com APIs do backend
- Componentes UI reutilizáveis
- Sistema de roteamento e autenticação
- Dashboard interativo
- Formulários de cadastro e edição

### ⏳ Pendente (10%)

#### Configurações de Produção
- API keys de produção (Stripe, MercadoPago, Pluggy)
- Configuração de domínio e SSL
- Setup de servidores de produção
- Configuração de backups automáticos

#### Ajustes Finais
- Testes de integração frontend/backend em produção
- Otimização de performance
- Documentação de usuário final
- Termos legais e políticas

## 🚀 Comandos Úteis

### Backend
```bash
cd backend

# Ambiente virtual
python -m venv venv
source venv/bin/activate

# Instalar dependências
pip install -r requirements.txt

# Migrações
python manage.py makemigrations
python manage.py migrate

# Criar superusuário
python manage.py createsuperuser

# Popular dados iniciais
python manage.py create_default_categories
python manage.py create_bank_providers
python manage.py create_subscription_plans

# Executar servidor
python manage.py runserver

# Executar testes
python manage.py test
```

### Frontend
```bash
cd frontend

# Instalar dependências
npm install

# Desenvolvimento
npm run dev

# Build de produção
npm run build
npm start

# Testes
npm test
```

### Docker
```bash
# Desenvolvimento
docker-compose up

# Produção
docker-compose -f docker-compose.production.yml up

# Rebuild
docker-compose build --no-cache
```

## 📝 Arquivos de Configuração

### Backend (.env)
```env
SECRET_KEY=your-secret-key
DEBUG=False
DATABASE_URL=postgresql://user:pass@localhost/db
REDIS_URL=redis://localhost:6379
FIELD_ENCRYPTION_KEY=your-encryption-key

# APIs
OPENAI_API_KEY=sk-xxx
PLUGGY_CLIENT_ID=xxx
PLUGGY_CLIENT_SECRET=xxx

# Email
EMAIL_HOST=smtp.gmail.com
EMAIL_HOST_USER=xxx
EMAIL_HOST_PASSWORD=xxx

# Pagamentos
STRIPE_SECRET_KEY=sk_xxx
MERCADOPAGO_ACCESS_TOKEN=xxx
```

### Frontend (.env.local)
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_PLUGGY_CONNECT_TOKEN=xxx
```

## 🔒 Segurança

- Autenticação JWT com refresh tokens
- Two-Factor Authentication (2FA)
- Criptografia de campos sensíveis
- Rate limiting em endpoints críticos
- CORS configurado
- Validação de dados em todas as entradas
- Logs de auditoria

## 📈 Métricas do Projeto

- **Linhas de código**: ~50.000+
- **Testes automatizados**: 728+
- **Cobertura de testes**: ~85%
- **APIs documentadas**: 100%
- **Tempo de desenvolvimento**: 6 meses
- **Pronto para produção**: 90%

## 🎯 Próximos Passos

1. Obter API keys de produção
2. Configurar infraestrutura
3. Deploy em ambiente de staging
4. Testes com usuários beta
5. Lançamento gradual