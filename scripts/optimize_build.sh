#!/bin/bash
# Script para otimizar o build Docker

echo "🚀 Otimizando build Docker..."

# Fazer download das imagens base em paralelo
echo "📥 Baixando imagens base..."
docker pull python:3.11-slim &
docker pull node:18-alpine &
docker pull postgres:15-alpine &
docker pull redis:7-alpine &
docker pull nginx:alpine &
wait

# Build apenas o backend primeiro (mais demorado)
echo "🔨 Construindo backend..."
docker-compose build backend

# Build frontend
echo "🔨 Construindo frontend..."
docker-compose build frontend

# Build outros serviços
echo "🔨 Construindo outros serviços..."
docker-compose build

echo "✅ Build otimizado concluído!"