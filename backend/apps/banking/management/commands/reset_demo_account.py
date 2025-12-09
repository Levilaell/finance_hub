"""
Reset and populate demo account with fresh, realistic data.
Creates fake bank accounts, transactions, and bills for demonstration.
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from apps.banking.models import (
    BankAccount, BankConnection, Connector, Transaction, Category, Bill
)
from decimal import Decimal
import uuid
from datetime import datetime, timedelta
import random

User = get_user_model()


class Command(BaseCommand):
    help = 'Reset demo account with fresh realistic data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--user-email',
            type=str,
            default='vitor@teste.com',
            help='Email of the demo user (default: vitor@teste.com)'
        )

    def handle(self, *args, **options):
        user_email = options.get('user_email')

        try:
            user = User.objects.get(email=user_email)
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'User {user_email} not found'))
            return

        self.stdout.write(self.style.WARNING(f'\n{"="*60}'))
        self.stdout.write(self.style.WARNING(f'RESETANDO CONTA DEMO: {user.email}'))
        self.stdout.write(self.style.WARNING(f'{"="*60}\n'))

        # Step 1: Clear all existing data
        self.stdout.write('1. Limpando dados antigos...')
        Bill.objects.filter(user=user).delete()
        BankConnection.objects.filter(user=user).delete()
        Category.objects.filter(user=user).delete()
        self.stdout.write(self.style.SUCCESS('   Dados antigos removidos'))

        # Step 2: Create categories
        self.stdout.write('\n2. Criando categorias...')
        categories = self._create_categories(user)
        self.stdout.write(self.style.SUCCESS(f'   {len(categories)} categorias criadas'))

        # Step 3: Create connectors and accounts
        self.stdout.write('\n3. Criando contas bancarias...')
        accounts = self._create_accounts(user)
        self.stdout.write(self.style.SUCCESS(f'   {len(accounts)} contas criadas'))

        # Step 4: Create transactions
        self.stdout.write('\n4. Criando transacoes...')
        total_transactions = 0
        for account in accounts:
            count = self._create_transactions(account, user, categories)
            total_transactions += count
            self.stdout.write(f'   - {account.name}: {count} transacoes')
        self.stdout.write(self.style.SUCCESS(f'   Total: {total_transactions} transacoes'))

        # Step 5: Create bills
        self.stdout.write('\n5. Criando contas a pagar/receber...')
        bills_count = self._create_bills(user, categories)
        self.stdout.write(self.style.SUCCESS(f'   {bills_count} bills criados'))

        # Summary
        self.stdout.write(self.style.SUCCESS(f'\n{"="*60}'))
        self.stdout.write(self.style.SUCCESS('RESUMO'))
        self.stdout.write(self.style.SUCCESS(f'{"="*60}'))
        self.stdout.write(f'Contas Bancarias: {len(accounts)}')
        self.stdout.write(f'Transacoes: {total_transactions}')
        self.stdout.write(f'Bills: {bills_count}')
        self.stdout.write(self.style.SUCCESS(f'\nDados demo atualizados com sucesso!'))

    def _create_categories(self, user):
        """Create categories based on Pluggy standard categories"""
        categories_data = {
            'income': [
                ('Salario', '#10b981', '💰'),
                ('Atividades de empreendedorismo', '#059669', '💼'),
                ('Renda nao-recorrente', '#34d399', '🎁'),
                ('Juros de rendimentos de dividendos', '#6ee7b7', '📈'),
                ('Transferencia - PIX', '#22c55e', '⚡'),
                ('Transferencia mesma titularidade', '#16a34a', '🔄'),
            ],
            'expense': [
                ('Supermercado', '#f59e0b', '🛒'),
                ('Alimentos e bebidas', '#ea580c', '🍔'),
                ('Compras', '#f97316', '🛍️'),
                ('Compras online', '#fb923c', '📦'),
                ('Aluguel', '#ef4444', '🏠'),
                ('Eletricidade', '#dc2626', '💡'),
                ('Agua', '#3b82f6', '💧'),
                ('Internet', '#6366f1', '🌐'),
                ('Celular', '#8b5cf6', '📱'),
                ('Servicos', '#a855f7', '🛠️'),
                ('Impostos', '#64748b', '📋'),
                ('Taxas bancarias', '#475569', '🏦'),
                ('Transporte', '#0ea5e9', '🚗'),
                ('Postos de gasolina', '#0284c7', '⛽'),
                ('Saude', '#ec4899', '🏥'),
                ('Farmacia', '#db2777', '💊'),
                ('Educacao', '#8b5cf6', '📚'),
                ('Streaming de video', '#7c3aed', '📺'),
                ('Streaming de musica', '#6d28d9', '🎵'),
                ('Restaurantes, bares e lanchonetes', '#f43f5e', '🍽️'),
                ('Delivery de alimentos', '#e11d48', '🛵'),
                ('Transferencia - PIX', '#64748b', '⚡'),
                ('Apostas', '#dc2626', '🎰'),
                ('Outros', '#94a3b8', '📁'),
            ]
        }

        categories = {}
        for cat_type, items in categories_data.items():
            for name, color, icon in items:
                category, _ = Category.objects.get_or_create(
                    user=user,
                    name=name,
                    type=cat_type,
                    defaults={'color': color, 'icon': icon, 'is_system': True}
                )
                categories[name] = category

        return categories

    def _create_accounts(self, user):
        """Create fake bank accounts"""
        banks = [
            {
                'pluggy_id': 999001,
                'name': 'Banco Inter',
                'logo': 'https://logo.clearbit.com/bancointer.com.br',
                'color': '#FF7A00',
            },
            {
                'pluggy_id': 999002,
                'name': 'Mercado Pago',
                'logo': 'https://logo.clearbit.com/mercadopago.com.br',
                'color': '#009EE3',
            },
            {
                'pluggy_id': 999003,
                'name': 'Nubank',
                'logo': 'https://logo.clearbit.com/nubank.com.br',
                'color': '#8A05BE',
            },
        ]

        accounts_config = [
            {'bank_idx': 0, 'name': 'BANCO INTER', 'type': 'CHECKING', 'balance': Decimal('12450.83')},
            {'bank_idx': 1, 'name': 'Mercado Pago', 'type': 'CHECKING', 'balance': Decimal('3280.45')},
            {'bank_idx': 2, 'name': 'Nubank Conta', 'type': 'CHECKING', 'balance': Decimal('8920.17')},
        ]

        accounts = []
        for config in accounts_config:
            bank = banks[config['bank_idx']]

            connector, _ = Connector.objects.get_or_create(
                pluggy_id=bank['pluggy_id'],
                defaults={
                    'name': bank['name'],
                    'institution_name': bank['name'],
                    'logo_url': bank['logo'],
                    'primary_color': bank['color'],
                    'type': 'PERSONAL_BANK',
                    'country': 'BR',
                    'is_active': True,
                    'is_sandbox': True,
                }
            )

            connection, _ = BankConnection.objects.get_or_create(
                user=user,
                connector=connector,
                defaults={
                    'pluggy_item_id': f'demo_{uuid.uuid4().hex[:16]}',
                    'status': 'UPDATED',
                    'is_active': True,
                }
            )

            account = BankAccount.objects.create(
                connection=connection,
                pluggy_account_id=f'demo_acc_{uuid.uuid4().hex[:16]}',
                type=config['type'],
                name=config['name'],
                balance=config['balance'],
                is_active=True,
            )
            accounts.append(account)

        return accounts

    def _create_transactions(self, account, user, categories):
        """Create realistic transactions for the last 90 days"""
        now = timezone.now()
        transactions_created = 0

        # Define patterns based on account
        is_main_account = 'INTER' in account.name.upper()
        is_mp = 'MERCADO' in account.name.upper()

        # --- RECEITAS ---

        # Vendas diarias (principalmente na conta principal)
        if is_main_account:
            for days_ago in range(90):
                date = now - timedelta(days=days_ago)
                if date.weekday() == 6:  # Skip Sunday
                    continue

                # Vendas do dia
                num_sales = random.randint(3, 8) if date.weekday() in [4, 5] else random.randint(1, 5)

                for _ in range(num_sales):
                    payment_type = random.choices(
                        ['Cartao De Credito - Stripe', 'Cartao De Debito - Stripe', 'PIX'],
                        weights=[40, 30, 30]
                    )[0]

                    amount = Decimal(str(round(random.uniform(45.00, 350.00), 2)))
                    hour = random.randint(8, 21)
                    minute = random.randint(0, 59)
                    tx_date = date.replace(hour=hour, minute=minute, second=0, microsecond=0)

                    if 'PIX' in payment_type:
                        desc = f'Pix recebido - Cliente {random.choice(["Maria", "Joao", "Ana", "Carlos", "Pedro", "Julia"])}'
                        cat_name = 'Transferencia - PIX'
                    else:
                        desc = f'Credito domicilio cartao - {payment_type}'
                        cat_name = 'Atividades de empreendedorismo'

                    Transaction.objects.create(
                        account=account,
                        pluggy_transaction_id=f'tx_{uuid.uuid4().hex[:20]}',
                        type='CREDIT',
                        description=desc,
                        amount=amount,
                        currency_code='BRL',
                        date=tx_date,
                        pluggy_category=cat_name,
                        user_category=categories.get(cat_name),
                    )
                    transactions_created += 1

        # Transferencias entre contas
        if is_mp or 'NUBANK' in account.name.upper():
            for _ in range(random.randint(5, 15)):
                days_ago = random.randint(0, 90)
                date = (now - timedelta(days=days_ago)).replace(
                    hour=random.randint(9, 18), minute=random.randint(0, 59)
                )
                amount = Decimal(str(round(random.uniform(100, 2000), 2)))

                Transaction.objects.create(
                    account=account,
                    pluggy_transaction_id=f'tx_{uuid.uuid4().hex[:20]}',
                    type='CREDIT',
                    description=f'Transferencia Pix recebida LEVI LAEL COELHO SILVA',
                    amount=amount,
                    currency_code='BRL',
                    date=date,
                    pluggy_category='Transferencia mesma titularidade',
                    user_category=categories.get('Transferencia mesma titularidade'),
                )
                transactions_created += 1

        # --- DESPESAS ---

        # Despesas fixas mensais (apenas na conta principal)
        if is_main_account:
            fixed_expenses = [
                (5, 'Aluguel Comercial - Imobiliaria Centro', Decimal('3200.00'), 'Aluguel'),
                (10, 'CPFL Energia - Conta de Luz', (450.00, 780.00), 'Eletricidade'),
                (12, 'Sabesp - Conta de Agua', (180.00, 320.00), 'Agua'),
                (15, 'Vivo Empresarial - Internet', Decimal('249.90'), 'Internet'),
                (8, 'Claro - Celular Empresarial', Decimal('189.90'), 'Celular'),
                (20, 'DAS - Simples Nacional', (850.00, 1450.00), 'Impostos'),
                (22, 'Servicos Contabeis - Contabilidade Silva', Decimal('550.00'), 'Servicos'),
            ]

            for month_offset in range(3):
                for day, desc, amount, cat_name in fixed_expenses:
                    try:
                        tx_date = (now.replace(day=1) - timedelta(days=month_offset * 30)).replace(
                            day=day, hour=random.randint(7, 11), minute=random.randint(0, 59)
                        )
                    except ValueError:
                        continue

                    if tx_date > now:
                        continue

                    if isinstance(amount, tuple):
                        final_amount = Decimal(str(round(random.uniform(*amount), 2)))
                    else:
                        final_amount = amount

                    Transaction.objects.create(
                        account=account,
                        pluggy_transaction_id=f'tx_{uuid.uuid4().hex[:20]}',
                        type='DEBIT',
                        description=desc,
                        amount=final_amount,
                        currency_code='BRL',
                        date=tx_date,
                        pluggy_category=cat_name,
                        user_category=categories.get(cat_name),
                    )
                    transactions_created += 1

        # Compras e servicos variados
        variable_expenses = [
            ('Pix enviado - Pay4fun Instituicao De Pagamento Sa', (20.00, 100.00), 'Servicos'),
            ('Pix enviado - Gowd Instituicao De Pagamento Ltda', (50.00, 150.00), 'Servicos'),
            ('Compra no Debito - Supermercado Dia', (80.00, 350.00), 'Supermercado'),
            ('Compra no Debito - Posto Shell', (100.00, 400.00), 'Postos de gasolina'),
            ('Compra no Debito - Farmacia Drogasil', (25.00, 180.00), 'Farmacia'),
            ('Pix enviado - iFood', (25.00, 95.00), 'Delivery de alimentos'),
            ('Pix enviado - Uber', (15.00, 65.00), 'Transporte'),
            ('Pix enviado - 99', (12.00, 55.00), 'Transporte'),
            ('Netflix.com', Decimal('55.90'), 'Streaming de video'),
            ('Spotify', Decimal('34.90'), 'Streaming de musica'),
            ('Amazon Prime', Decimal('19.90'), 'Streaming de video'),
            ('Compra Online - Mercado Livre', (35.00, 450.00), 'Compras online'),
            ('Compra Online - Amazon', (45.00, 380.00), 'Compras online'),
            ('Compra Online - Shopee', (15.00, 180.00), 'Compras online'),
        ]

        for _ in range(random.randint(25, 45)):
            days_ago = random.randint(0, 90)
            tx_date = (now - timedelta(days=days_ago)).replace(
                hour=random.randint(8, 22), minute=random.randint(0, 59)
            )

            desc, amount, cat_name = random.choice(variable_expenses)

            if isinstance(amount, tuple):
                final_amount = Decimal(str(round(random.uniform(*amount), 2)))
            else:
                final_amount = amount

            Transaction.objects.create(
                account=account,
                pluggy_transaction_id=f'tx_{uuid.uuid4().hex[:20]}',
                type='DEBIT',
                description=desc,
                amount=final_amount,
                currency_code='BRL',
                date=tx_date,
                pluggy_category=cat_name,
                user_category=categories.get(cat_name),
            )
            transactions_created += 1

        # Transferencias PIX para terceiros
        pix_recipients = [
            'Maria Santos', 'Joao Silva', 'Ana Costa', 'Carlos Oliveira',
            'Pedro Souza', 'Julia Ferreira', 'Lucas Almeida', 'Camila Rodrigues'
        ]

        for _ in range(random.randint(8, 20)):
            days_ago = random.randint(0, 90)
            tx_date = (now - timedelta(days=days_ago)).replace(
                hour=random.randint(8, 21), minute=random.randint(0, 59)
            )

            recipient = random.choice(pix_recipients)
            amount = Decimal(str(round(random.uniform(10, 500), 2)))

            Transaction.objects.create(
                account=account,
                pluggy_transaction_id=f'tx_{uuid.uuid4().hex[:20]}',
                type='DEBIT',
                description=f'Pix enviado - {recipient}',
                amount=amount,
                currency_code='BRL',
                date=tx_date,
                pluggy_category='Transferencia - PIX',
                user_category=categories.get('Transferencia - PIX'),
            )
            transactions_created += 1

        return transactions_created

    def _create_bills(self, user, categories):
        """Create bills (accounts payable and receivable)"""
        now = timezone.now()
        bills_created = 0

        # Contas a Pagar (proximos 30 dias)
        payables = [
            ('Aluguel Comercial - Janeiro', Decimal('3200.00'), 5, 'Aluguel'),
            ('CPFL Energia', Decimal('685.40'), 10, 'Eletricidade'),
            ('Sabesp - Agua', Decimal('245.80'), 12, 'Agua'),
            ('Internet Vivo', Decimal('249.90'), 15, 'Internet'),
            ('Celular Claro', Decimal('189.90'), 8, 'Celular'),
            ('DAS Simples Nacional', Decimal('1180.00'), 20, 'Impostos'),
            ('Contador - Honorarios', Decimal('550.00'), 22, 'Servicos'),
            ('Fornecedor ABC - Mercadorias', Decimal('4500.00'), 18, 'Supermercado'),
            ('Fornecedor XYZ - Produtos', Decimal('2800.00'), 25, 'Supermercado'),
        ]

        for desc, amount, day, cat_name in payables:
            try:
                due_date = now.replace(day=1) + timedelta(days=day - 1)
                if due_date.month != now.month:
                    due_date = (now.replace(day=1) + timedelta(days=32)).replace(day=day)
            except ValueError:
                due_date = now + timedelta(days=day)

            status = 'pending'
            amount_paid = Decimal('0.00')

            # Some bills in the past should be paid
            if due_date.date() < now.date():
                status = 'paid'
                amount_paid = amount

            Bill.objects.create(
                user=user,
                type='payable',
                description=desc,
                amount=amount,
                amount_paid=amount_paid,
                due_date=due_date.date(),
                status=status,
                category=categories.get(cat_name),
                customer_supplier='Fornecedor',
            )
            bills_created += 1

        # Contas a Receber (proximos 30 dias)
        receivables = [
            ('Cliente A - Venda Parcelada 1/3', Decimal('850.00'), 10),
            ('Cliente B - Servico Prestado', Decimal('1200.00'), 15),
            ('Cliente C - Venda Parcelada 2/4', Decimal('450.00'), 20),
            ('Cliente D - Produto Encomendado', Decimal('680.00'), 8),
            ('Cliente E - Consultoria', Decimal('2500.00'), 25),
        ]

        for desc, amount, day in receivables:
            try:
                due_date = now.replace(day=1) + timedelta(days=day - 1)
                if due_date.month != now.month:
                    due_date = (now.replace(day=1) + timedelta(days=32)).replace(day=day)
            except ValueError:
                due_date = now + timedelta(days=day)

            status = 'pending'
            amount_paid = Decimal('0.00')

            if due_date.date() < now.date():
                status = 'paid'
                amount_paid = amount

            Bill.objects.create(
                user=user,
                type='receivable',
                description=desc,
                amount=amount,
                amount_paid=amount_paid,
                due_date=due_date.date(),
                status=status,
                category=categories.get('Atividades de empreendedorismo'),
                customer_supplier='Cliente',
            )
            bills_created += 1

        # Adicionar alguns bills atrasados
        overdue_payables = [
            ('Fornecedor Atrasado - Nota 1234', Decimal('1850.00'), -5),
            ('Manutencao Equipamentos', Decimal('780.00'), -10),
        ]

        for desc, amount, days_offset in overdue_payables:
            due_date = now.date() + timedelta(days=days_offset)

            Bill.objects.create(
                user=user,
                type='payable',
                description=desc,
                amount=amount,
                amount_paid=Decimal('0.00'),
                due_date=due_date,
                status='pending',
                category=categories.get('Servicos'),
                customer_supplier='Fornecedor',
            )
            bills_created += 1

        return bills_created
