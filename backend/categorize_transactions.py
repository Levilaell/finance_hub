#!/usr/bin/env python
"""
Categorize existing transactions based on patterns
"""
import os
import sys
import django
import re

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from apps.banking.models import Transaction, TransactionCategory
from django.db import transaction as db_transaction

def create_default_categories():
    """Create default categories if they don't exist"""
    default_categories = [
        # Income categories
        {'name': 'Salário', 'slug': 'salario', 'category_type': 'income', 'keywords': ['SALARIO', 'SALARY', 'PAGAMENTO']},
        {'name': 'Transferências Recebidas', 'slug': 'transferencias-recebidas', 'category_type': 'income', 'keywords': ['PIX RECEBIDO', 'TED RECEBIDO', 'TRANSFERENCIA RECEBIDA']},
        {'name': 'Vendas', 'slug': 'vendas', 'category_type': 'income', 'keywords': ['VENDA', 'RECEBIMENTO']},
        {'name': 'Investimentos', 'slug': 'investimentos-receita', 'category_type': 'income', 'keywords': ['RESGATE', 'RENDIMENTO', 'DIVIDENDO']},
        
        # Expense categories
        {'name': 'Alimentação', 'slug': 'alimentacao', 'category_type': 'expense', 'keywords': ['IFOOD', 'RAPPI', 'UBER EATS', 'RESTAURANTE', 'LANCHONETE', 'PADARIA']},
        {'name': 'Transporte', 'slug': 'transporte', 'category_type': 'expense', 'keywords': ['UBER', '99', 'CABIFY', 'COMBUSTIVEL', 'POSTO', 'ESTACIONAMENTO']},
        {'name': 'Transferências Enviadas', 'slug': 'transferencias-enviadas', 'category_type': 'expense', 'keywords': ['PIX ENVIADO', 'TED ENVIADO', 'TRANSFERENCIA ENVIADA']},
        {'name': 'Entretenimento', 'slug': 'entretenimento', 'category_type': 'expense', 'keywords': ['NETFLIX', 'SPOTIFY', 'AMAZON PRIME', 'DISNEY', 'HBO', 'CINEMA', 'SHOW', 'INGRESSO']},
        {'name': 'Compras', 'slug': 'compras', 'category_type': 'expense', 'keywords': ['MERCADO', 'SUPERMERCADO', 'FARMACIA', 'LOJA', 'SHOPPING']},
        {'name': 'Contas e Serviços', 'slug': 'contas-servicos', 'category_type': 'expense', 'keywords': ['CONTA', 'FATURA', 'ENERGIA', 'AGUA', 'INTERNET', 'TELEFONE', 'CELULAR']},
        {'name': 'Saúde', 'slug': 'saude', 'category_type': 'expense', 'keywords': ['MEDICO', 'CLINICA', 'HOSPITAL', 'CONSULTA', 'EXAME', 'PLANO DE SAUDE']},
        {'name': 'Educação', 'slug': 'educacao', 'category_type': 'expense', 'keywords': ['ESCOLA', 'FACULDADE', 'CURSO', 'MENSALIDADE', 'MATERIAL ESCOLAR']},
        {'name': 'Lazer', 'slug': 'lazer', 'category_type': 'expense', 'keywords': ['BAR', 'BALADA', 'FESTA', 'CLUBE', 'VIAGEM']},
        {'name': 'Taxas Bancárias', 'slug': 'taxas-bancarias', 'category_type': 'expense', 'keywords': ['TAXA', 'TARIFA', 'ANUIDADE', 'MANUTENCAO']},
        {'name': 'Jogos e Apostas', 'slug': 'jogos-apostas', 'category_type': 'expense', 'keywords': ['BET', 'BETANO', 'SPORTINGBET', 'PIXBET', 'BLAZE', 'CASINO', 'APOSTA', 'KAIZEN']},
    ]
    
    created_count = 0
    for cat_data in default_categories:
        category, created = TransactionCategory.objects.get_or_create(
            slug=cat_data['slug'],
            defaults={
                'name': cat_data['name'],
                'category_type': cat_data['category_type'],
                'keywords': cat_data['keywords'],
                'icon': '💰' if cat_data['category_type'] == 'income' else '💸',
                'color': '#10B981' if cat_data['category_type'] == 'income' else '#EF4444',
                'is_system': True,
                'confidence_threshold': 0.7
            }
        )
        if created:
            created_count += 1
            print(f"✅ Created category: {category.name}")
    
    print(f"\nTotal categories created: {created_count}")
    return TransactionCategory.objects.all()

def categorize_transaction(transaction, categories):
    """Categorize a single transaction based on description"""
    description_upper = transaction.description.upper()
    
    # Check each category's keywords
    best_match = None
    best_score = 0
    
    for category in categories:
        # Check if category type matches transaction type
        if transaction.transaction_type == 'credit' and category.category_type == 'expense':
            continue
        if transaction.transaction_type == 'debit' and category.category_type == 'income':
            continue
        
        # Check keywords
        if hasattr(category, 'keywords') and category.keywords:
            for keyword in category.keywords:
                if keyword.upper() in description_upper:
                    # Calculate score based on keyword length (longer = more specific = better)
                    score = len(keyword)
                    if score > best_score:
                        best_score = score
                        best_match = category
    
    return best_match

def main():
    print("\n=== CATEGORIZADOR DE TRANSAÇÕES ===\n")
    
    # Create/update categories
    print("1. Criando/atualizando categorias...")
    categories = create_default_categories()
    
    # Get uncategorized transactions
    print("\n2. Buscando transações sem categoria...")
    uncategorized = Transaction.objects.filter(category__isnull=True)
    total_uncategorized = uncategorized.count()
    print(f"   Encontradas: {total_uncategorized} transações\n")
    
    if total_uncategorized == 0:
        print("✅ Todas as transações já estão categorizadas!")
        return
    
    # Categorize transactions
    print("3. Categorizando transações...")
    categorized_count = 0
    
    with db_transaction.atomic():
        for i, tx in enumerate(uncategorized):
            if i % 50 == 0:
                print(f"   Processando... {i}/{total_uncategorized}")
            
            category = categorize_transaction(tx, categories)
            if category:
                tx.category = category
                tx.save(update_fields=['category', 'updated_at'])
                categorized_count += 1
                
                if categorized_count <= 10:  # Show first 10 examples
                    print(f"   ✓ {tx.description[:40]} -> {category.name}")
    
    print(f"\n✅ Categorização concluída!")
    print(f"   Total categorizado: {categorized_count} ({categorized_count/total_uncategorized*100:.1f}%)")
    print(f"   Sem categoria: {total_uncategorized - categorized_count}")
    
    # Show some examples of uncategorized transactions
    still_uncategorized = Transaction.objects.filter(category__isnull=True)[:10]
    if still_uncategorized:
        print("\n⚠️  Exemplos de transações que não foram categorizadas:")
        for tx in still_uncategorized:
            print(f"   - {tx.description[:60]}")

if __name__ == '__main__':
    main()