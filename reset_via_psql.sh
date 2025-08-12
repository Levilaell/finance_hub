#!/bin/bash

echo "🔴 RESET DO BANCO DE PRODUÇÃO"
echo "================================"
echo ""
echo "⚠️  ATENÇÃO: Isso vai DELETAR TODOS OS DADOS!"
echo "Pressione Ctrl+C para cancelar ou Enter para continuar..."
read

# Pegar a DATABASE_URL do Railway
echo "📊 Obtendo informações de conexão..."
DATABASE_URL=$(railway variables --json | python3 -c "import json; import sys; data = json.load(sys.stdin); print(data.get('DATABASE_URL', ''))")

if [ -z "$DATABASE_URL" ]; then
    echo "❌ Erro: Não foi possível obter DATABASE_URL"
    echo "Certifique-se de estar no diretório correto e conectado ao Railway"
    exit 1
fi

echo "🔄 Conectando ao banco de produção..."
echo ""

# Executar o reset
psql "$DATABASE_URL" < RESET_PRODUCTION_NOW.sql

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Reset completo!"
    echo ""
    echo "Agora execute no Railway:"
    echo "1. Faça redeploy do serviço"
    echo "2. Ou adicione FORCE_DB_RESET=true nas variáveis temporariamente"
else
    echo "❌ Erro ao executar reset"
fi