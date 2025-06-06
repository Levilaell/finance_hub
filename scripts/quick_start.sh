#!/bin/bash

echo "⚡ QUICK START - Finance Management"
echo "=================================="

# Verificar se estamos no diretório correto
if [ ! -f "docker-compose.yml" ]; then
    echo "❌ Execute este script da raiz do projeto!"
    exit 1
fi

# Verificar se Docker está disponível
if command -v docker-compose &> /dev/null && docker info > /dev/null 2>&1; then
    echo "🐳 Usando Docker..."
    
    # Parar containers existentes
    docker-compose down -q 2>/dev/null
    
    # Subir todos os serviços
    echo "🚀 Iniciando todos os serviços..."
    docker-compose up -d
    
    # Aguardar um pouco
    sleep 5
    
    echo ""
    echo "✅ Sistema rodando!"
    echo "📱 Frontend: http://localhost:3000"
    echo "🔧 API: http://localhost:8000/api"
    echo ""
    echo "📝 Para parar: docker-compose down"
    
else
    echo "❌ Docker não disponível."
    echo ""
    echo "💡 Para uso sem Docker, execute em terminais separados:"
    echo ""
    echo "Terminal 1: cd backend && python manage.py runserver"
    echo "Terminal 2: cd frontend && npm run dev"
    echo ""
fi