#!/usr/bin/env python
"""
Add missing investment and crypto categories
"""
import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from apps.banking.models import TransactionCategory, Transaction

def add_missing_categories():
    print("\n=== ADICIONANDO CATEGORIAS FALTANTES ===\n")
    
    # Add investment application category
    cat1, created1 = TransactionCategory.objects.get_or_create(
        slug='aplicacao-investimentos',
        defaults={
            'name': 'Aplicação em Investimentos',
            'category_type': 'expense',
            'keywords': ['APLICACAO', 'LIQUIDACAO B3', 'DEBITO B3'],
            'icon': '📈',
            'color': '#6366F1',
            'is_system': True
        }
    )
    print(f"Aplicação em Investimentos: {'✅ criada' if created1 else '✓ já existe'}")
    
    # Add crypto categories
    cat2, created2 = TransactionCategory.objects.get_or_create(
        slug='cripto-compra',
        defaults={
            'name': 'Compra de Criptomoedas',
            'category_type': 'expense',
            'keywords': ['DÉBITO CRIPTO', 'DEBITO CRIPTO'],
            'icon': '₿',
            'color': '#F59E0B',
            'is_system': True
        }
    )
    print(f"Compra de Criptomoedas: {'✅ criada' if created2 else '✓ já existe'}")
    
    cat3, created3 = TransactionCategory.objects.get_or_create(
        slug='cripto-venda',
        defaults={
            'name': 'Venda de Criptomoedas',
            'category_type': 'income',
            'keywords': ['CRÉDITO CRIPTO', 'CREDITO CRIPTO'],
            'icon': '₿',
            'color': '#10B981',
            'is_system': True
        }
    )
    print(f"Venda de Criptomoedas: {'✅ criada' if created3 else '✓ já existe'}")
    
    # Update B3 events as income
    cat4, created4 = TransactionCategory.objects.get_or_create(
        slug='dividendos-juros',
        defaults={
            'name': 'Dividendos e Juros',
            'category_type': 'income',
            'keywords': ['CRED EVENTO B3', 'JUROS S/CAPITAL', 'DIVIDENDO'],
            'icon': '💵',
            'color': '#10B981',
            'is_system': True
        }
    )
    print(f"Dividendos e Juros: {'✅ criada' if created4 else '✓ já existe'}")
    
    # Now categorize the remaining transactions
    uncategorized = Transaction.objects.filter(category__isnull=True)
    print(f"\n📊 Transações sem categoria: {uncategorized.count()}")
    
    categorized_count = 0
    for tx in uncategorized:
        desc_upper = tx.description.upper()
        if 'APLICACAO' in desc_upper or 'LIQUIDACAO B3' in desc_upper:
            tx.category = cat1
            categorized_count += 1
        elif 'DÉBITO CRIPTO' in desc_upper:
            tx.category = cat2
            categorized_count += 1
        elif 'CRÉDITO CRIPTO' in desc_upper:
            tx.category = cat3
            categorized_count += 1
        elif 'CRED EVENTO B3' in desc_upper or 'JUROS S/CAPITAL' in desc_upper:
            tx.category = cat4
            categorized_count += 1
        
        if tx.category:
            tx.save()
            print(f"   ✓ {tx.description[:40]} -> {tx.category.name}")
    
    remaining = Transaction.objects.filter(category__isnull=True).count()
    print(f"\n✅ Categorizadas: {categorized_count}")
    print(f"❓ Restantes sem categoria: {remaining}")
    
    # Show final stats
    total = Transaction.objects.count()
    with_cat = Transaction.objects.filter(category__isnull=False).count()
    print(f"\n📈 ESTATÍSTICAS FINAIS:")
    print(f"   Total de transações: {total}")
    print(f"   Com categoria: {with_cat} ({with_cat/total*100:.1f}%)")
    print(f"   Sem categoria: {remaining} ({remaining/total*100:.1f}%)")

if __name__ == '__main__':
    add_missing_categories()