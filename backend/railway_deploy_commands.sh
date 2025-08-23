#!/bin/bash
# COMANDOS PARA DEPLOY SEGURO NO RAILWAY

echo "🚀 CHECKLIST DE DEPLOY RAILWAY - FINANCE HUB"
echo "============================================="

echo ""
echo "📋 PRÉ-DEPLOY CHECKLIST:"
echo "------------------------"

# 1. Backup do banco (sempre fazer antes de deploy crítico)
echo "1. 🗄️ BACKUP DO BANCO:"
echo "   railway run pg_dump > backup_$(date +%Y%m%d_%H%M%S).sql"

# 2. Verificar migrações pendentes
echo ""
echo "2. 🔍 VERIFICAR MIGRAÇÕES:"
echo "   railway shell"
echo "   python manage.py showmigrations | grep '\\[ \\]'"

# 3. Corrigir collation se necessário
echo ""
echo "3. 🔧 CORRIGIR COLLATION (se warnings nos logs):"
echo "   railway shell"
echo "   psql \$DATABASE_URL -c \"ALTER DATABASE railway REFRESH COLLATION VERSION;\""

# 4. Configurar variáveis críticas
echo ""
echo "4. ⚙️ CONFIGURAR VARIÁVEIS (Railway Dashboard → Variables):"
echo "   AI_INSIGHTS_ENCRYPTION_KEY=$(openssl rand -base64 32)"
echo "   PLUGGY_WEBHOOK_SECRET=$(openssl rand -base64 24)"

echo ""
echo "🚀 COMANDOS DE DEPLOY:"
echo "----------------------"

# 5. Deploy com migrações
echo "5. 📦 DEPLOY:"
echo "   git push railway main"
echo "   # Railway auto-executa: python manage.py migrate"

# 6. Validação pós-deploy
echo ""
echo "6. ✅ VALIDAÇÃO PÓS-DEPLOY:"
echo "   railway shell"
echo "   python validate_production_migrations.py"

# 7. Testes de smoke
echo ""
echo "7. 🧪 TESTES DE SMOKE:"
echo "   curl -f https://financehub-production.up.railway.app/api/health/"
echo "   curl -f https://financehub-production.up.railway.app/admin/"

echo ""
echo "🚨 EM CASO DE PROBLEMA:"
echo "----------------------"
echo "   railway rollback"
echo "   # ou"
echo "   railway shell"
echo "   python manage.py migrate <app> <migration_before_problem>"

echo ""
echo "📊 MONITORAMENTO:"
echo "----------------"
echo "   railway logs | grep -i error"
echo "   railway logs | grep -i migration"

echo ""
echo "✅ DEPLOY COMPLETO!"
echo "Verifique: https://financehub-production.up.railway.app/"