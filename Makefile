# Makefile for CaixaHub

.PHONY: help build up down restart logs shell migrate test clean

# Colors
GREEN := \033[0;32m
YELLOW := \033[1;33m
RED := \033[0;31m
NC := \033[0m

# Default target
help:
	@echo "$(GREEN)CaixaHub - Comandos disponíveis:$(NC)"
	@echo "  $(YELLOW)make build$(NC)        - Constrói os containers Docker"
	@echo "  $(YELLOW)make up$(NC)           - Inicia os containers"
	@echo "  $(YELLOW)make down$(NC)         - Para os containers"
	@echo "  $(YELLOW)make restart$(NC)      - Reinicia os containers"
	@echo "  $(YELLOW)make logs$(NC)         - Mostra os logs dos containers"
	@echo "  $(YELLOW)make shell$(NC)        - Abre shell do Django"
	@echo "  $(YELLOW)make migrate$(NC)      - Executa migrações do banco"
	@echo "  $(YELLOW)make test$(NC)         - Executa os testes"
	@echo "  $(YELLOW)make clean$(NC)        - Remove volumes e containers"
	@echo "  $(YELLOW)make quick-start$(NC)  - Configuração inicial rápida"

# Build containers
build:
	@echo "$(YELLOW)Construindo containers...$(NC)"
	docker-compose build

# Start containers
up:
	@echo "$(YELLOW)Iniciando containers...$(NC)"
	docker-compose up -d
	@echo "$(GREEN)Containers iniciados!$(NC)"
	@echo "Frontend: http://localhost:3000"
	@echo "Backend: http://localhost:8000"

# Stop containers
down:
	@echo "$(YELLOW)Parando containers...$(NC)"
	docker-compose down

# Restart containers
restart:
	@echo "$(YELLOW)Reiniciando containers...$(NC)"
	docker-compose restart

# Show logs
logs:
	docker-compose logs -f

# Django shell
shell:
	docker-compose exec backend python manage.py shell

# Run migrations
migrate:
	@echo "$(YELLOW)Executando migrações...$(NC)"
	docker-compose exec backend python manage.py migrate

# Create migrations
makemigrations:
	@echo "$(YELLOW)Criando migrações...$(NC)"
	docker-compose exec backend python manage.py makemigrations

# Run tests
test:
	@echo "$(YELLOW)Executando testes...$(NC)"
	docker-compose exec backend python manage.py test

# Run backend tests with coverage
test-backend:
	@echo "$(YELLOW)Executando testes do backend com cobertura...$(NC)"
	docker-compose exec backend coverage run --source='.' manage.py test
	docker-compose exec backend coverage report

# Clean everything
clean:
	@echo "$(RED)Removendo containers e volumes...$(NC)"
	docker-compose down -v
	@echo "$(GREEN)Limpeza concluída!$(NC)"

# Quick start
quick-start:
	@./scripts/quick_start.sh

# Development commands
dev-backend:
	docker-compose exec backend python manage.py runserver 0.0.0.0:8000

dev-celery:
	docker-compose exec celery celery -A core worker -l info

dev-frontend:
	docker-compose exec frontend npm run dev

# Production build
prod-build:
	@echo "$(YELLOW)Construindo para produção...$(NC)"
	docker-compose -f docker-compose.yml -f docker-compose.production.yml build

# Production deploy
prod-up:
	@echo "$(YELLOW)Iniciando em modo produção...$(NC)"
	docker-compose -f docker-compose.yml -f docker-compose.production.yml up -d

# Database backup
backup-db:
	@echo "$(YELLOW)Fazendo backup do banco de dados...$(NC)"
	@mkdir -p backups
	@docker-compose exec db pg_dump -U postgres finance_db | gzip > backups/backup_$(shell date +%Y%m%d_%H%M%S).sql.gz
	@echo "$(GREEN)Backup criado em backups/$(NC)"

# Restore database
restore-db:
	@echo "$(YELLOW)Restaurando banco de dados...$(NC)"
	@echo "$(RED)Uso: make restore-db FILE=backups/backup_YYYYMMDD_HHMMSS.sql.gz$(NC)"
	@[ -n "$(FILE)" ] || (echo "$(RED)Erro: Especifique o arquivo com FILE=...$(NC)" && exit 1)
	@gunzip -c $(FILE) | docker-compose exec -T db psql -U postgres finance_db

# Create superuser
createsuperuser:
	docker-compose exec backend python manage.py createsuperuser

# Collect static files
collectstatic:
	docker-compose exec backend python manage.py collectstatic --noinput

# Install/update dependencies
install-deps:
	docker-compose exec backend pip install -r requirements.txt
	docker-compose exec frontend npm install

# Format code
format:
	@echo "$(YELLOW)Formatando código Python...$(NC)"
	docker-compose exec backend black .
	docker-compose exec backend isort .

# Lint code
lint:
	@echo "$(YELLOW)Verificando código Python...$(NC)"
	docker-compose exec backend flake8 .
	docker-compose exec backend mypy .