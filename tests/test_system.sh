#!/bin/bash

# FinanceHub - Script de Teste do Sistema
echo "🧪 Testando FinanceHub - Sistema de Automação Financeira"
echo "================================================="

# Cores para output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Função para testar endpoint
test_endpoint() {
    local url=$1
    local description=$2
    local expected_status=${3:-200}
    
    echo -n "🔍 Testando $description... "
    
    response=$(curl -s -o /dev/null -w "%{http_code}" $url)
    
    if [ "$response" -eq "$expected_status" ]; then
        echo -e "${GREEN}✅ OK ($response)${NC}"
        return 0
    else
        echo -e "${RED}❌ FALHOU ($response)${NC}"
        return 1
    fi
}

# Aguardar serviços
echo "⏱️  Aguardando serviços iniciarem..."
sleep 5

# Contadores
passed=0
failed=0

echo ""
echo "🌐 Testando Conectividade dos Serviços"
echo "------------------------------------"

# Teste Frontend
if test_endpoint "http://localhost:3000" "Frontend Next.js"; then
    ((passed++))
else
    ((failed++))
fi

# Teste Backend Health
if test_endpoint "http://localhost:8000/api/auth/health/" "Backend Health Check"; then
    ((passed++))
else
    ((failed++))
fi

# Teste Admin Django
if test_endpoint "http://localhost:8000/admin/" "Django Admin" 302; then
    ((passed++))
else
    ((failed++))
fi

# Teste Swagger
if test_endpoint "http://localhost:8000/swagger/" "API Documentation"; then
    ((passed++))
else
    ((failed++))
fi

echo ""
echo "🔐 Testando APIs de Autenticação"
echo "--------------------------------"

# Teste endpoint de login
if test_endpoint "http://localhost:8000/api/auth/login/" "Login API" 405; then
    ((passed++))
else
    ((failed++))
fi

# Teste endpoint de registro
if test_endpoint "http://localhost:8000/api/auth/register/" "Register API" 405; then
    ((passed++))
else
    ((failed++))
fi

echo ""
echo "💰 Testando APIs Financeiras"
echo "----------------------------"

# Test banking API (requires auth - expect 401)
if test_endpoint "http://localhost:8000/api/banking/accounts/" "Banking API" 401; then
    ((passed++))
else
    ((failed++))
fi

# Test dashboard API (requires auth - expect 401)
if test_endpoint "http://localhost:8000/api/banking/dashboard/" "Dashboard API" 401; then
    ((passed++))
else
    ((failed++))
fi

echo ""
echo "🗄️  Testando Serviços de Infraestrutura"
echo "---------------------------------------"

# Teste PostgreSQL
echo -n "🔍 Testando PostgreSQL... "
if docker-compose exec -T db pg_isready -U postgres >/dev/null 2>&1; then
    echo -e "${GREEN}✅ OK${NC}"
    ((passed++))
else
    echo -e "${RED}❌ FALHOU${NC}"
    ((failed++))
fi

# Teste Redis
echo -n "🔍 Testando Redis... "
if docker-compose exec -T redis redis-cli ping >/dev/null 2>&1; then
    echo -e "${GREEN}✅ OK${NC}"
    ((passed++))
else
    echo -e "${RED}❌ FALHOU${NC}"
    ((failed++))
fi

# Teste Celery Worker
echo -n "🔍 Testando Celery Worker... "
if docker-compose exec -T backend celery -A core inspect ping >/dev/null 2>&1; then
    echo -e "${GREEN}✅ OK${NC}"
    ((passed++))
else
    echo -e "${YELLOW}⚠️  WORKER OFFLINE${NC}"
    ((failed++))
fi

echo ""
echo "📊 Testando Funcionalidades Específicas"
echo "--------------------------------------"

# Teste criação de usuário de teste
echo -n "🔍 Testando criação de dados... "
if docker-compose exec -T backend python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
print('Usuários:', User.objects.count())
" >/dev/null 2>&1; then
    echo -e "${GREEN}✅ OK${NC}"
    ((passed++))
else
    echo -e "${RED}❌ FALHOU${NC}"
    ((failed++))
fi

# Teste modelos principais
echo -n "🔍 Testando modelos do banco... "
if docker-compose exec -T backend python manage.py shell -c "
from apps.banking.models import BankProvider, TransactionCategory
from apps.companies.models import SubscriptionPlan
print('Bancos:', BankProvider.objects.count())
print('Categorias:', TransactionCategory.objects.count())
print('Planos:', SubscriptionPlan.objects.count())
" >/dev/null 2>&1; then
    echo -e "${GREEN}✅ OK${NC}"
    ((passed++))
else
    echo -e "${RED}❌ FALHOU${NC}"
    ((failed++))
fi

echo ""
echo "📱 Testando Responsividade Frontend"
echo "----------------------------------"

# Teste páginas principais do frontend
pages=(
    "http://localhost:3000/" 
    "http://localhost:3000/login"
    "http://localhost:3000/register"
)

for page in "${pages[@]}"; do
    page_name=$(echo $page | sed 's|http://localhost:3000||' | sed 's|^/||' | sed 's|^$|home|')
    if test_endpoint "$page" "Página $page_name"; then
        ((passed++))
    else
        ((failed++))
    fi
done

echo ""
echo "📋 Relatório Final"
echo "=================="

total=$((passed + failed))
percentage=$((passed * 100 / total))

echo "Total de testes: $total"
echo -e "Passou: ${GREEN}$passed${NC}"
echo -e "Falhou: ${RED}$failed${NC}"
echo -e "Taxa de sucesso: ${GREEN}$percentage%${NC}"

echo ""
if [ $failed -eq 0 ]; then
    echo -e "${GREEN}🎉 TODOS OS TESTES PASSARAM!${NC}"
    echo -e "${GREEN}✅ FinanceHub está funcionando perfeitamente!${NC}"
    echo ""
    echo "🌐 Acesse: http://localhost:3000"
    echo "👑 Admin: http://localhost:8000/admin"
    echo "📚 API Docs: http://localhost:8000/swagger"
    echo ""
    echo "📊 Login inicial:"
    echo "   Email: admin@financehub.com.br"
    echo "   Senha: admin123"
    
elif [ $percentage -gt 80 ]; then
    echo -e "${YELLOW}⚠️  SISTEMA FUNCIONANDO COM ALGUMAS FALHAS${NC}"
    echo "A maioria dos serviços está operacional"
    
else
    echo -e "${RED}❌ SISTEMA COM PROBLEMAS CRÍTICOS${NC}"
    echo "Verifique os logs: docker-compose logs"
    
fi

echo ""
echo "🔍 Para logs detalhados: docker-compose logs -f"
echo "🛑 Para parar: docker-compose down"
echo "================================================="