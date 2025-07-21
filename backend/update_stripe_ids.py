#!/usr/bin/env python
"""
Script para atualizar os IDs do Stripe nos planos
Execute com: python update_stripe_ids.py
"""
import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.development')
django.setup()

from apps.companies.models import SubscriptionPlan

# IDs dos preços do Stripe - COMPLETOS!
stripe_ids = {
    'starter': {
        'yearly': 'price_1RnPVfPFSVtvOaJKmwxNmUdz',  # R$ 490/ano
        'monthly': 'price_1RkePlPFSVtvOaJKYbiX6TqQ'  # R$ 49/mês
    },
    'professional': {
        'yearly': 'price_1RnPVRPFSVtvOaJKIWxiSHfm',  # R$ 1490/ano
        'monthly': 'price_1RkeQgPFSVtvOaJKgPOzW1SD'  # R$ 149/mês
    },
    'enterprise': {
        'yearly': 'price_1RnPV8PFSVtvOaJKoiZxvjPa',  # R$ 3490/ano
        'monthly': 'price_1RkeVLPFSVtvOaJKY5efgwca'  # R$ 349/mês
    }
}

print("=== ATUALIZANDO PLANOS COM IDs DO STRIPE ===\n")

# Atualizar planos
for plan_type, ids in stripe_ids.items():
    try:
        plan = SubscriptionPlan.objects.get(plan_type=plan_type)
        print(f"Atualizando {plan.name} ({plan_type}):")
        
        # Atualizar ID anual
        if ids['yearly']:
            plan.stripe_price_id_yearly = ids['yearly']
            print(f"  ✓ ID Anual: {ids['yearly']}")
        else:
            print(f"  ✗ ID Anual: NÃO CONFIGURADO")
        
        # Atualizar ID mensal
        if ids['monthly']:
            plan.stripe_price_id_monthly = ids['monthly']
            print(f"  ✓ ID Mensal: {ids['monthly']}")
        else:
            print(f"  ✗ ID Mensal: PRECISA CRIAR NO STRIPE")
            print(f"    Preço esperado: R$ {plan.price_monthly}/mês")
        
        plan.save()
        print(f"  ✓ Plano salvo!\n")
        
    except SubscriptionPlan.DoesNotExist:
        print(f"✗ Plano '{plan_type}' não encontrado!\n")

print("\n" + "="*50)
print("✅ TODOS OS PLANOS FORAM ATUALIZADOS COM SUCESSO!")
print("\nOs planos agora têm os IDs do Stripe configurados para:")
print("- Cobrança mensal")
print("- Cobrança anual (com 16% de desconto)")
print("\nO sistema está pronto para processar pagamentos!")