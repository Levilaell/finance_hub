"""
Populate a bank account with realistic test transactions
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from apps.banking.models import BankAccount, Transaction, Category
from decimal import Decimal
import uuid
import random
from datetime import datetime, timedelta

User = get_user_model()


class Command(BaseCommand):
    help = 'Populate a bank account with realistic test transactions'

    # Realistic transaction templates
    TRANSACTION_TEMPLATES = {
        'Food & Dining': {
            'type': 'DEBIT',
            'merchants': [
                'Restaurante Dona Maria',
                'Pizzaria Bella Napoli',
                'Lanchonete Quick Bite',
                'Café Expresso',
                'Sushi Bar Sakura',
                'Padaria Pão Quente',
                'Burger House',
                'Churrascaria Gaúcha',
            ],
            'amount_range': (15.00, 150.00),
            'frequency': 0.20,  # 20% of transactions
        },
        'Groceries': {
            'type': 'DEBIT',
            'merchants': [
                'Supermercado Compre Bem',
                'Mercado São Jorge',
                'Atacadão Central',
                'Hortifruti Natural',
                'Empório Gourmet',
            ],
            'amount_range': (50.00, 350.00),
            'frequency': 0.15,
        },
        'Transportation': {
            'type': 'DEBIT',
            'merchants': [
                'Uber',
                '99 Taxi',
                'Posto Shell',
                'Ipiranga',
                'Estacionamento Center Park',
                'Pedágio Via Fácil',
            ],
            'amount_range': (10.00, 200.00),
            'frequency': 0.15,
        },
        'Shopping': {
            'type': 'DEBIT',
            'merchants': [
                'Magazine Luiza',
                'Amazon Brasil',
                'Mercado Livre',
                'Lojas Americanas',
                'Renner',
                'Zara',
                'Nike Store',
            ],
            'amount_range': (50.00, 500.00),
            'frequency': 0.10,
        },
        'Bills & Utilities': {
            'type': 'DEBIT',
            'merchants': [
                'CPFL Energia',
                'Sabesp',
                'Vivo Fibra',
                'Sky TV',
                'Condomínio Edifício',
                'IPTU Prefeitura',
            ],
            'amount_range': (80.00, 450.00),
            'frequency': 0.08,
        },
        'Entertainment': {
            'type': 'DEBIT',
            'merchants': [
                'Cinemark',
                'Spotify Premium',
                'Netflix',
                'Steam Games',
                'Bar do Zé',
                'Boate Night Club',
            ],
            'amount_range': (20.00, 200.00),
            'frequency': 0.08,
        },
        'Healthcare': {
            'type': 'DEBIT',
            'merchants': [
                'Farmácia São Paulo',
                'Drogaria Pacheco',
                'Clínica Médica Central',
                'Laboratório Diagnóstico',
                'Academia Fitness',
            ],
            'amount_range': (30.00, 300.00),
            'frequency': 0.05,
        },
        'Subscriptions': {
            'type': 'DEBIT',
            'merchants': [
                'Netflix',
                'Spotify',
                'Amazon Prime',
                'Disney Plus',
                'YouTube Premium',
                'iCloud Storage',
            ],
            'amount_range': (15.00, 50.00),
            'frequency': 0.05,
        },
        'Salary': {
            'type': 'CREDIT',
            'merchants': [
                'Empresa XYZ Ltda',
                'Salário Mensal',
            ],
            'amount_range': (3000.00, 8000.00),
            'frequency': 0.03,
        },
        'Freelance': {
            'type': 'CREDIT',
            'merchants': [
                'Cliente Freelance A',
                'Projeto Consultoria',
                'Serviço Prestado',
            ],
            'amount_range': (500.00, 2500.00),
            'frequency': 0.03,
        },
        'Investments': {
            'type': 'CREDIT',
            'merchants': [
                'Dividendos Ações',
                'Rendimento CDB',
                'Tesouro Direto',
            ],
            'amount_range': (50.00, 500.00),
            'frequency': 0.02,
        },
        'Other Expenses': {
            'type': 'DEBIT',
            'merchants': [
                'Diversos',
                'Compra Online',
                'Serviço Prestado',
            ],
            'amount_range': (20.00, 200.00),
            'frequency': 0.06,
        },
    }

    def add_arguments(self, parser):
        parser.add_argument(
            '--account-id',
            type=str,
            help='UUID of the bank account to populate'
        )
        parser.add_argument(
            '--user-email',
            type=str,
            help='Email of the user (will use first active account)'
        )
        parser.add_argument(
            '--count',
            type=int,
            default=100,
            help='Number of transactions to create (default: 100)'
        )
        parser.add_argument(
            '--days-back',
            type=int,
            default=90,
            help='Create transactions for the last N days (default: 90)'
        )
        parser.add_argument(
            '--clear-existing',
            action='store_true',
            help='Delete existing test transactions before creating new ones'
        )

    def handle(self, *args, **options):
        account_id = options.get('account_id')
        user_email = options.get('user_email')
        count = options.get('count')
        days_back = options.get('days_back')
        clear_existing = options.get('clear_existing')

        # Get target account
        account = None
        if account_id:
            try:
                account = BankAccount.objects.get(id=account_id)
            except BankAccount.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'Account with ID {account_id} not found')
                )
                return
        elif user_email:
            try:
                user = User.objects.get(email=user_email)
                account = BankAccount.objects.filter(
                    connection__user=user,
                    is_active=True
                ).first()
                if not account:
                    self.stdout.write(
                        self.style.ERROR(f'No active bank account found for user {user_email}')
                    )
                    return
            except User.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'User with email {user_email} not found')
                )
                return
        else:
            self.stdout.write(
                self.style.ERROR('Please specify either --account-id or --user-email')
            )
            return

        user = account.connection.user

        self.stdout.write(
            self.style.WARNING(
                f'\nTarget Account: {account.name} ({account.type})'
            )
        )
        self.stdout.write(f'User: {user.email}')
        self.stdout.write(f'Transactions to create: {count}')
        self.stdout.write(f'Date range: {days_back} days back\n')

        # Clear existing test transactions if requested
        if clear_existing:
            test_transactions = Transaction.objects.filter(
                account=account,
                pluggy_transaction_id__startswith='test_tx_'
            )
            deleted_count = test_transactions.count()
            test_transactions.delete()
            self.stdout.write(
                self.style.WARNING(f'Deleted {deleted_count} existing test transactions\n')
            )

        # Ensure categories exist
        self.stdout.write('Checking categories...')
        self._ensure_categories(user)

        # Create transactions
        self.stdout.write(f'\nCreating {count} test transactions...\n')
        created_count = self._create_transactions(account, user, count, days_back)

        self.stdout.write(
            self.style.SUCCESS(
                f'\nSuccessfully created {created_count} test transactions!'
            )
        )

        # Show summary
        self._show_summary(account)

    def _ensure_categories(self, user):
        """Ensure all necessary categories exist for the user"""
        from apps.banking.management.commands.create_default_categories import Command as CategoriesCommand

        categories_cmd = CategoriesCommand()
        for category_type, categories in categories_cmd.DEFAULT_CATEGORIES.items():
            for cat_data in categories:
                category, created = Category.objects.get_or_create(
                    user=user,
                    name=cat_data['name'],
                    type=category_type,
                    defaults={
                        'color': cat_data['color'],
                        'icon': cat_data['icon'],
                        'is_system': True
                    }
                )
                if created:
                    self.stdout.write(f"  + Created category: {cat_data['name']}")

    def _create_transactions(self, account, user, count, days_back):
        """Create realistic test transactions"""
        transactions_created = 0
        now = timezone.now()

        # Build weighted list of categories based on frequency
        category_pool = []
        for category_name, config in self.TRANSACTION_TEMPLATES.items():
            weight = int(config['frequency'] * 1000)
            category_pool.extend([category_name] * weight)

        for i in range(count):
            # Select random category
            category_name = random.choice(category_pool)
            config = self.TRANSACTION_TEMPLATES[category_name]

            # Get or create category
            category_type = 'income' if config['type'] == 'CREDIT' else 'expense'
            try:
                category = Category.objects.get(
                    user=user,
                    name=category_name,
                    type=category_type
                )
            except Category.DoesNotExist:
                self.stdout.write(
                    self.style.WARNING(f'Category not found: {category_name}, skipping...')
                )
                continue

            # Generate transaction details
            merchant = random.choice(config['merchants'])
            amount = Decimal(str(round(random.uniform(*config['amount_range']), 2)))

            # Random date within the range
            days_ago = random.randint(0, days_back)
            transaction_date = now - timedelta(days=days_ago)

            # Add some time variance
            hours_offset = random.randint(0, 23)
            minutes_offset = random.randint(0, 59)
            transaction_date = transaction_date.replace(
                hour=hours_offset,
                minute=minutes_offset,
                second=0,
                microsecond=0
            )

            # Create transaction
            try:
                transaction = Transaction.objects.create(
                    account=account,
                    pluggy_transaction_id=f'test_tx_{uuid.uuid4().hex[:16]}',
                    type=config['type'],
                    description=merchant,
                    amount=amount,
                    currency_code='BRL',
                    date=transaction_date,
                    pluggy_category=category_name,
                    merchant_name=merchant,
                    merchant_category=category_name,
                    user_category=category
                )

                transactions_created += 1

                # Show progress every 10 transactions
                if transactions_created % 10 == 0:
                    self.stdout.write(f'  Created {transactions_created}/{count} transactions...')

            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Error creating transaction: {str(e)}')
                )
                continue

        return transactions_created

    def _show_summary(self, account):
        """Show summary of created transactions"""
        transactions = Transaction.objects.filter(
            account=account,
            pluggy_transaction_id__startswith='test_tx_'
        )

        total_income = transactions.filter(type='CREDIT').aggregate(
            total=models.Sum('amount')
        )['total'] or Decimal('0.00')

        total_expenses = transactions.filter(type='DEBIT').aggregate(
            total=models.Sum('amount')
        )['total'] or Decimal('0.00')

        balance = total_income - total_expenses

        self.stdout.write('\n' + '='*50)
        self.stdout.write(self.style.SUCCESS('SUMMARY'))
        self.stdout.write('='*50)
        self.stdout.write(f'Total Test Transactions: {transactions.count()}')
        self.stdout.write(f'Total Income: R$ {total_income:,.2f}')
        self.stdout.write(f'Total Expenses: R$ {total_expenses:,.2f}')
        self.stdout.write(f'Net Balance: R$ {balance:,.2f}')
        self.stdout.write('='*50 + '\n')


# Import models for aggregation
from django.db import models
