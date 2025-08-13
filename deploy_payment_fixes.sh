#!/bin/bash

# Script de deploy para correções do sistema de pagamentos
# Execute após o deploy em produção se necessário

echo "🚀 Aplicando correções do sistema de pagamentos..."

# Sincronizar planos de assinatura
echo "💰 Sincronizando planos de assinatura com Stripe..."
python manage.py sync_subscription_plans

# Verificar configuração
echo "✅ Verificando configuração dos planos..."
python manage.py shell << EOF
from apps.companies.models import SubscriptionPlan

print("\n=== VERIFICAÇÃO DOS PLANOS ===\n")
for plan in SubscriptionPlan.objects.all().order_by('display_order'):
    has_ids = "✅" if plan.has_stripe_ids() else "❌"
    print(f"{plan.name}:")
    print(f"  Preço Mensal: R$ {plan.price_monthly}")
    print(f"  Preço Anual: R$ {plan.price_yearly}")
    print(f"  IDs Stripe: {has_ids}")
    print()
EOF

echo "✅ Correções aplicadas com sucesso!"