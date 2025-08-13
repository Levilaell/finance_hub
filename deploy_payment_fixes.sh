#!/bin/bash

# Script de deploy para correções do sistema de pagamentos
# Execute após o deploy em produção

echo "🚀 Aplicando correções do sistema de pagamentos..."

# 1. Aplicar migrações se houver
echo "📦 Aplicando migrações..."
python manage.py migrate

# 2. Sincronizar planos de assinatura
echo "💰 Sincronizando planos de assinatura com Stripe..."
python manage.py sync_subscription_plans

# 3. Verificar configuração
echo "✅ Verificando configuração dos planos..."
python manage.py shell << EOF
from apps.companies.models import SubscriptionPlan

print("\n=== VERIFICAÇÃO DOS PLANOS ===\n")
for plan in SubscriptionPlan.objects.all().order_by('display_order'):
    has_ids = "✅" if plan.has_stripe_ids() else "❌"
    print(f"{plan.name}:")
    print(f"  Preço Mensal: R$ {plan.price_monthly}")
    print(f"  Preço Anual: R$ {plan.price_yearly}")
    print(f"  IDs Stripe Configurados: {has_ids}")
    print()

# Verificar se todos têm IDs
all_have_ids = all(p.has_stripe_ids() for p in SubscriptionPlan.objects.all())
if all_have_ids:
    print("✅ SUCESSO: Todos os planos estão configurados corretamente!")
else:
    print("⚠️ ATENÇÃO: Alguns planos não têm IDs do Stripe configurados")
    print("Execute novamente: python manage.py sync_subscription_plans")
EOF

# 4. Limpar cache se usar Redis
if command -v redis-cli &> /dev/null; then
    echo "🔄 Limpando cache Redis..."
    redis-cli FLUSHDB
fi

# 5. Reiniciar workers se usar Celery
if pgrep -x "celery" > /dev/null; then
    echo "🔄 Reiniciando Celery workers..."
    pkill -f "celery worker"
    # O supervisor ou systemd deve reiniciar automaticamente
fi

echo "✅ Correções aplicadas com sucesso!"
echo ""
echo "📊 Próximos passos:"
echo "1. Monitore os logs de webhook: tail -f logs/webhooks.log"
echo "2. Verifique checkout com um teste: criar nova assinatura"
echo "3. Confirme no Stripe Dashboard que está usando os price IDs corretos"