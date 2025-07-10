#!/bin/bash
# Quick start script for CaixaHub development environment

set -e

echo "🚀 Iniciando configuração do CaixaHub..."

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker não está instalado. Por favor, instale o Docker primeiro.${NC}"
    echo "Visite: https://docs.docker.com/get-docker/"
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}❌ Docker Compose não está instalado. Por favor, instale o Docker Compose primeiro.${NC}"
    echo "Visite: https://docs.docker.com/compose/install/"
    exit 1
fi

echo -e "${GREEN}✅ Docker e Docker Compose encontrados${NC}"

# Create .env files if they don't exist
if [ ! -f backend/.env ]; then
    echo -e "${YELLOW}📝 Criando arquivo .env do backend...${NC}"
    cp backend/.env.example backend/.env
    
    # Generate a random secret key
    SECRET_KEY=$(python3 -c 'import secrets; print(secrets.token_urlsafe(50))')
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        sed -i '' "s/your-secret-key-here/$SECRET_KEY/" backend/.env
    else
        # Linux
        sed -i "s/your-secret-key-here/$SECRET_KEY/" backend/.env
    fi
    
    echo -e "${GREEN}✅ Arquivo .env do backend criado${NC}"
else
    echo -e "${YELLOW}ℹ️  Arquivo .env do backend já existe${NC}"
fi

# Build and start containers
echo -e "${YELLOW}🐳 Construindo containers Docker...${NC}"
docker-compose build

echo -e "${YELLOW}🚀 Iniciando containers...${NC}"
docker-compose up -d

# Wait for services to be ready
echo -e "${YELLOW}⏳ Aguardando serviços iniciarem...${NC}"
sleep 10

# Run migrations
echo -e "${YELLOW}🗄️  Executando migrações do banco de dados...${NC}"
docker-compose exec backend python manage.py migrate

# Create default categories
echo -e "${YELLOW}📁 Criando categorias padrão...${NC}"
docker-compose exec backend python manage.py create_default_categories || true

# Create superuser
echo -e "${YELLOW}👤 Criando superusuário...${NC}"
docker-compose exec backend python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(email='admin@caixahub.com.br').exists():
    User.objects.create_superuser(
        username='admin@caixahub.com.br',
        email='admin@caixahub.com.br',
        password='admin123',
        first_name='Admin',
        last_name='CaixaHub'
    )
    print('Superusuário criado com sucesso')
else:
    print('Superusuário já existe')
"

# Collect static files
echo -e "${YELLOW}📦 Coletando arquivos estáticos...${NC}"
docker-compose exec backend python manage.py collectstatic --noinput

# Show status
echo -e "\n${GREEN}✅ Configuração concluída!${NC}\n"

echo -e "📍 URLs disponíveis:"
echo -e "   ${GREEN}Frontend:${NC} http://localhost:3000"
echo -e "   ${GREEN}Backend API:${NC} http://localhost:8000/api/"
echo -e "   ${GREEN}Django Admin:${NC} http://localhost:8000/admin/"
echo -e "   ${GREEN}Mailhog:${NC} http://localhost:8025"
echo -e "   ${GREEN}pgAdmin:${NC} http://localhost:5050"
echo -e "   ${GREEN}Redis Commander:${NC} http://localhost:8081"

echo -e "\n📧 Credenciais padrão:"
echo -e "   ${GREEN}Admin:${NC} admin@caixahub.com.br / admin123"
echo -e "   ${GREEN}pgAdmin:${NC} admin@caixahub.com.br / admin"

echo -e "\n📝 Comandos úteis:"
echo -e "   ${YELLOW}Ver logs:${NC} docker-compose logs -f"
echo -e "   ${YELLOW}Parar containers:${NC} docker-compose down"
echo -e "   ${YELLOW}Reiniciar:${NC} docker-compose restart"
echo -e "   ${YELLOW}Shell Django:${NC} docker-compose exec backend python manage.py shell"
echo -e "   ${YELLOW}Criar migrações:${NC} docker-compose exec backend python manage.py makemigrations"

echo -e "\n${GREEN}🎉 CaixaHub está pronto para uso!${NC}"