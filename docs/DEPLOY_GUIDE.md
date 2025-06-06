# 🚀 Guia de Deploy - FinanceHub

Sistema SaaS de automação financeira para micro empresas brasileiras com Open Banking e IA.

## 📋 Pré-requisitos

- Docker 20.10+
- Docker Compose 2.0+
- 4GB RAM mínimo
- 10GB espaço em disco

## 🔧 Configuração Rápida

### 1. Clone e Configuração

```bash
git clone <seu-repo>
cd finance_management
```

### 2. Configuração de Ambiente

```bash
# Copie o arquivo de configuração
cp .env.docker .env

# Edite as configurações se necessário
nano .env
```

### 3. Execução com Docker

```bash
# Torna o script executável
chmod +x start_development.sh

# Executa o setup completo
./start_development.sh
```

## 🌐 Acesso ao Sistema

Após a execução bem-sucedida:

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000/api
- **Documentação API**: http://localhost:8000/swagger
- **Admin Django**: http://localhost:8000/admin

### 👤 Login Inicial

- **Email**: admin@financehub.com.br
- **Senha**: admin123

## 🏗️ Arquitetura

### Backend (Django)
- **Autenticação**: JWT + 2FA opcional
- **Open Banking**: Integração mock (pronto para produção)
- **IA**: Categorização automática de transações
- **APIs**: REST com documentação Swagger

### Frontend (Next.js)
- **Framework**: Next.js 15 com App Router
- **Styling**: Tailwind CSS + Shadcn/ui
- **Estado**: Zustand + React Query
- **Formulários**: React Hook Form + Zod

### Infraestrutura
- **Banco**: PostgreSQL 15
- **Cache**: Redis 7
- **Queue**: Celery com Redis
- **Containers**: Docker + Docker Compose

## 🔄 Comandos Úteis

### Desenvolvimento

```bash
# Ver logs
docker-compose logs -f

# Parar serviços
docker-compose down

# Rebuild containers
docker-compose build --no-cache

# Executar migrações
docker-compose exec backend python manage.py migrate

# Criar superusuário
docker-compose exec backend python manage.py createsuperuser

# Acessar shell Django
docker-compose exec backend python manage.py shell

# Acessar banco
docker-compose exec db psql -U postgres -d caixa_digital
```

### Produção

```bash
# Deploy em produção
docker-compose -f docker-compose.production.yml up -d

# Backup do banco
docker-compose exec db pg_dump -U postgres caixa_digital > backup.sql

# Restore do banco
cat backup.sql | docker-compose exec -T db psql -U postgres caixa_digital
```

## 🛠️ Funcionalidades Implementadas

### ✅ Core Features
- [x] Autenticação JWT com 2FA
- [x] Dashboard financeiro em tempo real
- [x] Integração Open Banking (mock)
- [x] Categorização IA de transações
- [x] Sistema de notificações
- [x] Relatórios financeiros básicos
- [x] Gestão de contas bancárias
- [x] Metas financeiras
- [x] Orçamentos

### ✅ APIs Implementadas
- [x] `/api/auth/` - Autenticação completa
- [x] `/api/banking/` - Contas e transações
- [x] `/api/categories/` - Categorização
- [x] `/api/dashboard/` - Dashboard data
- [x] `/api/reports/` - Relatórios
- [x] `/api/notifications/` - Notificações

### ✅ Frontend Implementado
- [x] Páginas de autenticação
- [x] Dashboard principal
- [x] Gestão de contas
- [x] Categorização de transações
- [x] Relatórios básicos
- [x] Configurações

## 🔧 Configurações Avançadas

### Variáveis de Ambiente

```bash
# Banco de dados
DB_NAME=caixa_digital
DB_USER=postgres
DB_PASSWORD=postgres123
DB_HOST=db
DB_PORT=5432

# Redis
REDIS_URL=redis://redis:6379/0

# Django
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0

# APIs externas
OPENAI_API_KEY=sk-your-openai-key
OPEN_BANKING_CLIENT_ID=your-client-id
OPEN_BANKING_CLIENT_SECRET=your-client-secret

# Email
EMAIL_HOST=smtp.gmail.com
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
```

### Customizações

#### Adicionar Novos Bancos

```python
# backend/apps/banking/management/commands/add_bank.py
from apps.banking.models import BankProvider

BankProvider.objects.create(
    name='Novo Banco',
    code='999',
    color='#FF0000',
    is_open_banking=True
)
```

#### Novas Categorias

```python
# Via admin Django ou API
{
    "name": "Nova Categoria",
    "category_type": "expense",
    "icon": "💰",
    "color": "#FF0000",
    "keywords": ["palavra", "chave"]
}
```

## 🚨 Troubleshooting

### Problemas Comuns

#### 1. Containers não sobem
```bash
# Verificar logs
docker-compose logs

# Limpar volumes
docker-compose down -v
docker system prune -f
```

#### 2. Erro de migrações
```bash
# Reset migrações
docker-compose exec backend python manage.py migrate --fake-initial
```

#### 3. Frontend não conecta
```bash
# Verificar variáveis de ambiente
echo $NEXT_PUBLIC_API_URL

# Rebuild frontend
docker-compose build frontend
```

#### 4. Erro de permissões
```bash
# Fix permissões (Linux/Mac)
sudo chown -R $USER:$USER .
```

## 📊 Monitoramento

### Health Checks

```bash
# Backend
curl http://localhost:8000/api/auth/health/

# Frontend
curl http://localhost:3000/api/health

# Banco
docker-compose exec db pg_isready -U postgres
```

### Logs Importantes

```bash
# Aplicação
docker-compose logs backend frontend

# Banco
docker-compose logs db

# Celery
docker-compose logs celery_worker celery_beat
```

## 🔒 Segurança

### Produção
- [ ] Alterar SECRET_KEY
- [ ] Configurar HTTPS
- [ ] Usar banco externo
- [ ] Configurar backups
- [ ] Monitoramento
- [ ] Rate limiting

### Configurações Recomendadas

```bash
# .env.production
DEBUG=False
SECRET_KEY=super-secret-key-here
ALLOWED_HOSTS=yourdomain.com
DATABASE_URL=postgresql://user:pass@host:5432/db
REDIS_URL=redis://redis-host:6379/0
```

## 📞 Suporte

### Contato
- **Email**: suporte@financehub.com.br
- **Documentação**: Acesse /swagger quando rodando

### Contribuições
1. Fork o projeto
2. Crie uma branch (`git checkout -b feature/nova-feature`)
3. Commit suas mudanças (`git commit -am 'Adiciona nova feature'`)
4. Push para branch (`git push origin feature/nova-feature`)
5. Abra um Pull Request

---

## 🎯 Próximos Passos

1. **WebSockets**: Notificações em tempo real
2. **Relatórios Avançados**: PDFs e dashboards
3. **Mobile**: App React Native
4. **ML**: Melhorar IA de categorização
5. **Integrações**: Contabilidade, ERP

## ⚡ Quick Commands

```bash
# Start everything
./start_development.sh

# Stop everything
docker-compose down

# View logs
docker-compose logs -f

# Reset everything
docker-compose down -v && docker-compose build --no-cache && ./start_development.sh
```

🎉 **FinanceHub está pronto para produção!**