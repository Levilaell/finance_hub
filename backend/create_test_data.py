#!/usr/bin/env python
"""
Create test data for development
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.development')
django.setup()

from apps.authentication.models import User
from apps.companies.models import Company, SubscriptionPlan
from apps.banking.models import BankProvider, BankAccount
from decimal import Decimal

def create_test_data():
    print("🚀 Criando dados de teste...")
    
    # Create subscription plan first
    starter_plan, created = SubscriptionPlan.objects.get_or_create(
        slug='starter',
        defaults={
            'name': 'Starter',
            'plan_type': 'starter',
            'price_monthly': Decimal('29.90'),
            'price_yearly': Decimal('299.00'),
            'max_transactions': 500,
            'max_bank_accounts': 2,
            'max_users': 1,
            'has_ai_categorization': True,
            'has_advanced_reports': False,
            'has_api_access': False,
            'has_accountant_access': False
        }
    )
    if created:
        print("✅ Plano Starter criado")
    
    # Create admin user first
    admin_user, created = User.objects.get_or_create(
        email='admin@admin.com',
        defaults={
            'username': 'admin',
            'first_name': 'Admin',
            'last_name': 'User',
            'is_staff': True,
            'is_superuser': True
        }
    )
    if created:
        admin_user.set_password('admin123')
        admin_user.save()
        print("✅ Admin user criado: admin@admin.com / admin123")
    
    # Create test company with admin as owner
    company, created = Company.objects.get_or_create(
        owner=admin_user,
        defaults={
            'name': 'Empresa Teste',
            'cnpj': '12345678000195',
            'company_type': 'mei',
            'business_sector': 'technology',
            'email': 'empresa@teste.com',
            'phone': '(11) 99999-9999',
            'subscription_plan': starter_plan
        }
    )
    
    # Company created successfully
    
    # Create test user
    test_user, created = User.objects.get_or_create(
        email='user@test.com',
        defaults={
            'username': 'testuser',
            'first_name': 'Test',
            'last_name': 'User'
        }
    )
    if created:
        test_user.set_password('test123')
        test_user.save()
        print("✅ Test user criado: user@test.com / test123")
    
    # Create bank providers
    banks = [
        {'name': 'Banco do Brasil', 'code': '001', 'color': '#FFFF00'},
        {'name': 'Bradesco', 'code': '237', 'color': '#CC0000'},
        {'name': 'Itaú', 'code': '341', 'color': '#FF8C00'},
        {'name': 'Santander', 'code': '033', 'color': '#EC1C24'},
        {'name': 'Caixa Econômica', 'code': '104', 'color': '#0066CC'},
        {'name': 'BTG Pactual', 'code': '208', 'color': '#000000'},
        {'name': 'Nubank', 'code': '260', 'color': '#8A05BE'},
        {'name': 'Inter', 'code': '077', 'color': '#FF7A00'},
    ]
    
    created_banks = 0
    for bank_data in banks:
        provider, created = BankProvider.objects.get_or_create(
            code=bank_data['code'],
            defaults={
                'name': bank_data['name'],
                'color': bank_data['color'],
                'is_active': True,
                'supports_pix': True,
                'supports_ted': True
            }
        )
        if created:
            created_banks += 1
    
    print(f"✅ {created_banks} bancos criados")
    
    # Create test bank accounts
    bb = BankProvider.objects.get(code='001')
    nubank = BankProvider.objects.get(code='260')
    
    account1, created = BankAccount.objects.get_or_create(
        company=company,
        bank_provider=bb,
        agency='1234',
        account_number='12345678',
        defaults={
            'account_type': 'checking',
            'account_digit': '9',
            'current_balance': Decimal('5000.00'),
            'available_balance': Decimal('4500.00'),
            'nickname': 'Conta Principal',
            'status': 'active',
            'is_primary': True
        }
    )
    
    account2, created = BankAccount.objects.get_or_create(
        company=company,
        bank_provider=nubank,
        agency='0001',
        account_number='87654321',
        defaults={
            'account_type': 'digital',
            'account_digit': '0',
            'current_balance': Decimal('1500.00'),
            'available_balance': Decimal('1500.00'),
            'nickname': 'Nubank',
            'status': 'active'
        }
    )
    
    accounts_count = BankAccount.objects.filter(company=company).count()
    print(f"✅ {accounts_count} contas bancárias criadas")
    
    print("\n🎉 Dados de teste criados com sucesso!")
    print("🌐 Acesse: http://127.0.0.1:8000/")
    print("📧 Admin: admin@admin.com / admin123")
    print("👤 User: user@test.com / test123")
    print("📚 Documentação: http://127.0.0.1:8000/swagger/")

if __name__ == '__main__':
    create_test_data()