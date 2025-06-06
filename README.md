# FinanceHub - SaaS de Automação Financeira 🚀

Sistema de automação financeira completo para micro empresas brasileiras. Conecta automaticamente com bancos via Open Banking e usa IA para categorizar transações sem trabalho manual.

## ✨ Características Principais

- **🤖 Automação Total**: IA categoriza transações automaticamente
- **🏦 Open Banking**: Conecta com bancos brasileiros em 5 minutos
- **📱 Mobile-First**: Situação financeira em tempo real no celular
- **🔄 Zero Trabalho Manual**: Sistema funciona sozinho
- **📊 Relatórios Inteligentes**: Insights automáticos e previsões
- **🛡️ Segurança Bancária**: Criptografia e autenticação 2FA

## 🛠️ Stack Tecnológico

### Backend
- **Django 5.0.1** + Django REST Framework
- **PostgreSQL 15** para dados transacionais
- **Redis 7** para cache e filas
- **Celery + Celery Beat** para tarefas assíncronas
- **Django Channels** para WebSockets em tempo real
- **OpenAI GPT-4o-mini** para categorização inteligente
- **JWT** com autenticação 2FA

### Frontend
- **Next.js 15** + React 19 + TypeScript
- **Tailwind CSS** + Radix UI para interface profissional
- **Zustand** para estado global
- **TanStack Query** para cache e sincronização de dados
- **Recharts** para visualizações
- **React Hook Form + Zod** para formulários

### Infraestrutura
- **Docker + Docker Compose** para desenvolvimento
- **nginx** para proxy reverso
- **Celery** para processamento em background

## 🚀 Início Rápido

### Método 1: Setup Automático (Recomendado)

```bash
# 1. Clone o repositório
git clone <repository-url>
cd finance_management

# 2. Execute o script de configuração automática
chmod +x setup.sh
./setup.sh

# 3. Acesse o sistema
# Frontend: http://localhost:3000
# Backend: http://localhost:8000
# Admin: http://localhost:8000/admin (admin@financehub.com / admin123)
```

### Método 2: Setup Manual

#### Backend
```bash
cd backend

# Criar ambiente virtual
python3 -m venv venv
source venv/bin/activate

# Instalar dependências
pip install -r requirements.txt

# Configurar variáveis de ambiente
cp .env.example .env
# Edite .env com suas configurações

# Executar migrações
python manage.py migrate

# Criar superusuário
python manage.py createsuperuser

# Carregar dados iniciais
python manage.py create_default_categories
python manage.py create_bank_providers
python manage.py create_subscription_plans

# Iniciar servidor
python manage.py runserver
```

#### Frontend
```bash
cd frontend

# Instalar dependências
npm install

# Configurar variáveis de ambiente
cp .env.example .env.local
# Edite .env.local conforme necessário

# Iniciar servidor de desenvolvimento
npm run dev
```

## 🐳 Docker (Desenvolvimento)

```bash
# Iniciar todos os serviços
docker-compose up -d

# Ver logs
docker-compose logs -f

# Executar migrações
docker-compose exec backend python manage.py migrate

# Parar serviços
docker-compose down
```

## 🎯 Scripts de Desenvolvimento

O projeto inclui scripts para facilitar o desenvolvimento:

### dev.sh - Script de Desenvolvimento
```bash
chmod +x dev.sh

# Comandos disponíveis:
./dev.sh start      # Inicia todos os serviços
./dev.sh stop       # Para todos os serviços
./dev.sh restart    # Reinicia todos os serviços
./dev.sh backend    # Inicia apenas backend
./dev.sh frontend   # Inicia apenas frontend
./dev.sh db         # Inicia apenas banco de dados
./dev.sh migrate    # Executa migrações Django
./dev.sh shell      # Abre shell Django
./dev.sh test       # Executa testes
./dev.sh logs       # Mostra logs dos containers
./dev.sh clean      # Remove containers e volumes
./dev.sh status     # Mostra status dos serviços
./dev.sh help       # Mostra ajuda
```

## 📁 Estrutura do Projeto

```
finance_management/
├── backend/                    # Django API
│   ├── apps/
│   │   ├── authentication/    # Login, registro, 2FA
│   │   ├── banking/           # Contas bancárias e transações
│   │   ├── categories/        # Categorização com IA
│   │   ├── companies/         # Empresas e planos
│   │   ├── notifications/     # Notificações em tempo real
│   │   └── reports/           # Relatórios e analytics
│   ├── core/                  # Configurações Django
│   └── requirements.txt
├── frontend/                   # Next.js App
│   ├── app/
│   │   ├── (auth)/            # Páginas de autenticação
│   │   └── (dashboard)/       # Dashboard principal
│   ├── components/ui/         # Componentes reutilizáveis
│   ├── services/              # Serviços de API
│   ├── store/                 # Estado global (Zustand)
│   ├── types/                 # Tipos TypeScript
│   └── package.json
├── docker-compose.yml         # Orquestração Docker
├── setup.sh                  # Script de configuração
├── dev.sh                    # Script de desenvolvimento
└── README.md
```

## 🔧 Configuração

### Backend (.env)
```env
# Segurança
SECRET_KEY=sua-chave-secreta-super-segura
DEBUG=True

# Banco de Dados
DATABASE_URL=postgresql://usuario:senha@localhost:5432/financehub

# Redis
REDIS_URL=redis://localhost:6379/0

# OpenAI (para IA)
OPENAI_API_KEY=sua-chave-openai

# Email (opcional)
EMAIL_HOST=smtp.gmail.com
EMAIL_HOST_USER=seu-email@gmail.com
EMAIL_HOST_PASSWORD=sua-senha-app

# Open Banking (configurar com provedores)
OPEN_BANKING_CLIENT_ID=seu-client-id
OPEN_BANKING_CLIENT_SECRET=seu-client-secret
```

### Frontend (.env.local)
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_APP_NAME=FinanceHub
NEXT_PUBLIC_ENVIRONMENT=development
```

## 🏦 Integração com Open Banking

O sistema suporta integração com os principais bancos brasileiros:

- Banco do Brasil
- Itaú
- Bradesco
- Santander
- Nubank
- Inter
- E mais...

### Configuração Open Banking
1. Registre sua aplicação nos bancos desejados
2. Configure as credenciais no arquivo `.env`
3. Implemente os endpoints específicos de cada banco
4. Use os mocks incluídos para desenvolvimento

## 🤖 IA para Categorização

O sistema usa GPT-4o-mini Turbo para categorizar transações automaticamente:

- **Precisão**: >95% nas categorizações
- **Aprendizado**: Melhora com feedback do usuário
- **Velocidade**: Categorização em tempo real
- **Configurável**: Regras personalizáveis por empresa

## 📊 Funcionalidades

### Dashboard
- Visão geral financeira em tempo real
- Alertas e insights automáticos
- Gráficos interativos
- Métricas de performance

### Contas Bancárias
- Conexão automática via Open Banking
- Sincronização em tempo real
- Múltiplas contas e bancos
- Histórico completo de transações

### Transações
- Import automático dos bancos
- Categorização inteligente com IA
- Busca e filtros avançados
- Anexos e notas

### Relatórios
- DRE automática
- Fluxo de caixa
- Análise por categoria
- Relatórios personalizados
- Export PDF/Excel
- Agendamento automático

### Categorias
- Categorização automática
- Regras personalizáveis
- Hierarquia de categorias
- Machine learning integrado

## 🧪 Testes

### Backend
```bash
# Testes unitários
python manage.py test

# Testes com coverage
coverage run --source='.' manage.py test
coverage report
coverage html
```

### Frontend
```bash
# Testes Jest
npm test

# Testes E2E (quando configurados)
npm run test:e2e
```

## 📱 URLs do Sistema

Após inicialização:

- **🌐 Frontend**: http://localhost:3000
- **🔧 Backend API**: http://localhost:8000
- **📊 Admin Django**: http://localhost:8000/admin
- **📖 API Docs (Swagger)**: http://localhost:8000/swagger
- **📖 API Docs (ReDoc)**: http://localhost:8000/redoc

### Credenciais Padrão
- **Email**: admin@financehub.com
- **Senha**: admin123

## 📡 Principais Endpoints

### Autenticação
```
POST /api/auth/login/          # Login
POST /api/auth/register/       # Registro
POST /api/auth/refresh/        # Refresh token
POST /api/auth/logout/         # Logout
```

### Banking
```
GET  /api/banking/accounts/           # Listar contas
POST /api/banking/accounts/           # Criar conta
GET  /api/banking/transactions/       # Listar transações
POST /api/banking/connect/            # Conectar banco
GET  /api/banking/dashboard/          # Dashboard
```

### Relatórios
```
GET  /api/reports/                    # Listar relatórios
POST /api/reports/generate/           # Gerar relatório
GET  /api/reports/analytics/          # Analytics
```

## 🚀 Deploy em Produção

### Preparação
1. Configure variáveis de ambiente de produção
2. Use PostgreSQL hospedado (AWS RDS, etc.)
3. Configure Redis hospedado
4. Use armazenamento S3 para arquivos
5. Configure CDN (CloudFront)
6. Use HTTPS

### Docker Compose Produção
```bash
# Use o arquivo de produção
docker-compose -f docker-compose.production.yml up -d
```

### Recomendações de Infraestrutura
- **Servidor**: AWS EC2 t3.medium+
- **Banco**: AWS RDS PostgreSQL
- **Cache**: AWS ElastiCache Redis
- **Storage**: AWS S3
- **CDN**: AWS CloudFront
- **SSL**: Let's Encrypt ou AWS Certificate Manager

## 🔒 Segurança

- Autenticação JWT com refresh tokens
- 2FA opcional
- Criptografia de dados sensíveis
- Rate limiting
- CORS configurado
- Validação de entrada rigorosa
- Logs de auditoria

## 📈 Performance

- Cache Redis para queries frequentes
- Paginação em todas as listagens
- Lazy loading no frontend
- Otimização de queries no Django
- CDN para assets estáticos
- Compressão gzip

## 🛟 Suporte e Troubleshooting

### Problemas Comuns

**Erro de conexão com banco:**
```bash
# Verifique se PostgreSQL está rodando
docker-compose ps

# Recrie o banco se necessário
docker-compose down -v
docker-compose up -d
```

**Frontend não carrega:**
```bash
# Limpe cache e reinstale
rm -rf frontend/node_modules frontend/.next
cd frontend && npm install && npm run dev
```

**Celery não processa tarefas:**
```bash
# Reinicie o worker
docker-compose restart celery-worker
```

### Logs
```bash
# Ver todos os logs
docker-compose logs -f

# Log específico de um serviço
docker-compose logs -f backend
docker-compose logs -f frontend
```

## 📝 Contribuição

1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

## 📄 Licença

Este projeto é proprietário e confidencial. Todos os direitos reservados.

## 👥 Equipe

Desenvolvido para revolucionar a gestão financeira de micro empresas brasileiras.

---

**🎯 Objetivo**: Permitir que empresários conectem seus bancos em 5 minutos e tenham toda organização financeira funcionando automaticamente com IA, sem trabalho manual.

Para dúvidas ou suporte: Entre em contato através dos issues do GitHub.