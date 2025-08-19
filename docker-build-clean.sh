#!/bin/bash
# Script para limpar build cache e resolver problemas de deploy

echo "🧹 Limpando Docker build cache..."

# Limpar build cache do Docker
echo "Removendo build cache..."
docker builder prune -f

# Limpar todas as imagens não utilizadas
echo "Removendo imagens não utilizadas..."
docker image prune -a -f

# Limpar volumes não utilizados
echo "Removendo volumes não utilizados..."
docker volume prune -f

# Rebuild das imagens com --no-cache
echo "🔨 Rebuilding imagens sem cache..."

echo "Building backend..."
cd backend
docker build --no-cache -t finance-hub-backend .
cd ..

echo "Building frontend..."
cd frontend
docker build --no-cache -t finance-hub-frontend .
cd ..

echo "✅ Build limpo concluído!"
echo ""
echo "📋 Para deploy no Railway:"
echo "1. Faça commit das alterações"
echo "2. Push para o repositório"
echo "3. Railway irá rebuildar automaticamente"
echo ""
echo "🚨 Problemas comuns resolvidos:"
echo "  ✓ Docker build cache limpo"
echo "  ✓ Alpine package timeouts corrigidos"
echo "  ✓ Collectstatic configurado corretamente"
echo "  ✓ Dockerignore files criados"