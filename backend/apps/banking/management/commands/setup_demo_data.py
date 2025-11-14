"""
Setup complete demo data for video recording
Creates fake bank accounts and realistic transactions for retail/PME businesses
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from apps.banking.models import BankAccount, BankConnection, Connector, Transaction, Category
from decimal import Decimal
import uuid
from datetime import datetime, timedelta
import random

User = get_user_model()


class Command(BaseCommand):
    help = 'Setup complete demo data with fake bank accounts and realistic transactions'

    def add_arguments(self, parser):
        parser.add_argument(
            '--user-email',
            type=str,
            required=True,
            help='Email of the user to setup demo data for'
        )
        parser.add_argument(
            '--clear-all',
            action='store_true',
            help='Delete all existing bank accounts and transactions for this user'
        )

    def handle(self, *args, **options):
        user_email = options.get('user_email')
        clear_all = options.get('clear_all')

        # Get user
        try:
            user = User.objects.get(email=user_email)
        except User.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'User with email {user_email} not found')
            )
            return

        self.stdout.write(self.style.WARNING(f'\n{"="*60}'))
        self.stdout.write(self.style.WARNING(f'CONFIGURANDO DADOS DEMO PARA: {user.email}'))
        self.stdout.write(self.style.WARNING(f'{"="*60}\n'))

        # Clear existing data if requested
        if clear_all:
            self.stdout.write('Limpando dados existentes...')
            BankConnection.objects.filter(user=user).delete()
            Category.objects.filter(user=user).delete()
            self.stdout.write(self.style.SUCCESS('✓ Dados anteriores removidos\n'))

        # Create categories
        self.stdout.write('Criando categorias...')
        categories = self._create_categories(user)
        self.stdout.write(self.style.SUCCESS(f'✓ {len(categories)} categorias criadas\n'))

        # Get or create connectors
        self.stdout.write('Verificando bancos disponíveis...')
        connectors = self._get_or_create_connectors()
        self.stdout.write(self.style.SUCCESS(f'✓ {len(connectors)} bancos disponíveis\n'))

        # Create fake bank accounts
        self.stdout.write('Criando contas bancárias fake...')
        accounts = self._create_fake_accounts(user, connectors)
        self.stdout.write(self.style.SUCCESS(f'✓ {len(accounts)} contas criadas\n'))

        # Create realistic transactions for each account
        total_transactions = 0
        for account in accounts:
            self.stdout.write(f'\nCriando transações para: {account.name}')
            count = self._create_realistic_transactions(account, user, categories)
            total_transactions += count
            self.stdout.write(self.style.SUCCESS(f'  ✓ {count} transações criadas'))

        # Show final summary
        self.stdout.write(self.style.SUCCESS(f'\n{"="*60}'))
        self.stdout.write(self.style.SUCCESS('RESUMO FINAL'))
        self.stdout.write(self.style.SUCCESS(f'{"="*60}'))
        self.stdout.write(f'Contas Bancárias: {len(accounts)}')
        self.stdout.write(f'Categorias: {len(categories)}')
        self.stdout.write(f'Transações Totais: {total_transactions}')

        self._show_detailed_summary(accounts)

        self.stdout.write(self.style.SUCCESS(f'\n{"="*60}'))
        self.stdout.write(self.style.SUCCESS('✓ DADOS DEMO CONFIGURADOS COM SUCESSO!'))
        self.stdout.write(self.style.SUCCESS(f'{"="*60}\n'))

    def _create_categories(self, user):
        """Create realistic categories for retail business"""
        categories_data = {
            'income': [
                {'name': 'Vendas à Vista', 'color': '#10b981', 'icon': '💵'},
                {'name': 'Vendas Cartão Débito', 'color': '#059669', 'icon': '💳'},
                {'name': 'Vendas Cartão Crédito', 'color': '#047857', 'icon': '💳'},
                {'name': 'Vendas Pix', 'color': '#34d399', 'icon': '📱'},
                {'name': 'Vendas Online', 'color': '#6ee7b7', 'icon': '🛒'},
                {'name': 'Outras Receitas', 'color': '#86efac', 'icon': '➕'},
            ],
            'expense': [
                {'name': 'Compra de Mercadorias', 'color': '#f59e0b', 'icon': '📦'},
                {'name': 'Fornecedores', 'color': '#d97706', 'icon': '🏭'},
                {'name': 'Aluguel', 'color': '#6366f1', 'icon': '🏢'},
                {'name': 'Energia Elétrica', 'color': '#facc15', 'icon': '💡'},
                {'name': 'Água', 'color': '#3b82f6', 'icon': '💧'},
                {'name': 'Internet/Telefone', 'color': '#8b5cf6', 'icon': '📡'},
                {'name': 'Salários', 'color': '#ef4444', 'icon': '👥'},
                {'name': 'Encargos Trabalhistas', 'color': '#dc2626', 'icon': '📋'},
                {'name': 'Contador', 'color': '#64748b', 'icon': '🧮'},
                {'name': 'Marketing', 'color': '#ec4899', 'icon': '📢'},
                {'name': 'Manutenção', 'color': '#f97316', 'icon': '🔧'},
                {'name': 'Limpeza', 'color': '#06b6d4', 'icon': '🧹'},
                {'name': 'Impostos', 'color': '#475569', 'icon': '🏛️'},
                {'name': 'Taxas Bancárias', 'color': '#94a3b8', 'icon': '🏦'},
                {'name': 'Embalagens', 'color': '#a3e635', 'icon': '📦'},
                {'name': 'Transporte/Frete', 'color': '#14b8a6', 'icon': '🚚'},
                {'name': 'Equipamentos', 'color': '#84cc16', 'icon': '⚙️'},
                {'name': 'Outras Despesas', 'color': '#cbd5e1', 'icon': '➖'},
            ]
        }

        categories = {}
        for cat_type, cats in categories_data.items():
            for cat_data in cats:
                category, created = Category.objects.get_or_create(
                    user=user,
                    name=cat_data['name'],
                    type=cat_type,
                    defaults={
                        'color': cat_data['color'],
                        'icon': cat_data['icon'],
                        'is_system': True
                    }
                )
                categories[cat_data['name']] = category

        return categories

    def _get_or_create_connectors(self):
        """Get or create fake bank connectors"""
        banks_data = [
            {
                'pluggy_id': 999001,
                'name': 'Banco do Brasil',
                'institution_name': 'Banco do Brasil S.A.',
                'institution_url': 'https://www.bb.com.br',
                'logo_url': 'https://logo.clearbit.com/bb.com.br',
                'primary_color': '#FFED00',
                'type': 'PERSONAL_BANK',
            },
            {
                'pluggy_id': 999002,
                'name': 'Itaú Unibanco',
                'institution_name': 'Itaú Unibanco S.A.',
                'institution_url': 'https://www.itau.com.br',
                'logo_url': 'https://logo.clearbit.com/itau.com.br',
                'primary_color': '#EC7000',
                'type': 'PERSONAL_BANK',
            },
            {
                'pluggy_id': 999003,
                'name': 'Bradesco',
                'institution_name': 'Banco Bradesco S.A.',
                'institution_url': 'https://www.bradesco.com.br',
                'logo_url': 'https://logo.clearbit.com/bradesco.com.br',
                'primary_color': '#CC092F',
                'type': 'PERSONAL_BANK',
            },
        ]

        connectors = []
        for bank_data in banks_data:
            connector, created = Connector.objects.get_or_create(
                pluggy_id=bank_data['pluggy_id'],
                defaults={
                    'name': bank_data['name'],
                    'institution_name': bank_data['institution_name'],
                    'institution_url': bank_data['institution_url'],
                    'logo_url': bank_data['logo_url'],
                    'primary_color': bank_data['primary_color'],
                    'type': bank_data['type'],
                    'country': 'BR',
                    'is_active': True,
                    'is_sandbox': True,  # Mark as sandbox/demo
                }
            )
            connectors.append(connector)

        return connectors

    def _create_fake_accounts(self, user, connectors):
        """Create 3 fake bank accounts"""
        accounts_data = [
            {
                'connector': connectors[0],  # Banco do Brasil
                'name': 'Conta Empresarial BB',
                'type': 'CHECKING',
                'balance': Decimal('45280.75'),
                'account_number': '12345-6',
                'agency': '1234-5',
            },
            {
                'connector': connectors[1],  # Itaú
                'name': 'Conta Corrente Itaú',
                'type': 'CHECKING',
                'balance': Decimal('28950.40'),
                'account_number': '67890-1',
                'agency': '6789',
            },
            {
                'connector': connectors[2],  # Bradesco
                'name': 'Conta PJ Bradesco',
                'type': 'CHECKING',
                'balance': Decimal('19635.20'),
                'account_number': '54321-9',
                'agency': '5432',
            },
        ]

        accounts = []
        for account_data in accounts_data:
            # Create connection
            connection, created = BankConnection.objects.get_or_create(
                user=user,
                connector=account_data['connector'],
                defaults={
                    'pluggy_item_id': f'demo_item_{uuid.uuid4().hex[:16]}',
                    'status': 'UPDATED',
                    'is_active': True,
                }
            )

            # Create account
            account = BankAccount.objects.create(
                connection=connection,
                pluggy_account_id=f'demo_acc_{uuid.uuid4().hex[:16]}',
                type=account_data['type'],
                name=account_data['name'],
                balance=account_data['balance'],
                is_active=True,
            )
            accounts.append(account)

            self.stdout.write(f'  ✓ {account.name} - Saldo: R$ {account.balance:,.2f}')

        return accounts

    def _create_realistic_transactions(self, account, user, categories):
        """Create realistic transactions for the last 90 days"""
        now = timezone.now()
        transactions_created = 0

        # Define transaction templates based on account
        account_index = ['BB', 'Itaú', 'Bradesco'].index(
            next(word for word in ['BB', 'Itaú', 'Bradesco'] if word in account.name)
        )

        # Transactions for last 90 days
        days_back = 90

        # RECEITAS (Income) - Vendas diárias
        for days_ago in range(days_back):
            date = now - timedelta(days=days_ago)

            # Skip Sundays (most retail closed on Sundays)
            if date.weekday() == 6:
                continue

            # Number of sales per day (more on weekends)
            num_sales = random.randint(8, 15) if date.weekday() in [4, 5] else random.randint(4, 10)

            for _ in range(num_sales):
                # Random sale type
                sale_type = random.choices(
                    [
                        ('Vendas Pix', 'PIX', (15.00, 450.00)),
                        ('Vendas Cartão Débito', 'Cartão Débito', (20.00, 380.00)),
                        ('Vendas Cartão Crédito', 'Cartão Crédito', (30.00, 650.00)),
                        ('Vendas à Vista', 'Dinheiro', (10.00, 250.00)),
                    ],
                    weights=[35, 30, 25, 10]
                )[0]

                category_name, payment_method, amount_range = sale_type
                amount = Decimal(str(round(random.uniform(*amount_range), 2)))

                # Random time during business hours (8h - 20h)
                hour = random.randint(8, 20)
                minute = random.randint(0, 59)
                transaction_date = date.replace(hour=hour, minute=minute, second=0, microsecond=0)

                Transaction.objects.create(
                    account=account,
                    pluggy_transaction_id=f'demo_tx_{uuid.uuid4().hex[:16]}',
                    type='CREDIT',
                    description=f'Venda - {payment_method}',
                    amount=amount,
                    currency_code='BRL',
                    date=transaction_date,
                    pluggy_category=category_name,
                    merchant_name=f'Venda PDV',
                    merchant_category='Sales',
                    user_category=categories.get(category_name),
                )
                transactions_created += 1

        # DESPESAS (Expenses) - Específicas por tipo

        # 1. Compras de Mercadorias (Semanal - Segunda ou Terça)
        for week in range(int(days_back / 7)):
            days_ago = week * 7 + random.randint(0, 1)  # Monday or Tuesday
            date = (now - timedelta(days=days_ago)).replace(hour=10, minute=30)

            suppliers = [
                ('Atacadão Martins', (1500.00, 4500.00)),
                ('Distribuidora Central', (2000.00, 5500.00)),
                ('Fornecedor ABC Ltda', (1800.00, 4000.00)),
            ]

            supplier, amount_range = random.choice(suppliers)
            amount = Decimal(str(round(random.uniform(*amount_range), 2)))

            Transaction.objects.create(
                account=account,
                pluggy_transaction_id=f'demo_tx_{uuid.uuid4().hex[:16]}',
                type='DEBIT',
                description=f'Compra de Mercadorias - {supplier}',
                amount=amount,
                currency_code='BRL',
                date=date,
                pluggy_category='Compra de Mercadorias',
                merchant_name=supplier,
                merchant_category='Inventory',
                user_category=categories.get('Compra de Mercadorias'),
            )
            transactions_created += 1

        # 2. Aluguel (Mensal - Dia 5)
        for month in range(int(days_back / 30)):
            days_ago = month * 30 + 5
            if days_ago > days_back:
                continue
            date = (now - timedelta(days=days_ago)).replace(hour=8, minute=0)

            Transaction.objects.create(
                account=account,
                pluggy_transaction_id=f'demo_tx_{uuid.uuid4().hex[:16]}',
                type='DEBIT',
                description='Aluguel Comercial - Imobiliária Centro',
                amount=Decimal('2800.00'),
                currency_code='BRL',
                date=date,
                pluggy_category='Aluguel',
                merchant_name='Imobiliária Centro',
                merchant_category='Rent',
                user_category=categories.get('Aluguel'),
            )
            transactions_created += 1

        # 3. Energia Elétrica (Mensal - Dia 10)
        for month in range(int(days_back / 30)):
            days_ago = month * 30 + 10
            if days_ago > days_back:
                continue
            date = (now - timedelta(days=days_ago)).replace(hour=9, minute=0)

            amount = Decimal(str(round(random.uniform(450.00, 850.00), 2)))
            Transaction.objects.create(
                account=account,
                pluggy_transaction_id=f'demo_tx_{uuid.uuid4().hex[:16]}',
                type='DEBIT',
                description='CPFL Energia - Conta de Luz',
                amount=amount,
                currency_code='BRL',
                date=date,
                pluggy_category='Energia Elétrica',
                merchant_name='CPFL Energia',
                merchant_category='Utilities',
                user_category=categories.get('Energia Elétrica'),
            )
            transactions_created += 1

        # 4. Internet/Telefone (Mensal - Dia 15)
        for month in range(int(days_back / 30)):
            days_ago = month * 30 + 15
            if days_ago > days_back:
                continue
            date = (now - timedelta(days=days_ago)).replace(hour=10, minute=0)

            Transaction.objects.create(
                account=account,
                pluggy_transaction_id=f'demo_tx_{uuid.uuid4().hex[:16]}',
                type='DEBIT',
                description='Vivo Empresarial - Internet',
                amount=Decimal('299.90'),
                currency_code='BRL',
                date=date,
                pluggy_category='Internet/Telefone',
                merchant_name='Vivo Empresarial',
                merchant_category='Utilities',
                user_category=categories.get('Internet/Telefone'),
            )
            transactions_created += 1

        # 5. Água (Mensal - Dia 12)
        for month in range(int(days_back / 30)):
            days_ago = month * 30 + 12
            if days_ago > days_back:
                continue
            date = (now - timedelta(days=days_ago)).replace(hour=11, minute=0)

            amount = Decimal(str(round(random.uniform(120.00, 280.00), 2)))
            Transaction.objects.create(
                account=account,
                pluggy_transaction_id=f'demo_tx_{uuid.uuid4().hex[:16]}',
                type='DEBIT',
                description='Sabesp - Conta de Água',
                amount=amount,
                currency_code='BRL',
                date=date,
                pluggy_category='Água',
                merchant_name='Sabesp',
                merchant_category='Utilities',
                user_category=categories.get('Água'),
            )
            transactions_created += 1

        # 6. Salários (Mensal - Dia 5)
        for month in range(int(days_back / 30)):
            days_ago = month * 30 + 5
            if days_ago > days_back:
                continue
            date = (now - timedelta(days=days_ago)).replace(hour=7, minute=0)

            # 3 funcionários
            salaries = [
                ('Maria Silva - Vendedora', Decimal('1850.00')),
                ('João Santos - Estoquista', Decimal('1650.00')),
                ('Ana Costa - Caixa', Decimal('1750.00')),
            ]

            for employee, salary in salaries:
                Transaction.objects.create(
                    account=account,
                    pluggy_transaction_id=f'demo_tx_{uuid.uuid4().hex[:16]}',
                    type='DEBIT',
                    description=f'Salário - {employee}',
                    amount=salary,
                    currency_code='BRL',
                    date=date,
                    pluggy_category='Salários',
                    merchant_name=employee,
                    merchant_category='Payroll',
                    user_category=categories.get('Salários'),
                )
                transactions_created += 1

        # 7. Encargos Trabalhistas (Mensal - Dia 7)
        for month in range(int(days_back / 30)):
            days_ago = month * 30 + 7
            if days_ago > days_back:
                continue
            date = (now - timedelta(days=days_ago)).replace(hour=8, minute=30)

            encargos = [
                ('INSS Empresa', Decimal('1245.50')),
                ('FGTS Depósito', Decimal('525.00')),
            ]

            for descricao, valor in encargos:
                Transaction.objects.create(
                    account=account,
                    pluggy_transaction_id=f'demo_tx_{uuid.uuid4().hex[:16]}',
                    type='DEBIT',
                    description=descricao,
                    amount=valor,
                    currency_code='BRL',
                    date=date,
                    pluggy_category='Encargos Trabalhistas',
                    merchant_name='Receita Federal',
                    merchant_category='Taxes',
                    user_category=categories.get('Encargos Trabalhistas'),
                )
                transactions_created += 1

        # 8. Contador (Mensal - Dia 20)
        for month in range(int(days_back / 30)):
            days_ago = month * 30 + 20
            if days_ago > days_back:
                continue
            date = (now - timedelta(days=days_ago)).replace(hour=15, minute=0)

            Transaction.objects.create(
                account=account,
                pluggy_transaction_id=f'demo_tx_{uuid.uuid4().hex[:16]}',
                type='DEBIT',
                description='Serviços Contábeis - Contabilidade Silva',
                amount=Decimal('450.00'),
                currency_code='BRL',
                date=date,
                pluggy_category='Contador',
                merchant_name='Contabilidade Silva',
                merchant_category='Services',
                user_category=categories.get('Contador'),
            )
            transactions_created += 1

        # 9. Impostos (Mensal - Dia 20)
        for month in range(int(days_back / 30)):
            days_ago = month * 30 + 20
            if days_ago > days_back:
                continue
            date = (now - timedelta(days=days_ago)).replace(hour=9, minute=0)

            amount = Decimal(str(round(random.uniform(800.00, 1500.00), 2)))
            Transaction.objects.create(
                account=account,
                pluggy_transaction_id=f'demo_tx_{uuid.uuid4().hex[:16]}',
                type='DEBIT',
                description='DAS - Simples Nacional',
                amount=amount,
                currency_code='BRL',
                date=date,
                pluggy_category='Impostos',
                merchant_name='Receita Federal',
                merchant_category='Taxes',
                user_category=categories.get('Impostos'),
            )
            transactions_created += 1

        # 10. Despesas variadas (aleatórias)
        variable_expenses = [
            ('Marketing', 'Google Ads', (200.00, 800.00)),
            ('Marketing', 'Facebook Ads', (150.00, 500.00)),
            ('Manutenção', 'Manutenção Ar Condicionado', (180.00, 450.00)),
            ('Limpeza', 'Produtos de Limpeza', (120.00, 280.00)),
            ('Embalagens', 'Sacolas e Embalagens', (150.00, 350.00)),
            ('Taxas Bancárias', 'Taxa Manutenção Conta', (35.00, 85.00)),
            ('Transporte/Frete', 'Frete Mercadorias', (180.00, 450.00)),
        ]

        for _ in range(random.randint(15, 25)):
            days_ago = random.randint(0, days_back)
            date = (now - timedelta(days=days_ago)).replace(
                hour=random.randint(8, 18),
                minute=random.randint(0, 59)
            )

            category_name, merchant, amount_range = random.choice(variable_expenses)
            amount = Decimal(str(round(random.uniform(*amount_range), 2)))

            Transaction.objects.create(
                account=account,
                pluggy_transaction_id=f'demo_tx_{uuid.uuid4().hex[:16]}',
                type='DEBIT',
                description=merchant,
                amount=amount,
                currency_code='BRL',
                date=date,
                pluggy_category=category_name,
                merchant_name=merchant,
                merchant_category='Operational',
                user_category=categories.get(category_name),
            )
            transactions_created += 1

        return transactions_created

    def _show_detailed_summary(self, accounts):
        """Show detailed summary for each account"""
        from django.db import models

        self.stdout.write(f'\n{"="*60}')
        self.stdout.write('DETALHAMENTO POR CONTA')
        self.stdout.write(f'{"="*60}')

        for account in accounts:
            transactions = Transaction.objects.filter(account=account)

            total_income = transactions.filter(type='CREDIT').aggregate(
                total=models.Sum('amount')
            )['total'] or Decimal('0.00')

            total_expenses = transactions.filter(type='DEBIT').aggregate(
                total=models.Sum('amount')
            )['total'] or Decimal('0.00')

            balance = total_income - total_expenses

            self.stdout.write(f'\n{account.name} ({account.connection.connector.name})')
            self.stdout.write('-' * 60)
            self.stdout.write(f'  Transações: {transactions.count()}')
            self.stdout.write(f'  Receitas: R$ {total_income:,.2f}')
            self.stdout.write(f'  Despesas: R$ {total_expenses:,.2f}')
            self.stdout.write(f'  Saldo: R$ {balance:,.2f}')


# Import models for aggregation
from django.db import models
