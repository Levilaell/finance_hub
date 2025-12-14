"""
Management command to populate realistic demo data for vitor@teste.com
Usage: python manage.py populate_demo_data
"""

import random
from datetime import datetime, timedelta
from decimal import Decimal
import uuid

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db import transaction

from apps.banking.models import (
    BankAccount, BankConnection, Transaction, Category, Bill, CategoryRule
)

User = get_user_model()

# Demo user email
DEMO_EMAIL = 'vitor@teste.com'

# Category structure for retail business
CATEGORIES = {
    'income': [
        {'name': 'Vendas', 'icon': '💰', 'color': '#22c55e', 'subcategories': [
            {'name': 'Cartão de Crédito', 'icon': '💳', 'color': '#10b981'},
            {'name': 'Cartão de Débito', 'icon': '💳', 'color': '#14b8a6'},
            {'name': 'PIX', 'icon': '📱', 'color': '#06b6d4'},
            {'name': 'Dinheiro', 'icon': '💵', 'color': '#0ea5e9'},
        ]},
        {'name': 'Outras Receitas', 'icon': '📈', 'color': '#84cc16', 'subcategories': []},
    ],
    'expense': [
        {'name': 'Custos Operacionais', 'icon': '🏭', 'color': '#ef4444', 'subcategories': [
            {'name': 'Compra de Mercadorias', 'icon': '📦', 'color': '#dc2626'},
            {'name': 'Frete', 'icon': '🚚', 'color': '#b91c1c'},
            {'name': 'Embalagens', 'icon': '🛍️', 'color': '#991b1b'},
        ]},
        {'name': 'Despesas Fixas', 'icon': '🏢', 'color': '#f97316', 'subcategories': [
            {'name': 'Aluguel', 'icon': '🏠', 'color': '#ea580c'},
            {'name': 'Energia Elétrica', 'icon': '💡', 'color': '#c2410c'},
            {'name': 'Água', 'icon': '💧', 'color': '#9a3412'},
            {'name': 'Internet', 'icon': '🌐', 'color': '#7c2d12'},
            {'name': 'Telefone', 'icon': '📞', 'color': '#6c2e0f'},
        ]},
        {'name': 'Folha de Pagamento', 'icon': '👥', 'color': '#8b5cf6', 'subcategories': [
            {'name': 'Salários', 'icon': '💼', 'color': '#7c3aed'},
            {'name': 'INSS', 'icon': '🏛️', 'color': '#6d28d9'},
            {'name': 'FGTS', 'icon': '🏦', 'color': '#5b21b6'},
            {'name': 'Vale Transporte', 'icon': '🚌', 'color': '#4c1d95'},
        ]},
        {'name': 'Marketing', 'icon': '📢', 'color': '#ec4899', 'subcategories': [
            {'name': 'Facebook/Instagram Ads', 'icon': '📱', 'color': '#db2777'},
            {'name': 'Google Ads', 'icon': '🔍', 'color': '#be185d'},
            {'name': 'Material Gráfico', 'icon': '🖨️', 'color': '#9d174d'},
        ]},
        {'name': 'Despesas Administrativas', 'icon': '📋', 'color': '#6366f1', 'subcategories': [
            {'name': 'Contador', 'icon': '📊', 'color': '#4f46e5'},
            {'name': 'Software/Sistema', 'icon': '💻', 'color': '#4338ca'},
            {'name': 'Material de Escritório', 'icon': '✏️', 'color': '#3730a3'},
        ]},
        {'name': 'Taxas e Impostos', 'icon': '🏛️', 'color': '#64748b', 'subcategories': [
            {'name': 'Taxas Bancárias', 'icon': '🏦', 'color': '#475569'},
            {'name': 'DAS/Simples Nacional', 'icon': '📄', 'color': '#334155'},
            {'name': 'Taxas de Cartão', 'icon': '💳', 'color': '#1e293b'},
        ]},
        {'name': 'Manutenção', 'icon': '🔧', 'color': '#0891b2', 'subcategories': [
            {'name': 'Equipamentos', 'icon': '🖥️', 'color': '#0e7490'},
            {'name': 'Instalações', 'icon': '🏗️', 'color': '#155e75'},
        ]},
    ]
}

# Fornecedores realistas
FORNECEDORES = [
    'Atacadão Martins',
    'Distribuidora Central',
    'Fornecedor ABC Ltda',
    'Makro Atacadista',
    'Assaí Atacadista',
]

# Funcionários
FUNCIONARIOS = [
    {'nome': 'Maria Silva', 'cargo': 'Vendedora', 'salario': 1800},
    {'nome': 'João Santos', 'cargo': 'Estoquista', 'salario': 1650},
    {'nome': 'Ana Costa', 'cargo': 'Caixa', 'salario': 1700},
]


class Command(BaseCommand):
    help = 'Populates realistic demo data for vitor@teste.com'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clean-only',
            action='store_true',
            help='Only clean data without populating new data',
        )

    def handle(self, *args, **options):
        try:
            user = User.objects.get(email=DEMO_EMAIL)
        except User.DoesNotExist:
            self.stderr.write(f'User {DEMO_EMAIL} not found!')
            return

        self.stdout.write(f'Processing user: {user.email} (ID: {user.id})')

        with transaction.atomic():
            # Clean existing data
            self.clean_data(user)

            if options['clean_only']:
                self.stdout.write(self.style.SUCCESS('Data cleaned successfully!'))
                return

            # Create new data
            categories = self.create_categories(user)
            self.create_transactions(user, categories)
            self.create_bills(user, categories)
            self.update_account_balances(user)

        self.stdout.write(self.style.SUCCESS('Demo data populated successfully!'))

    def clean_data(self, user):
        """Clean all existing data for the user"""
        self.stdout.write('Cleaning existing data...')

        # Delete transactions (through accounts)
        connections = BankConnection.objects.filter(user=user)
        for conn in connections:
            tx_count = Transaction.objects.filter(account__connection=conn).count()
            Transaction.objects.filter(account__connection=conn).delete()
            self.stdout.write(f'  Deleted {tx_count} transactions')

        # Delete bills
        bill_count = Bill.objects.filter(user=user).count()
        Bill.objects.filter(user=user).delete()
        self.stdout.write(f'  Deleted {bill_count} bills')

        # Delete category rules
        rule_count = CategoryRule.objects.filter(user=user).count()
        CategoryRule.objects.filter(user=user).delete()
        self.stdout.write(f'  Deleted {rule_count} category rules')

        # Delete categories
        cat_count = Category.objects.filter(user=user).count()
        Category.objects.filter(user=user).delete()
        self.stdout.write(f'  Deleted {cat_count} categories')

    def create_categories(self, user):
        """Create hierarchical categories for retail business"""
        self.stdout.write('Creating categories...')
        categories = {}

        for cat_type, cat_list in CATEGORIES.items():
            for cat_data in cat_list:
                parent = Category.objects.create(
                    user=user,
                    name=cat_data['name'],
                    type=cat_type,
                    icon=cat_data['icon'],
                    color=cat_data['color'],
                    is_system=False,
                )
                categories[cat_data['name']] = parent

                for sub_data in cat_data.get('subcategories', []):
                    sub = Category.objects.create(
                        user=user,
                        name=sub_data['name'],
                        type=cat_type,
                        icon=sub_data['icon'],
                        color=sub_data['color'],
                        parent=parent,
                        is_system=False,
                    )
                    categories[sub_data['name']] = sub

        self.stdout.write(f'  Created {len(categories)} categories')
        return categories

    def create_transactions(self, user, categories):
        """Create 3 months of realistic transactions (Oct-Dec 2024)"""
        self.stdout.write('Creating transactions...')

        accounts = list(BankAccount.objects.filter(connection__user=user))
        if not accounts:
            self.stderr.write('No accounts found!')
            return

        # Main account for most transactions
        main_account = accounts[0]

        transactions = []
        start_date = datetime(2024, 10, 1, tzinfo=timezone.utc)
        end_date = datetime(2024, 12, 31, tzinfo=timezone.utc)

        current_date = start_date
        tx_count = 0

        while current_date <= end_date:
            is_weekend = current_date.weekday() >= 5
            is_holiday = current_date.day in [25, 31] and current_date.month == 12

            # Daily sales (more on weekends, less on holidays)
            if not is_holiday:
                num_sales = random.randint(8, 15) if is_weekend else random.randint(5, 12)

                for _ in range(num_sales):
                    sale_type = random.choices(
                        ['Cartão de Crédito', 'Cartão de Débito', 'PIX', 'Dinheiro'],
                        weights=[35, 25, 30, 10]
                    )[0]

                    amount = Decimal(str(round(random.uniform(25, 450), 2)))

                    # More expensive items on weekends
                    if is_weekend and random.random() > 0.7:
                        amount = Decimal(str(round(random.uniform(200, 800), 2)))

                    tx_time = current_date.replace(
                        hour=random.randint(8, 20),
                        minute=random.randint(0, 59)
                    )

                    transactions.append(Transaction(
                        account=main_account,
                        pluggy_transaction_id=f'demo_tx_{uuid.uuid4().hex[:16]}',
                        type='CREDIT',
                        description=f'Venda - {sale_type}',
                        amount=amount,
                        date=tx_time,
                        pluggy_category='Vendas',
                        user_category=categories.get(sale_type) or categories.get('Vendas'),
                        merchant_name='PDV Loja',
                    ))
                    tx_count += 1

            # Weekly expenses (Mondays - purchases from suppliers)
            if current_date.weekday() == 0:
                fornecedor = random.choice(FORNECEDORES)
                amount = Decimal(str(round(random.uniform(2500, 6000), 2)))

                transactions.append(Transaction(
                    account=main_account,
                    pluggy_transaction_id=f'demo_tx_{uuid.uuid4().hex[:16]}',
                    type='DEBIT',
                    description=f'Compra de Mercadorias - {fornecedor}',
                    amount=amount,
                    date=current_date.replace(hour=10, minute=30),
                    pluggy_category='Compras',
                    user_category=categories.get('Compra de Mercadorias'),
                    merchant_name=fornecedor,
                ))
                tx_count += 1

                # Frete (50% chance)
                if random.random() > 0.5:
                    frete = Decimal(str(round(random.uniform(150, 350), 2)))
                    transactions.append(Transaction(
                        account=main_account,
                        pluggy_transaction_id=f'demo_tx_{uuid.uuid4().hex[:16]}',
                        type='DEBIT',
                        description='Frete Mercadorias',
                        amount=frete,
                        date=current_date.replace(hour=11, minute=0),
                        pluggy_category='Transporte',
                        user_category=categories.get('Frete'),
                        merchant_name='Transportadora Express',
                    ))
                    tx_count += 1

            # Marketing expenses (every 3-4 days)
            if current_date.day % 3 == 0:
                ad_spend = Decimal(str(round(random.uniform(80, 350), 2)))
                transactions.append(Transaction(
                    account=main_account,
                    pluggy_transaction_id=f'demo_tx_{uuid.uuid4().hex[:16]}',
                    type='DEBIT',
                    description='Facebook/Instagram Ads',
                    amount=ad_spend,
                    date=current_date.replace(hour=6, minute=0),
                    pluggy_category='Marketing',
                    user_category=categories.get('Facebook/Instagram Ads'),
                    merchant_name='Meta Platforms',
                ))
                tx_count += 1

            # Monthly fixed expenses (on day 5, 10, 15, 20, 25)
            if current_date.day == 5:
                # Aluguel
                transactions.append(Transaction(
                    account=main_account,
                    pluggy_transaction_id=f'demo_tx_{uuid.uuid4().hex[:16]}',
                    type='DEBIT',
                    description='Aluguel Comercial - Imobiliária Centro',
                    amount=Decimal('4500.00'),
                    date=current_date.replace(hour=9, minute=0),
                    pluggy_category='Moradia',
                    user_category=categories.get('Aluguel'),
                    merchant_name='Imobiliária Centro',
                ))
                tx_count += 1

            if current_date.day == 10:
                # Energia
                energia = Decimal(str(round(random.uniform(650, 950), 2)))
                transactions.append(Transaction(
                    account=main_account,
                    pluggy_transaction_id=f'demo_tx_{uuid.uuid4().hex[:16]}',
                    type='DEBIT',
                    description='Energia Elétrica - CEMIG',
                    amount=energia,
                    date=current_date.replace(hour=10, minute=0),
                    pluggy_category='Utilidades',
                    user_category=categories.get('Energia Elétrica'),
                    merchant_name='CEMIG',
                ))
                tx_count += 1

                # Internet
                transactions.append(Transaction(
                    account=main_account,
                    pluggy_transaction_id=f'demo_tx_{uuid.uuid4().hex[:16]}',
                    type='DEBIT',
                    description='Internet Fibra - Vivo',
                    amount=Decimal('199.90'),
                    date=current_date.replace(hour=10, minute=30),
                    pluggy_category='Utilidades',
                    user_category=categories.get('Internet'),
                    merchant_name='Vivo',
                ))
                tx_count += 1

            if current_date.day == 15:
                # Contador
                transactions.append(Transaction(
                    account=main_account,
                    pluggy_transaction_id=f'demo_tx_{uuid.uuid4().hex[:16]}',
                    type='DEBIT',
                    description='Honorários Contábeis - Escritório Fiscal',
                    amount=Decimal('850.00'),
                    date=current_date.replace(hour=14, minute=0),
                    pluggy_category='Serviços',
                    user_category=categories.get('Contador'),
                    merchant_name='Escritório Fiscal Ltda',
                ))
                tx_count += 1

            if current_date.day == 20:
                # DAS/Simples
                das = Decimal(str(round(random.uniform(1200, 2500), 2)))
                transactions.append(Transaction(
                    account=main_account,
                    pluggy_transaction_id=f'demo_tx_{uuid.uuid4().hex[:16]}',
                    type='DEBIT',
                    description='DAS - Simples Nacional',
                    amount=das,
                    date=current_date.replace(hour=8, minute=0),
                    pluggy_category='Impostos',
                    user_category=categories.get('DAS/Simples Nacional'),
                    merchant_name='Receita Federal',
                ))
                tx_count += 1

            # Salaries (day 5 of each month)
            if current_date.day == 5:
                for func in FUNCIONARIOS:
                    salario = Decimal(str(func['salario']))
                    transactions.append(Transaction(
                        account=main_account,
                        pluggy_transaction_id=f'demo_tx_{uuid.uuid4().hex[:16]}',
                        type='DEBIT',
                        description=f"Salário - {func['nome']} - {func['cargo']}",
                        amount=salario,
                        date=current_date.replace(hour=8, minute=random.randint(0, 30)),
                        pluggy_category='Salários',
                        user_category=categories.get('Salários'),
                        merchant_name=func['nome'],
                    ))
                    tx_count += 1

            # Bank fees (random, 2-3 times per month)
            if current_date.day in [7, 17, 27]:
                taxa = Decimal(str(round(random.uniform(15, 45), 2)))
                transactions.append(Transaction(
                    account=main_account,
                    pluggy_transaction_id=f'demo_tx_{uuid.uuid4().hex[:16]}',
                    type='DEBIT',
                    description='Taxa Manutenção Conta',
                    amount=taxa,
                    date=current_date.replace(hour=0, minute=1),
                    pluggy_category='Taxas',
                    user_category=categories.get('Taxas Bancárias'),
                    merchant_name='Banco Inter',
                ))
                tx_count += 1

            # Occasional expenses
            if random.random() > 0.95:  # ~5% chance per day
                desc = random.choice([
                    ('Manutenção Ar Condicionado', 'Equipamentos', 350, 800),
                    ('Produtos de Limpeza', 'Embalagens', 80, 200),
                    ('Material de Escritório', 'Material de Escritório', 50, 150),
                    ('Sacolas e Embalagens', 'Embalagens', 200, 500),
                ])
                amount = Decimal(str(round(random.uniform(desc[2], desc[3]), 2)))
                transactions.append(Transaction(
                    account=main_account,
                    pluggy_transaction_id=f'demo_tx_{uuid.uuid4().hex[:16]}',
                    type='DEBIT',
                    description=desc[0],
                    amount=amount,
                    date=current_date.replace(hour=random.randint(10, 17), minute=random.randint(0, 59)),
                    pluggy_category='Compras',
                    user_category=categories.get(desc[1]),
                    merchant_name='Fornecedor Local',
                ))
                tx_count += 1

            current_date += timedelta(days=1)

        # Bulk create all transactions
        Transaction.objects.bulk_create(transactions, batch_size=500)
        self.stdout.write(f'  Created {tx_count} transactions')

    def create_bills(self, user, categories):
        """Create bills (contas a pagar/receber)"""
        self.stdout.write('Creating bills...')

        bills = []

        # Contas a pagar fixas para os próximos 3 meses
        for month_offset in range(1, 4):
            due_date = datetime(2025, month_offset, 5).date()

            # Aluguel
            bills.append(Bill(
                user=user,
                type='payable',
                description=f'Aluguel Comercial - {due_date.strftime("%b/%Y")}',
                amount=Decimal('4500.00'),
                due_date=due_date,
                status='pending',
                category=categories.get('Aluguel'),
                customer_supplier='Imobiliária Centro',
                recurrence='monthly',
            ))

            # Energia
            bills.append(Bill(
                user=user,
                type='payable',
                description=f'Energia Elétrica - {due_date.strftime("%b/%Y")}',
                amount=Decimal(str(round(random.uniform(650, 950), 2))),
                due_date=due_date.replace(day=10),
                status='pending',
                category=categories.get('Energia Elétrica'),
                customer_supplier='CEMIG',
                recurrence='monthly',
            ))

            # Internet
            bills.append(Bill(
                user=user,
                type='payable',
                description=f'Internet Fibra - {due_date.strftime("%b/%Y")}',
                amount=Decimal('199.90'),
                due_date=due_date.replace(day=10),
                status='pending',
                category=categories.get('Internet'),
                customer_supplier='Vivo',
                recurrence='monthly',
            ))

            # Contador
            bills.append(Bill(
                user=user,
                type='payable',
                description=f'Honorários Contábeis - {due_date.strftime("%b/%Y")}',
                amount=Decimal('850.00'),
                due_date=due_date.replace(day=15),
                status='pending',
                category=categories.get('Contador'),
                customer_supplier='Escritório Fiscal Ltda',
                recurrence='monthly',
            ))

            # Fornecedor (compra programada)
            bills.append(Bill(
                user=user,
                type='payable',
                description=f'Compra Mercadorias - {random.choice(FORNECEDORES)} - {due_date.strftime("%b/%Y")}',
                amount=Decimal(str(round(random.uniform(5000, 12000), 2))),
                due_date=due_date.replace(day=20),
                status='pending',
                category=categories.get('Compra de Mercadorias'),
                customer_supplier=random.choice(FORNECEDORES),
                recurrence='once',
            ))

        # Contas a receber (clientes com crédito)
        clientes = [
            ('Cliente Atacado A', 8500),
            ('Cliente Atacado B', 6200),
            ('Cliente Atacado C', 4800),
        ]

        for month_offset in range(1, 3):
            due_date = datetime(2025, month_offset, 15).date()
            for cliente, valor_base in clientes:
                valor = Decimal(str(round(valor_base * random.uniform(0.9, 1.1), 2)))
                bills.append(Bill(
                    user=user,
                    type='receivable',
                    description=f'Venda Atacado - {cliente} - {due_date.strftime("%b/%Y")}',
                    amount=valor,
                    due_date=due_date,
                    status='pending',
                    category=categories.get('Vendas'),
                    customer_supplier=cliente,
                    recurrence='once',
                ))

        Bill.objects.bulk_create(bills)
        self.stdout.write(f'  Created {len(bills)} bills')

    def update_account_balances(self, user):
        """Update account balances based on transactions"""
        self.stdout.write('Updating account balances...')

        accounts = BankAccount.objects.filter(connection__user=user)

        # Update main account name and calculate balance
        main_account = accounts.first()
        if main_account:
            main_account.name = 'Banco Inter PJ'
            main_account.balance = Decimal('18450.00')  # Realistic balance
            main_account.save()

        # Update other accounts
        for i, account in enumerate(accounts[1:], 1):
            if i == 1:
                account.name = 'Conta Reserva - Nubank'
                account.balance = Decimal('12800.00')
            elif i == 2:
                account.name = 'Mercado Pago'
                account.balance = Decimal('3250.00')
            account.save()

        self.stdout.write('  Account balances updated')
