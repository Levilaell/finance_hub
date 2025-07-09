#!/bin/bash
# Build rápido para desenvolvimento

echo "🛑 PARANDO build atual..."
docker-compose down

echo "🧹 Limpando cache Docker..."
docker system prune -f

echo "🚀 Build rápido - apenas serviços essenciais..."

# Criar versão simplificada do docker-compose
cat > docker-compose.simple.yml << 'EOF'
version: '3.8'

services:
  db:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: finance_db
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

volumes:
  postgres_data:
  redis_data:
EOF

echo "📦 Iniciando apenas banco e Redis..."
docker-compose -f docker-compose.simple.yml up -d

echo "✅ Serviços básicos rodando!"
echo "🔧 Agora você pode rodar backend/frontend localmente:"
echo ""
echo "Backend:"
echo "  cd backend"
echo "  python -m venv venv"
echo "  source venv/bin/activate"
echo "  pip install -r requirements.txt"
echo "  python manage.py migrate"
echo "  python manage.py runserver"
echo ""
echo "Frontend:"
echo "  cd frontend"
echo "  npm install"
echo "  npm run dev"