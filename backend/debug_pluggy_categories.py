#!/usr/bin/env python
"""
Debug script para verificar categorização das transações Pluggy
"""
import os
import sys
import django
from decimal import Decimal
from datetime import datetime

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from apps.banking.models import Transaction, TransactionCategory, BankAccount
from apps.banking.pluggy_client import PluggyClient
from apps.banking.pluggy_category_mapper import pluggy_category_mapper
from asgiref.sync import sync_to_async
import asyncio
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


async def test_pluggy_categories():
    """Test Pluggy category retrieval and mapping"""
    
    print("\n=== TESTE DE CATEGORIZAÇÃO PLUGGY ===\n")
    
    # 1. Check existing categories in database
    print("1. Categorias existentes no banco:")
    categories = await sync_to_async(list)(TransactionCategory.objects.all()[:10])
    for cat in categories:  # Show first 10
        print(f"   - {cat.name} ({cat.category_type}) - Slug: {cat.slug}")
    total_categories = await sync_to_async(TransactionCategory.objects.count)()
    print(f"   Total: {total_categories} categorias\n")
    
    # 2. Check recent transactions without categories
    print("2. Transações recentes sem categoria:")
    no_cat_transactions = Transaction.objects.filter(category__isnull=True).order_by('-created_at')[:10]
    for tx in no_cat_transactions:
        print(f"   - {tx.description[:50]} | R$ {tx.amount} | {tx.transaction_date}")
    print(f"   Total sem categoria: {Transaction.objects.filter(category__isnull=True).count()}\n")
    
    # 3. Get a Pluggy account to test
    print("3. Testando com conta Pluggy:")
    pluggy_accounts = BankAccount.objects.filter(
        external_id__isnull=False,
        status='active'
    ).first()
    
    if not pluggy_accounts:
        print("   ❌ Nenhuma conta Pluggy ativa encontrada!")
        return
    
    account = pluggy_accounts
    print(f"   Conta: {account.bank_provider.name} - {account.account_number}")
    print(f"   External ID: {account.external_id}\n")
    
    # 4. Fetch fresh transactions from Pluggy
    print("4. Buscando transações direto da Pluggy API:")
    async with PluggyClient() as client:
        try:
            # Get recent transactions
            response = await client.get_transactions(
                account.external_id,
                from_date=(datetime.now().replace(day=1)).strftime('%Y-%m-%d'),
                to_date=datetime.now().strftime('%Y-%m-%d'),
                page=1,
                page_size=10
            )
            
            transactions = response.get('results', [])
            print(f"   Encontradas {len(transactions)} transações\n")
            
            # 5. Analyze each transaction
            print("5. Análise das transações da Pluggy:")
            for i, tx in enumerate(transactions[:5], 1):
                print(f"\n   Transação {i}:")
                print(f"   - ID: {tx.get('id')}")
                print(f"   - Descrição: {tx.get('description')}")
                print(f"   - Valor: R$ {tx.get('amount')}")
                print(f"   - Tipo: {tx.get('type')}")
                print(f"   - Data: {tx.get('date')}")
                
                # Check if Pluggy provides category
                pluggy_category = tx.get('category')
                print(f"   - Categoria Pluggy: {pluggy_category or 'NÃO FORNECIDA'}")
                
                # Check merchant info
                merchant = tx.get('merchant', {})
                if merchant:
                    print(f"   - Merchant: {merchant.get('name', 'N/A')}")
                    print(f"   - MCC: {merchant.get('mcc', 'N/A')}")
                
                # Test category mapping
                if pluggy_category:
                    transaction_type = 'credit' if tx.get('type') == 'CREDIT' else 'debit'
                    mapped_category = pluggy_category_mapper.map_category(
                        pluggy_category,
                        transaction_type
                    )
                    if mapped_category:
                        print(f"   - Categoria Mapeada: {mapped_category.name}")
                    else:
                        print(f"   - ❌ Categoria não mapeada!")
                
                # Check if transaction exists in DB
                existing = Transaction.objects.filter(
                    external_id=str(tx.get('id'))
                ).first()
                
                if existing:
                    print(f"   - Status no BD: Existe")
                    print(f"   - Categoria no BD: {existing.category.name if existing.category else 'SEM CATEGORIA'}")
                else:
                    print(f"   - Status no BD: Não existe")
            
            # 6. Test category mapper
            print("\n\n6. Testando mapeador de categorias:")
            test_categories = [
                'AUTO', 'TRANSPORT', 'FOOD', 'RESTAURANT', 'ENTERTAINMENT',
                'BILLS', 'HEALTH', 'SHOPPING', 'TRANSFER', 'PIX'
            ]
            
            for test_cat in test_categories:
                mapped = pluggy_category_mapper.map_category(test_cat, 'debit')
                if mapped:
                    print(f"   ✓ {test_cat} -> {mapped.name}")
                else:
                    print(f"   ✗ {test_cat} -> Não mapeado")
            
        except Exception as e:
            print(f"   ❌ Erro ao buscar transações: {e}")
            import traceback
            traceback.print_exc()
    
    # 7. Summary
    print("\n\n=== RESUMO ===")
    total_transactions = Transaction.objects.count()
    with_category = Transaction.objects.filter(category__isnull=False).count()
    without_category = Transaction.objects.filter(category__isnull=True).count()
    
    print(f"Total de transações: {total_transactions}")
    print(f"Com categoria: {with_category} ({with_category/total_transactions*100:.1f}%)")
    print(f"Sem categoria: {without_category} ({without_category/total_transactions*100:.1f}%)")
    
    # Check if categories are being saved
    recent_with_cat = Transaction.objects.filter(
        category__isnull=False,
        created_at__gte=datetime.now().replace(hour=0, minute=0, second=0)
    ).count()
    print(f"Transações categorizadas hoje: {recent_with_cat}")


async def fix_missing_categories():
    """Try to fix missing categories for existing transactions"""
    print("\n\n=== CORRIGINDO CATEGORIAS FALTANTES ===\n")
    
    # Get transactions without categories
    no_cat_transactions = Transaction.objects.filter(
        category__isnull=True,
        bank_account__external_id__isnull=False  # Only Pluggy accounts
    ).select_related('bank_account')[:50]
    
    print(f"Processando {no_cat_transactions.count()} transações sem categoria...\n")
    
    fixed_count = 0
    
    for tx in no_cat_transactions:
        # Try to categorize based on description
        description = tx.description.upper()
        category = None
        
        # Simple rule-based categorization
        if 'PIX' in description:
            if tx.transaction_type == 'credit':
                category = TransactionCategory.objects.filter(
                    slug='transferencias-recebidas'
                ).first()
            else:
                category = TransactionCategory.objects.filter(
                    slug='transferencias-enviadas'
                ).first()
        elif 'SALARIO' in description or 'SALARY' in description:
            category = TransactionCategory.objects.filter(
                slug='salarios'
            ).first()
        elif 'UBER' in description or 'TAXI' in description or '99' in description:
            category = TransactionCategory.objects.filter(
                slug='transporte'
            ).first()
        elif 'IFOOD' in description or 'RAPPI' in description:
            category = TransactionCategory.objects.filter(
                slug='delivery'
            ).first()
        
        if category:
            tx.category = category
            tx.save(update_fields=['category'])
            fixed_count += 1
            print(f"✓ Categorizada: {tx.description[:40]} -> {category.name}")
    
    print(f"\nTotal corrigido: {fixed_count} transações")


if __name__ == '__main__':
    # Run the async function
    asyncio.run(test_pluggy_categories())
    
    # Ask if user wants to fix missing categories
    response = input("\nDeseja tentar corrigir categorias faltantes? (s/n): ")
    if response.lower() == 's':
        asyncio.run(fix_missing_categories())