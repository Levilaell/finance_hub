"""
Populate a bank account with realistic test transactions
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from apps.banking.models import BankAccount, Transaction, Category, Bill
from decimal import Decimal
import uuid
import random
from datetime import datetime, timedelta

User = get_user_model()


class Command(BaseCommand):
    help = 'Populate a bank account with realistic test transactions'

    # Realistic transaction templates for PERSONAL accounts (Portuguese)
    # Descrições como aparecem em extratos bancários reais
    TRANSACTION_TEMPLATES = {
        'Alimentação': {
            'type': 'DEBIT',
            'merchants': [
                'PIX QR CODE - IFOOD',
                'RAPPI*RAPPI BRASIL',
                'PAG*JoseDaSilva',
                'PIX - RESTAURANTE SABOR',
                'DEBITO MASTERCARD - OUTBACK',
                'COMPRA CARTAO - STARBUCKS',
                'PAG*MariaRestaurante',
                'PIX QR CODE - UBER EATS',
            ],
            'amount_range': (18.00, 95.00),
            'frequency': 0.12,
        },
        'Mercado': {
            'type': 'DEBIT',
            'merchants': [
                'COMPRA CARTAO - CARREFOUR',
                'DEBITO - PAO DE ACUCAR',
                'PIX - ASSAI ATACADISTA',
                'COMPRA CARTAO - EXTRA HIPER',
                'DEBITO VISA - SONDA SUPERM',
                'PIX QR CODE - HORTIFRUTI',
            ],
            'amount_range': (85.00, 420.00),
            'frequency': 0.10,
        },
        'Transporte': {
            'type': 'DEBIT',
            'merchants': [
                'UBER *UBER *TRIP',
                '99 *99APP',
                'AUTO POSTO IPIRANGA',
                'SHELL SELECT',
                'DEBITO - ESTAPAR',
                'PIX - PEDAGIO ECOVIAS',
                'UBER *UBER *TRIP HELP',
                '99* 99POP',
            ],
            'amount_range': (12.00, 180.00),
            'frequency': 0.10,
        },
        'Compras': {
            'type': 'DEBIT',
            'merchants': [
                'AMAZON.COM.BR',
                'MERCADOLIVRE*MELI',
                'MAGALU*MAGAZINELUIZA',
                'COMPRA CARTAO - RENNER',
                'SHEIN BRAZIL',
                'ALIEXPRESS.COM',
                'PIX - CASAS BAHIA',
                'SHOPEE BRAZIL',
            ],
            'amount_range': (45.00, 380.00),
            'frequency': 0.08,
        },
        'Contas e Serviços': {
            'type': 'DEBIT',
            'merchants': [
                'DEB AUTO CPFL ENERGIA',
                'DEB AUTO SABESP',
                'PAG BOLETO - VIVO',
                'DEB AUTO CLARO',
                'PAG BOLETO - CONDOMINIO',
                'PIX - CONSORCIO HONDA',
            ],
            'amount_range': (89.00, 520.00),
            'frequency': 0.06,
        },
        'Lazer': {
            'type': 'DEBIT',
            'merchants': [
                'SPOTIFY P*SPOTIFY',
                'NETFLIX.COM',
                'PRIME VIDEO*AMAZON',
                'STEAM PURCHASE',
                'PIX - INGRESSO.COM',
                'HBO MAX',
                'DISNEY PLUS',
            ],
            'amount_range': (14.90, 89.90),
            'frequency': 0.06,
        },
        'Saúde': {
            'type': 'DEBIT',
            'merchants': [
                'DROGASIL',
                'DROGA RAIA',
                'FARMACIA SAO PAULO',
                'PIX - LABORATORIO FLEURY',
                'DEB AUTO - UNIMED',
                'COMPRA - DROGARIA ARAUJO',
            ],
            'amount_range': (25.00, 280.00),
            'frequency': 0.04,
        },
        'Assinaturas': {
            'type': 'DEBIT',
            'merchants': [
                'APPLE.COM/BILL',
                'GOOGLE *GOOGLE STORAGE',
                'CANVA* PRO MONTHLY',
                'MICROSOFT*OFFICE365',
                'ADOBE *CREATIVE CLOUD',
                'CHATGPT SUBSCRIPTION',
            ],
            'amount_range': (9.90, 69.90),
            'frequency': 0.04,
        },
        'Salário': {
            'type': 'CREDIT',
            'merchants': [
                'TED RECEBIDA - TECH SOLUTIONS LTDA',
                'CREDITO SALARIO - EMPRESA ABC SA',
                'TED RECEBIDA - CONSULTING GROUP',
                'CREDITO FOLHA - CORP SISTEMAS',
            ],
            'amount_range': (4500.00, 12000.00),
            'frequency': 0.08,
        },
        'Freelance': {
            'type': 'CREDIT',
            'merchants': [
                'PIX RECEBIDO - JOAO SILVA',
                'TED RECEBIDA - MARIA SANTOS ME',
                'PIX RECEBIDO - STARTUP XYZ',
                'TED RECEBIDA - AGENCIA DIGITAL',
                'PIX RECEBIDO - CLIENTE PJ',
            ],
            'amount_range': (800.00, 4500.00),
            'frequency': 0.10,
        },
        'Investimentos': {
            'type': 'CREDIT',
            'merchants': [
                'RESGATE CDB - NUBANK',
                'DIVIDENDOS - ITAUSA PN',
                'RENDIMENTO POUPANCA',
                'RESGATE TESOURO DIRETO',
                'JCP - BANCO DO BRASIL',
                'DIVIDENDOS - PETR4',
            ],
            'amount_range': (50.00, 850.00),
            'frequency': 0.06,
        },
        'Transferências Recebidas': {
            'type': 'CREDIT',
            'merchants': [
                'PIX RECEBIDO - CPF ***.456.***',
                'TED RECEBIDA - BANCO INTER',
                'PIX RECEBIDO - NUBANK',
                'TRANSF RECEBIDA - C6 BANK',
                'PIX RECEBIDO - CPF ***.789.***',
            ],
            'amount_range': (100.00, 2000.00),
            'frequency': 0.08,
        },
        'Outras Despesas': {
            'type': 'DEBIT',
            'merchants': [
                'PIX ENVIADO - CPF ***.123.***',
                'TED ENVIADA - BANCO BRADESCO',
                'PIX ENVIADO - CHAVE ALEATORIA',
                'SAQUE 24H - BANCO24HORAS',
            ],
            'amount_range': (50.00, 500.00),
            'frequency': 0.04,
        },
        'Outras Receitas': {
            'type': 'CREDIT',
            'merchants': [
                'ESTORNO - COMPRA DUPLICADA',
                'DEVOLUCAO - MERCADOLIVRE',
                'CASHBACK - NUBANK',
                'REEMBOLSO - UBER',
                'ESTORNO - AMAZON',
            ],
            'amount_range': (15.00, 200.00),
            'frequency': 0.04,
        },
    }

    # Retail business transaction templates (Portuguese)
    RETAIL_TEMPLATES = {
        'Vendas': {
            'type': 'CREDIT',
            'merchants': [
                'Venda PDV - Débito',
                'Venda PDV - Crédito',
                'Venda PDV - Pix',
                'Venda PDV - Dinheiro',
                'Stone - Vendas Cartão',
                'Cielo - Vendas Cartão',
                'PagSeguro - Vendas Online',
                'Mercado Pago - Recebimento',
                'Ifood - Repasse Vendas',
                'Rappi - Recebimento',
            ],
            'amount_range': (25.00, 850.00),
            'frequency': 0.45,  # 45% - Principal receita
        },
        'Compra de Estoque': {
            'type': 'DEBIT',
            'merchants': [
                'Fornecedor Atacado Central',
                'Distribuidora Alimentos Ltda',
                'Martins Atacado',
                'Makro Atacadista',
                'Assaí Atacadista',
                'Fornecedor Bebidas Sul',
                'Indústria Produtos Ltda',
                'Importadora ABC',
            ],
            'amount_range': (500.00, 5000.00),
            'frequency': 0.15,  # 15% - Compra de estoque
        },
        'Aluguel e Infraestrutura': {
            'type': 'DEBIT',
            'merchants': [
                'Aluguel Loja - Imobiliária',
                'Condomínio Shopping Center',
                'CPFL Energia Comercial',
                'Sabesp Conta Comercial',
                'Vivo Empresarial Internet',
                'Limpeza e Conservação',
                'Segurança Patrimonial',
            ],
            'amount_range': (200.00, 3500.00),
            'frequency': 0.08,  # 8% - Custos fixos
        },
        'Folha de Pagamento': {
            'type': 'DEBIT',
            'merchants': [
                'Folha de Pagamento',
                'Salário Funcionário',
                'INSS Empresa',
                'FGTS Depósito',
                'Vale Transporte',
                'Vale Refeição Sodexo',
                'Plano de Saúde Unimed',
            ],
            'amount_range': (1200.00, 4500.00),
            'frequency': 0.10,  # 10% - Folha de pagamento
        },
        'Marketing e Publicidade': {
            'type': 'DEBIT',
            'merchants': [
                'Google Ads',
                'Facebook Ads',
                'Instagram Ads',
                'Gráfica Rápida - Panfletos',
                'Banner e Faixas',
                'Agência Marketing Digital',
                'Ifood - Taxa Publicidade',
            ],
            'amount_range': (50.00, 1200.00),
            'frequency': 0.06,  # 6% - Marketing
        },
        'Despesas Operacionais': {
            'type': 'DEBIT',
            'merchants': [
                'Embalagens e Sacolas',
                'Material de Limpeza',
                'Papelaria e Escritório',
                'Manutenção Equipamentos',
                'Contador Serviços',
                'Advogado Consultoria',
                'Taxas Bancárias',
                'Taxa Maquininha Cartão',
            ],
            'amount_range': (30.00, 800.00),
            'frequency': 0.08,  # 8% - Despesas operacionais
        },
        'Impostos': {
            'type': 'DEBIT',
            'merchants': [
                'Simples Nacional - DAS',
                'ISS Prefeitura',
                'ICMS Estado',
                'PIS/COFINS',
                'Impostos Diversos',
            ],
            'amount_range': (300.00, 2500.00),
            'frequency': 0.05,  # 5% - Impostos
        },
        'Transferências Bancárias': {
            'type': 'DEBIT',
            'merchants': [
                'TED - Fornecedor',
                'Pix - Pagamento',
                'Transferência Banco',
                'Saque Caixa',
            ],
            'amount_range': (100.00, 3000.00),
            'frequency': 0.03,  # 3% - Transferências
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
        parser.add_argument(
            '--mode',
            type=str,
            choices=['personal', 'retail'],
            default='personal',
            help='Transaction mode: personal (default) or retail business'
        )
        parser.add_argument(
            '--clear-bills',
            action='store_true',
            help='Delete existing bills for this user before creating new ones'
        )
        parser.add_argument(
            '--create-bills',
            action='store_true',
            help='Create test bills (contas a pagar/receber) for this month'
        )

    def handle(self, *args, **options):
        account_id = options.get('account_id')
        user_email = options.get('user_email')
        count = options.get('count')
        days_back = options.get('days_back')
        clear_existing = options.get('clear_existing')
        mode = options.get('mode')
        clear_bills = options.get('clear_bills')
        create_bills = options.get('create_bills')

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

        mode_label = 'RETAIL BUSINESS' if mode == 'retail' else 'PERSONAL'
        self.stdout.write(
            self.style.WARNING(
                f'\nTarget Account: {account.name} ({account.type})'
            )
        )
        self.stdout.write(f'User: {user.email}')
        self.stdout.write(f'Mode: {mode_label}')
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
        self._ensure_categories(user, mode)

        # Create transactions
        self.stdout.write(f'\nCreating {count} test transactions...\n')
        created_count = self._create_transactions(account, user, count, days_back, mode)

        self.stdout.write(
            self.style.SUCCESS(
                f'\nSuccessfully created {created_count} test transactions!'
            )
        )

        # Handle bills
        if clear_bills:
            deleted_bills = Bill.objects.filter(user=user).count()
            Bill.objects.filter(user=user).delete()
            self.stdout.write(
                self.style.WARNING(f'\nDeleted {deleted_bills} existing bills')
            )

        if create_bills:
            self.stdout.write('\nCreating test bills for this month...')
            bills_count = self._create_bills(user)
            self.stdout.write(
                self.style.SUCCESS(f'Successfully created {bills_count} test bills!')
            )

        # Show summary
        self._show_summary(account)

    def _ensure_categories(self, user, mode='personal'):
        """Ensure all necessary categories exist for the user"""
        if mode == 'retail':
            # Create retail-specific categories (Portuguese)
            retail_categories = {
                'income': [
                    {'name': 'Vendas', 'color': '#10b981', 'icon': '💰'},
                ],
                'expense': [
                    {'name': 'Compra de Estoque', 'color': '#f59e0b', 'icon': '📦'},
                    {'name': 'Aluguel e Infraestrutura', 'color': '#6366f1', 'icon': '🏢'},
                    {'name': 'Folha de Pagamento', 'color': '#ef4444', 'icon': '👥'},
                    {'name': 'Marketing e Publicidade', 'color': '#ec4899', 'icon': '📢'},
                    {'name': 'Despesas Operacionais', 'color': '#8b5cf6', 'icon': '⚙️'},
                    {'name': 'Impostos', 'color': '#64748b', 'icon': '🏛️'},
                    {'name': 'Transferências Bancárias', 'color': '#06b6d4', 'icon': '🔄'},
                ]
            }

            for category_type, categories in retail_categories.items():
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
                        self.stdout.write(f"  + Categoria criada: {cat_data['name']}")
        else:
            # Personal categories (Portuguese)
            personal_categories = {
                'income': [
                    {'name': 'Salário', 'color': '#10b981', 'icon': '💵'},
                    {'name': 'Freelance', 'color': '#059669', 'icon': '💻'},
                    {'name': 'Investimentos', 'color': '#34d399', 'icon': '📈'},
                    {'name': 'Transferências Recebidas', 'color': '#0ea5e9', 'icon': '🔄'},
                    {'name': 'Outras Receitas', 'color': '#6ee7b7', 'icon': '💰'},
                ],
                'expense': [
                    {'name': 'Alimentação', 'color': '#f59e0b', 'icon': '🍽️'},
                    {'name': 'Mercado', 'color': '#ef4444', 'icon': '🛒'},
                    {'name': 'Transporte', 'color': '#ec4899', 'icon': '🚗'},
                    {'name': 'Compras', 'color': '#6366f1', 'icon': '🛍️'},
                    {'name': 'Contas e Serviços', 'color': '#8b5cf6', 'icon': '📄'},
                    {'name': 'Lazer', 'color': '#14b8a6', 'icon': '🎬'},
                    {'name': 'Saúde', 'color': '#f43f5e', 'icon': '🏥'},
                    {'name': 'Assinaturas', 'color': '#a855f7', 'icon': '📱'},
                    {'name': 'Outras Despesas', 'color': '#64748b', 'icon': '📦'},
                ]
            }

            for category_type, categories in personal_categories.items():
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
                        self.stdout.write(f"  + Categoria criada: {cat_data['name']}")

    def _create_transactions(self, account, user, count, days_back, mode='personal'):
        """Create realistic test transactions"""
        transactions_created = 0
        now = timezone.now()

        # Select templates based on mode
        templates = self.RETAIL_TEMPLATES if mode == 'retail' else self.TRANSACTION_TEMPLATES

        # Build weighted list of categories based on frequency
        category_pool = []
        for category_name, config in templates.items():
            weight = int(config['frequency'] * 1000)
            category_pool.extend([category_name] * weight)

        for i in range(count):
            # Select random category
            category_name = random.choice(category_pool)
            config = templates[category_name]

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
        self.stdout.write(self.style.SUCCESS('RESUMO'))
        self.stdout.write('='*50)
        self.stdout.write(f'Total de Transações de Teste: {transactions.count()}')
        self.stdout.write(f'Total de Receitas: R$ {total_income:,.2f}')
        self.stdout.write(f'Total de Despesas: R$ {total_expenses:,.2f}')
        self.stdout.write(f'Saldo Líquido: R$ {balance:,.2f}')
        self.stdout.write('='*50 + '\n')

    def _create_bills(self, user):
        """Create test bills (contas a pagar/receber) for this month"""
        now = timezone.now()
        bills_created = 0

        # Bills templates - Contas a Pagar (payable)
        payable_bills = [
            {'description': 'Aluguel - Dezembro', 'amount': Decimal('2800.00'), 'due_day': 5},
            {'description': 'CPFL Energia', 'amount': Decimal('385.50'), 'due_day': 10},
            {'description': 'Sabesp - Água', 'amount': Decimal('145.80'), 'due_day': 12},
            {'description': 'Vivo Internet', 'amount': Decimal('199.90'), 'due_day': 15},
            {'description': 'Claro Celular', 'amount': Decimal('89.90'), 'due_day': 18},
            {'description': 'Netflix', 'amount': Decimal('55.90'), 'due_day': 5},
            {'description': 'Spotify', 'amount': Decimal('21.90'), 'due_day': 8},
            {'description': 'Amazon Prime', 'amount': Decimal('14.90'), 'due_day': 20},
            {'description': 'Cartão Nubank', 'amount': Decimal('1250.00'), 'due_day': 10},
            {'description': 'Cartão C6 Bank', 'amount': Decimal('890.00'), 'due_day': 15},
            {'description': 'Seguro Auto', 'amount': Decimal('280.00'), 'due_day': 22},
            {'description': 'Plano de Saúde', 'amount': Decimal('450.00'), 'due_day': 1},
            {'description': 'Condomínio', 'amount': Decimal('680.00'), 'due_day': 10},
            {'description': 'Academia', 'amount': Decimal('99.90'), 'due_day': 5},
            {'description': 'IPTU Parcela 12/12', 'amount': Decimal('320.00'), 'due_day': 28},
        ]

        # Bills templates - Contas a Receber (receivable)
        receivable_bills = [
            {'description': 'Salário - Empresa XYZ', 'amount': Decimal('5500.00'), 'due_day': 5},
            {'description': 'Freelance - Projeto Web', 'amount': Decimal('2800.00'), 'due_day': 15},
            {'description': 'Consultoria - Cliente ABC', 'amount': Decimal('1500.00'), 'due_day': 20},
            {'description': 'Aluguel Recebido - Apt 201', 'amount': Decimal('1800.00'), 'due_day': 10},
            {'description': 'Dividendos - Ações', 'amount': Decimal('250.00'), 'due_day': 25},
        ]

        # Create payable bills
        for bill_data in payable_bills:
            due_date = now.replace(day=bill_data['due_day'])

            # Determine status based on due date
            if due_date.date() < now.date():
                status = 'paid' if random.random() > 0.3 else 'pending'  # 70% paid if past
            else:
                status = 'pending'

            Bill.objects.create(
                user=user,
                type='payable',
                description=bill_data['description'],
                amount=bill_data['amount'],
                amount_paid=bill_data['amount'] if status == 'paid' else Decimal('0.00'),
                due_date=due_date,
                status=status,
                paid_at=now if status == 'paid' else None,
            )
            bills_created += 1
            self.stdout.write(f"  + A Pagar: {bill_data['description']} - R$ {bill_data['amount']}")

        # Create receivable bills
        for bill_data in receivable_bills:
            due_date = now.replace(day=bill_data['due_day'])

            # Determine status based on due date
            if due_date.date() < now.date():
                status = 'paid' if random.random() > 0.2 else 'pending'  # 80% received if past
            else:
                status = 'pending'

            Bill.objects.create(
                user=user,
                type='receivable',
                description=bill_data['description'],
                amount=bill_data['amount'],
                amount_paid=bill_data['amount'] if status == 'paid' else Decimal('0.00'),
                due_date=due_date,
                status=status,
                paid_at=now if status == 'paid' else None,
            )
            bills_created += 1
            self.stdout.write(f"  + A Receber: {bill_data['description']} - R$ {bill_data['amount']}")

        return bills_created


# Import models for aggregation
from django.db import models
