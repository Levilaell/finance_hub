#!/usr/bin/env python
"""
Script simples para verificar categorização das transações
"""
import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from apps.banking.models import Transaction, TransactionCategory

def check_categories():
    print("\n=== VERIFICAÇÃO DE CATEGORIAS ===\n")
    
    # 1. Check existing categories
    print("1. Categorias existentes:")
    categories = TransactionCategory.objects.all()
    for cat in categories[:10]:
        print(f"   - {cat.name} ({cat.category_type}) - Slug: {cat.slug}")
    print(f"   Total: {categories.count()} categorias\n")
    
    # 2. Check transactions
    print("2. Status das transações:")
    total = Transaction.objects.count()
    with_cat = Transaction.objects.filter(category__isnull=False).count()
    without_cat = Transaction.objects.filter(category__isnull=True).count()
    
    print(f"   Total de transações: {total}")
    print(f"   Com categoria: {with_cat} ({with_cat/total*100:.1f}% se total > 0)")
    print(f"   Sem categoria: {without_cat} ({without_cat/total*100:.1f}% se total > 0)\n")
    
    # 3. Recent transactions without category
    print("3. Transações recentes sem categoria:")
    recent_no_cat = Transaction.objects.filter(
        category__isnull=True
    ).order_by('-created_at')[:10]
    
    for tx in recent_no_cat:
        print(f"   - {tx.description[:50]} | R$ {tx.amount} | {tx.transaction_date}")
    
    # 4. Check if AI categorization is enabled
    print("\n4. Transações categorizadas por IA:")
    ai_categorized = Transaction.objects.filter(is_ai_categorized=True).count()
    print(f"   Total categorizado por IA: {ai_categorized}")
    
    # 5. Sample categorized transactions
    print("\n5. Exemplos de transações COM categoria:")
    with_cat_examples = Transaction.objects.filter(
        category__isnull=False
    ).order_by('-created_at')[:5]
    
    for tx in with_cat_examples:
        print(f"   - {tx.description[:40]} -> {tx.category.name}")
        print(f"     (IA: {tx.is_ai_categorized}, Confiança: {tx.ai_category_confidence})")

if __name__ == '__main__':
    check_categories()