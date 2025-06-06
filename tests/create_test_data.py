#!/usr/bin/env python3
import os
import sys
import django
from decimal import Decimal
from datetime import datetime, timedelta

# Add backend to path
sys.path.insert(0, '/Users/levilaell/Desktop/finance_management/backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.development')
django.setup()

from apps.authentication.models import User
from apps.banking.models import BankAccount, BankProvider, Transaction, TransactionCategory
from apps.companies.models import Company
from django.utils import timezone

def create_test_banking_data():
    """Create test banking data for the test user"""
    
    # Get test user
    user = User.objects.filter(email='test@example.com').first()
    if not user or not user.company:
        print("❌ Test user not found. Run create_test_user.py first")
        return
    
    company = user.company
    print(f"✅ Creating test data for: {user.email} / {company.name}")
    
    # Get bank providers
    nubank = BankProvider.objects.filter(code='260').first()
    itau = BankProvider.objects.filter(code='341').first()
    
    if not nubank or not itau:
        print("❌ Bank providers not found. Run: python manage.py create_bank_providers")
        return
    
    # Create test bank accounts
    accounts_data = [
        {
            'bank_provider': nubank,
            'account_type': 'checking',
            'agency': '0001',
            'account_number': '12345678',
            'account_digit': '9',
            'current_balance': Decimal('5250.75'),
            'available_balance': Decimal('5250.75'),
            'nickname': 'Nubank Principal',
            'is_primary': True,
            'status': 'active',
        },
        {
            'bank_provider': itau,
            'account_type': 'business',
            'agency': '1234',
            'account_number': '87654321',
            'account_digit': '0',
            'current_balance': Decimal('12800.50'),
            'available_balance': Decimal('12800.50'),
            'nickname': 'Itaú Empresarial',
            'is_primary': False,
            'status': 'active',
        }
    ]
    
    created_accounts = []
    for acc_data in accounts_data:
        account, created = BankAccount.objects.update_or_create(
            company=company,
            bank_provider=acc_data['bank_provider'],
            agency=acc_data['agency'],
            account_number=acc_data['account_number'],
            defaults=acc_data
        )
        created_accounts.append(account)
        if created:
            print(f"✅ Created account: {account.display_name}")
        else:
            print(f"✅ Updated account: {account.display_name}")
    
    # Get categories
    categories = {
        'vendas': TransactionCategory.objects.filter(slug='vendas').first(),
        'servicos': TransactionCategory.objects.filter(slug='servicos').first(),
        'fornecedores': TransactionCategory.objects.filter(slug='fornecedores').first(),
        'alimentacao': TransactionCategory.objects.filter(slug='alimentacao').first(),
        'transporte': TransactionCategory.objects.filter(slug='transporte').first(),
        'software': TransactionCategory.objects.filter(slug='software-tecnologia').first(),
        'impostos': TransactionCategory.objects.filter(slug='impostos').first(),
        'taxas': TransactionCategory.objects.filter(slug='taxas-bancarias').first(),
    }
    
    # Create test transactions for the last 60 days
    transactions_data = []
    base_date = timezone.now().date()
    
    # Recent transactions (last 30 days)
    for i in range(30):
        date = base_date - timedelta(days=i)
        
        # Income transactions
        if i % 5 == 0:  # Every 5 days
            transactions_data.append({
                'bank_account': created_accounts[0],
                'transaction_type': 'pix_in',
                'amount': Decimal('1250.00'),
                'description': f'Recebimento PIX - Cliente {i+1}',
                'transaction_date': timezone.make_aware(datetime.combine(date, datetime.min.time())),
                'category': categories['vendas'],
                'counterpart_name': f'Cliente {i+1}',
                'status': 'completed',
            })
        
        if i % 7 == 0:  # Weekly
            transactions_data.append({
                'bank_account': created_accounts[1],
                'transaction_type': 'credit',
                'amount': Decimal('3500.00'),
                'description': f'Pagamento Serviços - Projeto {i+1}',
                'transaction_date': timezone.make_aware(datetime.combine(date, datetime.min.time())),
                'category': categories['servicos'],
                'counterpart_name': f'Empresa Cliente {i+1}',
                'status': 'completed',
            })
        
        # Expense transactions
        if i % 3 == 0:  # Every 3 days
            transactions_data.append({
                'bank_account': created_accounts[0],
                'transaction_type': 'debit',
                'amount': Decimal('-85.50'),
                'description': f'Almoço - Restaurante {i+1}',
                'transaction_date': timezone.make_aware(datetime.combine(date, datetime.min.time())),
                'category': categories['alimentacao'],
                'counterpart_name': f'Restaurante {i+1}',
                'status': 'completed',
            })
        
        if i % 4 == 0:  # Every 4 days
            transactions_data.append({
                'bank_account': created_accounts[0],
                'transaction_type': 'pix_out',
                'amount': Decimal('-45.00'),
                'description': f'Uber - Corrida {i+1}',
                'transaction_date': timezone.make_aware(datetime.combine(date, datetime.min.time())),
                'category': categories['transporte'],
                'counterpart_name': 'Uber Brasil',
                'status': 'completed',
            })
        
        if i == 15:  # Monthly expenses
            transactions_data.extend([
                {
                    'bank_account': created_accounts[1],
                    'transaction_type': 'debit',
                    'amount': Decimal('-299.90'),
                    'description': 'Azure - Assinatura Mensal',
                    'transaction_date': timezone.make_aware(datetime.combine(date, datetime.min.time())),
                    'category': categories['software'],
                    'counterpart_name': 'Microsoft Azure',
                    'status': 'completed',
                },
                {
                    'bank_account': created_accounts[1],
                    'transaction_type': 'debit',
                    'amount': Decimal('-1250.00'),
                    'description': 'DAS - Pagamento MEI',
                    'transaction_date': timezone.make_aware(datetime.combine(date, datetime.min.time())),
                    'category': categories['impostos'],
                    'counterpart_name': 'Receita Federal',
                    'status': 'completed',
                },
                {
                    'bank_account': created_accounts[0],
                    'transaction_type': 'fee',
                    'amount': Decimal('-12.50'),
                    'description': 'Taxa de Manutenção',
                    'transaction_date': timezone.make_aware(datetime.combine(date, datetime.min.time())),
                    'category': categories['taxas'],
                    'counterpart_name': nubank.name,
                    'status': 'completed',
                }
            ])
    
    # Create transactions
    created_count = 0
    for trans_data in transactions_data:
        transaction, created = Transaction.objects.get_or_create(
            bank_account=trans_data['bank_account'],
            description=trans_data['description'],
            transaction_date=trans_data['transaction_date'],
            defaults=trans_data
        )
        if created:
            created_count += 1
    
    print(f"✅ Created {created_count} transactions")
    
    # Summary
    total_accounts = BankAccount.objects.filter(company=company).count()
    total_transactions = Transaction.objects.filter(bank_account__company=company).count()
    total_balance = sum(acc.current_balance for acc in created_accounts)
    
    print(f"\n📊 Test Data Summary:")
    print(f"   Bank Accounts: {total_accounts}")
    print(f"   Transactions: {total_transactions}")
    print(f"   Total Balance: R$ {total_balance:,.2f}")
    print(f"\n🎉 Test banking data created successfully!")

if __name__ == "__main__":
    create_test_banking_data()