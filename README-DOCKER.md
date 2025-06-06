# 🚀 FinanceHub - Docker Setup

**FinanceHub** é um sistema SaaS de automação financeira para micro empresas brasileiras que conecta automaticamente com bancos via Open Banking e usa IA para categorizar transações.

## 🐳 Quick Start com Docker

### 1. Pré-requisitos
- Docker (versão 20.10+)
- Docker Compose (versão 2.0+)
- 4GB RAM disponível
- Portas livres: 3000, 8000, 5432, 6379, 80

### 2. Iniciar o FinanceHub

```bash
# Clone o repositório (se ainda não tiver)
cd /Users/levilaell/Desktop/finance_management

# Inicie todos os serviços
docker-compose -f docker-compose.financehub.yml up -d

# Aguarde todos os containers iniciarem (1-2 minutos)
docker-compose -f docker-compose.financehub.yml logs -f
```

### 3. Configuração Inicial

Após todos os containers estarem rodando:

```bash
# Execute as migrações e crie dados de teste
docker-compose -f docker-compose.financehub.yml exec backend python manage.py migrate
docker-compose -f docker-compose.financehub.yml exec backend python manage.py collectstatic --noinput
docker-compose -f docker-compose.financehub.yml exec backend python manage.py createsuperuser

# Crie dados de teste do FinanceHub
docker-compose -f docker-compose.financehub.yml exec backend python manage.py shell -c "
from django.contrib.auth import get_user_model
from apps.companies.models import Company
from apps.banking.models import BankProvider, BankAccount, Transaction, TransactionCategory
from decimal import Decimal
from django.utils import timezone
from datetime import timedelta

User = get_user_model()
user = User.objects.first()

# Create company
company, _ = Company.objects.get_or_create(
    owner=user,
    defaults={'name': 'Tech Solutions ME', 'document': '12.345.678/0001-90'}
)

print('✅ FinanceHub setup completed!')
print('🌐 Frontend: http://localhost:3000')
print('🔧 Backend: http://localhost:8000')
print('📊 Admin: http://localhost:8000/admin')
"
```

## 🌐 Acessos

- **Frontend (Next.js)**: http://localhost:3000
- **Backend API (Django)**: http://localhost:8000
- **Admin Panel**: http://localhost:8000/admin
- **API Docs**: http://localhost:8000/api/docs

## 📊 Serviços Inclusos

| Serviço | Descrição | Porta | Status |
|---------|-----------|-------|--------|
| **frontend** | Interface Next.js | 3000 | ✅ |
| **backend** | API Django | 8000 | ✅ |
| **db** | PostgreSQL 15 | 5432 | ✅ |
| **redis** | Cache + Celery | 6379 | ✅ |
| **celery_worker** | Tarefas background | - | ✅ |
| **celery_beat** | Tarefas agendadas | - | ✅ |
| **nginx** | Reverse proxy | 80, 443 | ✅ |

## 🔧 Comandos Úteis

### Status dos Containers
```bash
docker-compose -f docker-compose.financehub.yml ps
```

### Logs em Tempo Real
```bash
# Todos os serviços
docker-compose -f docker-compose.financehub.yml logs -f

# Apenas backend
docker-compose -f docker-compose.financehub.yml logs -f backend

# Apenas frontend  
docker-compose -f docker-compose.financehub.yml logs -f frontend
```

### Django Management Commands
```bash
# Entrar no container do backend
docker-compose -f docker-compose.financehub.yml exec backend bash

# Rodar migrações
docker-compose -f docker-compose.financehub.yml exec backend python manage.py migrate

# Criar superusuário
docker-compose -f docker-compose.financehub.yml exec backend python manage.py createsuperuser

# Shell do Django
docker-compose -f docker-compose.financehub.yml exec backend python manage.py shell
```

### Parar e Limpar
```bash
# Parar todos os serviços
docker-compose -f docker-compose.financehub.yml down

# Parar e remover volumes (CUIDADO: apaga dados!)
docker-compose -f docker-compose.financehub.yml down -v

# Rebuild completo
docker-compose -f docker-compose.financehub.yml build --no-cache
```

## 🔍 Troubleshooting

### Frontend retorna erro 500
```bash
# Verificar logs do backend
docker-compose -f docker-compose.financehub.yml logs backend

# Verificar se banco está funcionando
docker-compose -f docker-compose.financehub.yml exec db psql -U financehub -d financehub -c "SELECT 1;"
```

### Banco não conecta
```bash
# Verificar status do PostgreSQL
docker-compose -f docker-compose.financehub.yml exec db pg_isready -U financehub

# Reconstruir container do banco
docker-compose -f docker-compose.financehub.yml down
docker volume rm finance_management_postgres_data
docker-compose -f docker-compose.financehub.yml up -d db
```

### Rebuild após mudanças
```bash
# Rebuild apenas backend
docker-compose -f docker-compose.financehub.yml build backend
docker-compose -f docker-compose.financehub.yml up -d backend

# Rebuild apenas frontend
docker-compose -f docker-compose.financehub.yml build frontend
docker-compose -f docker-compose.financehub.yml up -d frontend
```

## 🏢 Dados de Teste

O sistema vem com dados realistas de uma micro empresa de tecnologia:

- **Empresa**: Tech Solutions ME
- **Contas**: Itaú PJ, Nubank PJ
- **Transações**: 22+ transações categorizadas por IA
- **Categorias**: 12+ categorias específicas para micro empresas
- **Receitas**: R$ 31.650,00 (serviços de desenvolvimento)
- **Despesas**: R$ 41.246,20 (salários, aluguel, etc.)

## 🤖 IA e Automação

- ✅ Categorização automática de transações (95% confiança)
- ✅ Open Banking para 5+ bancos brasileiros
- ✅ Sincronização automática de dados
- ✅ Insights e alertas inteligentes
- ✅ Previsões de fluxo de caixa

## 🚀 Produção

Para produção, use:
```bash
docker-compose -f docker-compose.production.yml up -d
```

---

**FinanceHub** - O sistema financeiro que funciona sozinho! 💰🤖