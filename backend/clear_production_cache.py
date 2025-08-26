#!/usr/bin/env python
"""
Script to clear production cache for cash flow fix
This should be run after deployment to ensure new logic is used
"""

import os
import sys
import django
import requests

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.development')
sys.path.append('/Users/levilaell/Desktop/finance_hub/backend')

try:
    django.setup()
    from django.core.cache import cache
    
    print("=== LIMPEZA DE CACHE LOCAL ===")
    
    # Clear local cache
    cache.clear()
    print("✅ Cache local limpo")
    
    # Clear specific cash flow cache keys
    cache_patterns = [
        'cashflow_data_*',
        'cashflow_*',
        'dashboard_stats_*',
        'category_spending_*'
    ]
    
    for pattern in cache_patterns:
        try:
            cache.delete_pattern(pattern)
            print(f"✅ Padrão de cache limpo: {pattern}")
        except:
            print(f"⚠️  Não foi possível limpar: {pattern}")
    
except Exception as e:
    print(f"❌ Erro ao limpar cache local: {e}")

print("""
=== INSTRUÇÕES PARA PRODUÇÃO ===

1. 🚀 **Aguardar Deploy Railway** (2-3 minutos)
   - Acesse: https://railway.app/dashboard  
   - Verifique se o deploy finalizou com sucesso

2. 🧹 **Limpar Cache em Produção**
   - Execute via Railway CLI:
     railway run python manage.py shell -c "from django.core.cache import cache; cache.clear()"

3. 🔄 **Testar Endpoint**
   - URL: https://[seu-dominio]/api/reports/dashboard/cash-flow/
   - Parâmetros: ?start_date=2024-07-03&end_date=2024-07-30
   - Deve retornar dados não-vazios

4. 🎯 **Validar Frontend**  
   - Recarregar página de relatórios
   - Forçar refresh: Ctrl+F5 / Cmd+Shift+R
   - Verificar gráfico de Fluxo de Caixa

=== DETALHES DA CORREÇÃO ===

✅ **Bug Corrigido**: Filtros de transação muito restritivos
✅ **Antes**: Apenas ['CREDIT', 'INCOME', 'DEBIT', 'EXPENSE'] (28.6% dos tipos)  
✅ **Depois**: Inclui ['TRANSFER_IN', 'PIX_IN', 'INTEREST', 'TRANSFER_OUT', 'PIX_OUT', 'FEE'] (100% dos tipos)
✅ **Resultado**: Case-insensitive matching + cobertura completa

=== TROUBLESHOOTING ===

❌ **Se ainda não funcionar**:
1. Verificar se Railway deployou a versão mais recente
2. Limpar cache do navegador (Application > Storage > Clear)  
3. Testar API diretamente com curl/Postman
4. Verificar logs de erro no Railway

💡 **Para debug**:
- Ativar logs de debug no backend
- Comparar resposta do endpoint de categorias vs cash flow
- Verificar tipos de transação reais no banco de dados
""")