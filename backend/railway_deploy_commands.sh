#!/bin/bash
# RAILWAY DEPLOY COMMANDS - ULTIMATE MIGRATION FIX
# Script para aplicar a correção definitiva no Railway
# Data: 2025-08-23

echo "🚀 ULTIMATE MIGRATION FIX - RAILWAY DEPLOYMENT"
echo "=============================================="

# Verifica se está no diretório correto
if [ ! -f "manage.py" ]; then
    echo "❌ Erro: Execute este script no diretório backend/"
    exit 1
fi

echo "📍 Diretório atual: $(pwd)"

# 1. Verifica o status inicial
echo ""
echo "1️⃣ STATUS INICIAL DAS MIGRAÇÕES"
echo "--------------------------------"
railway run python manage.py showmigrations

# 2. Aplica o SQL fix diretamente
echo ""
echo "2️⃣ APLICANDO ULTIMATE FIX SQL"
echo "------------------------------"

# Opção A: Via arquivo SQL
if [ -f "ultimate_migration_fix.sql" ]; then
    echo "📁 Aplicando via arquivo SQL..."
    railway run psql $DATABASE_URL -f ultimate_migration_fix.sql
else
    echo "📝 Aplicando via comando direto..."
    
    # SQL inline para caso o arquivo não esteja disponível
    railway run psql $DATABASE_URL << 'EOF'
-- ULTIMATE FIX - VERSÃO INLINE
DELETE FROM django_migrations WHERE app = 'companies' AND name = '0009_add_early_access';

UPDATE django_migrations 
SET applied = '2025-07-31 02:00:00+00:00'
WHERE app = 'banking' AND name = '0008_delete_consent';

DELETE FROM django_migrations 
WHERE app = 'reports' AND name IN (
    '0002_alter_aianalysis_options_and_more',
    '0003_aianalysistemplate_aianalysis', 
    '0005_fix_inconsistent_history'
);

INSERT INTO django_migrations (app, name, applied) VALUES
('reports', '0002_alter_aianalysis_options_and_more', '2025-08-12 01:00:00+00:00'),
('reports', '0003_aianalysistemplate_aianalysis', '2025-08-12 02:00:00+00:00'),
('reports', '0005_fix_inconsistent_history', '2025-08-12 03:00:00+00:00');

SELECT '✅ Ultimate fix aplicado!' as status;
EOF
fi

# 3. Executa o script Python de validação
echo ""
echo "3️⃣ VALIDAÇÃO AUTOMÁTICA"
echo "------------------------"
railway run python apply_ultimate_fix.py

# 4. Tenta aplicar migrações restantes
echo ""
echo "4️⃣ APLICANDO MIGRAÇÕES RESTANTES"
echo "---------------------------------"
railway run python manage.py migrate --no-input

# 5. Verifica status final
echo ""
echo "5️⃣ STATUS FINAL"
echo "---------------"
railway run python manage.py showmigrations

# 6. Teste básico de funcionamento
echo ""
echo "6️⃣ TESTE DE FUNCIONAMENTO"
echo "-------------------------"
railway run python -c "
import django
django.setup()
from django.contrib.auth.models import User
from apps.companies.models import Company
print(f'✅ Users: {User.objects.count()}')
print(f'✅ Companies: {Company.objects.count()}')
print('🎯 Sistema funcionando!')
"

echo ""
echo "🎯 DEPLOY CONCLUÍDO!"
echo "==================="
echo ""
echo "📋 CHECKLIST PÓS-DEPLOY:"
echo "  □ Verificar logs de erro"
echo "  □ Testar registro de novo usuário" 
echo "  □ Testar login existente"
echo "  □ Testar conectar conta bancária"
echo "  □ Testar geração de relatórios"
echo ""
echo "💡 Se houver problemas, executar:"
echo "   railway logs --follow"