#!/usr/bin/env python
"""
Lista todos os preços do Stripe para encontrar os IDs mensais
Execute com: python list_stripe_prices.py
"""
import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.development')
django.setup()

import stripe
from django.conf import settings
from apps.companies.models import SubscriptionPlan

# Configurar Stripe
stripe.api_key = settings.STRIPE_SECRET_KEY

print("=== LISTANDO TODOS OS PREÇOS DO STRIPE ===\n")

# Mapear produtos aos planos
product_to_plan = {
    'Starter': 'starter',
    'Profissional': 'professional',
    'Empresarial': 'enterprise'
}

# Buscar todos os preços
prices = stripe.Price.list(active=True, limit=100)

# Organizar por produto
prices_by_product = {}
for price in prices.data:
    # Buscar detalhes do produto
    try:
        product = stripe.Product.retrieve(price.product)
        product_name = product.name
        
        if product_name not in prices_by_product:
            prices_by_product[product_name] = []
        
        prices_by_product[product_name].append({
            'id': price.id,
            'amount': price.unit_amount / 100,  # Converter de centavos
            'currency': price.currency,
            'interval': price.recurring.interval if price.recurring else 'one_time',
            'interval_count': price.recurring.interval_count if price.recurring else None
        })
    except:
        continue

# Mostrar preços organizados
for product_name, prices in prices_by_product.items():
    print(f"\n{product_name}:")
    for price in prices:
        if price['interval'] != 'one_time':
            interval_text = f"{price['interval_count']} {price['interval']}" if price['interval_count'] > 1 else price['interval']
            print(f"  - {price['id']}: R$ {price['amount']:.2f}/{interval_text}")

# Gerar código de atualização
print("\n" + "="*50)
print("CÓDIGO PARA ATUALIZAR OS PLANOS:\n")

print("```python")
print("from apps.companies.models import SubscriptionPlan")
print()

for product_name, plan_type in product_to_plan.items():
    if product_name in prices_by_product:
        monthly_price = None
        yearly_price = None
        
        for price in prices_by_product[product_name]:
            if price['interval'] == 'month':
                monthly_price = price['id']
            elif price['interval'] == 'year':
                yearly_price = price['id']
        
        print(f"# {product_name}")
        print(f"plan = SubscriptionPlan.objects.get(plan_type='{plan_type}')")
        if monthly_price:
            print(f"plan.stripe_price_id_monthly = '{monthly_price}'")
        if yearly_price:
            print(f"plan.stripe_price_id_yearly = '{yearly_price}'")
        print("plan.save()")
        print()

print("```")