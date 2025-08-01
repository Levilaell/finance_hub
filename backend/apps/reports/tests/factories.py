"""
Test factories for reports app using factory_boy for generating test data
"""
import factory
from datetime import date, timedelta
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.utils import timezone

from apps.companies.models import Company, Subscription
from apps.banking.models import BankAccount, Transaction
from apps.categories.models import Category
from apps.reports.models import Report, ScheduledReport, ReportTemplate

User = get_user_model()


class CompanyFactory(factory.django.DjangoModelFactory):
    """Factory for creating Company instances"""
    
    class Meta:
        model = Company
    
    name = factory.Sequence(lambda n: f"Test Company {n}")
    cnpj = factory.Sequence(lambda n: f"{str(n).zfill(11)}000{str(n % 100).zfill(2)}")
    trading_name = factory.LazyAttribute(lambda obj: f"{obj.name} Trading")
    email = factory.LazyAttribute(lambda obj: f"contact@{obj.name.lower().replace(' ', '')}.com")
    phone = factory.Sequence(lambda n: f"+55 11 9{str(n).zfill(8)}")
    address = factory.Faker('address')
    city = factory.Faker('city')
    state = factory.Faker('state_abbr')
    postal_code = factory.Faker('postcode')


class UserFactory(factory.django.DjangoModelFactory):
    """Factory for creating User instances"""
    
    class Meta:
        model = User
    
    email = factory.Faker('email')
    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')
    is_verified = True
    is_active = True
    company = factory.SubFactory(CompanyFactory)
    
    @factory.post_generation
    def set_password(self, create, extracted, **kwargs):
        if not create:
            return
        
        password = extracted or 'testpass123'
        self.set_password(password)
        self.save()


class SubscriptionFactory(factory.django.DjangoModelFactory):
    """Factory for creating Subscription instances"""
    
    class Meta:
        model = Subscription
    
    company = factory.SubFactory(CompanyFactory)
    plan = factory.Iterator(['starter', 'professional', 'premium', 'enterprise'])
    status = factory.Iterator(['active', 'past_due', 'canceled', 'unpaid'])
    current_period_start = factory.LazyFunction(timezone.now)
    current_period_end = factory.LazyAttribute(
        lambda obj: obj.current_period_start + timedelta(days=30)
    )
    stripe_subscription_id = factory.Sequence(lambda n: f"sub_test_{n}")
    stripe_customer_id = factory.Sequence(lambda n: f"cus_test_{n}")
    
    @factory.lazy_attribute
    def plan_data(self):
        plan_configs = {
            'starter': {
                'max_reports_per_month': 5,
                'max_accounts': 2,
                'has_advanced_reports': False,
                'has_ai_insights': False,
                'storage_gb': 1,
            },
            'professional': {
                'max_reports_per_month': 20,
                'max_accounts': 10,
                'has_advanced_reports': True,
                'has_ai_insights': False,
                'storage_gb': 5,
            },
            'premium': {
                'max_reports_per_month': 100,
                'max_accounts': 50,
                'has_advanced_reports': True,
                'has_ai_insights': True,
                'storage_gb': 20,
            },
            'enterprise': {
                'max_reports_per_month': -1,  # Unlimited
                'max_accounts': -1,
                'has_advanced_reports': True,
                'has_ai_insights': True,
                'storage_gb': 100,
            }
        }
        return plan_configs.get(self.plan, plan_configs['starter'])


class BankAccountFactory(factory.django.DjangoModelFactory):
    """Factory for creating BankAccount instances"""
    
    class Meta:
        model = BankAccount
    
    company = factory.SubFactory(CompanyFactory)
    pluggy_account_id = factory.Sequence(lambda n: f"pluggy_account_{n}")
    item = factory.LazyFunction(lambda: factory.create_mock_object())
    type = factory.Iterator(['BANK', 'CREDIT'])
    subtype = factory.Iterator(['CHECKING', 'SAVINGS', 'CREDIT_CARD'])
    name = factory.Iterator([
        'Conta Corrente',
        'Conta Poupança', 
        'Cartão de Crédito',
        'Conta Empresarial'
    ])
    display_name = factory.LazyAttribute(lambda obj: f"{obj.name} - {obj.pluggy_account_id[-4:]}")
    balance = factory.LazyFunction(lambda: Decimal(str(factory.Faker('pydecimal', left_digits=6, right_digits=2, positive=True).generate({}))))
    currency_code = 'BRL'
    masked_number = factory.Sequence(lambda n: f"****{str(n).zfill(4)}")
    institution = factory.Dict({
        'name': factory.Iterator(['Banco do Brasil', 'Itaú', 'Bradesco', 'Santander', 'Caixa']),
        'code': factory.Sequence(lambda n: str(n).zfill(3)),
    })


class CategoryFactory(factory.django.DjangoModelFactory):
    """Factory for creating Category instances"""
    
    class Meta:
        model = Category
    
    name = factory.Iterator([
        'Food & Dining',
        'Transportation',
        'Shopping',
        'Entertainment',
        'Bills & Utilities',
        'Healthcare',
        'Education',
        'Travel',
        'Salary',
        'Investments',
        'Business',
        'Other Income'
    ])
    
    icon = factory.Iterator([
        'utensils',
        'car',
        'shopping-cart',
        'film',
        'zap',
        'heart',
        'book',
        'plane',
        'briefcase',
        'trending-up',
        'building',
        'dollar-sign'
    ])
    
    type = factory.Iterator(['expense', 'income', 'transfer'])
    color = factory.Iterator([
        '#ef4444',  # Red
        '#f97316',  # Orange
        '#eab308',  # Yellow
        '#22c55e',  # Green
        '#06b6d4',  # Cyan
        '#3b82f6',  # Blue
        '#8b5cf6',  # Purple
        '#ec4899',  # Pink
    ])
    
    parent = None  # Can be overridden for subcategories


class TransactionFactory(factory.django.DjangoModelFactory):
    """Factory for creating Transaction instances"""
    
    class Meta:
        model = Transaction
    
    pluggy_transaction_id = factory.Sequence(lambda n: f"txn_{n}")
    account = factory.SubFactory(BankAccountFactory)
    company = factory.LazyAttribute(lambda obj: obj.account.company.id)
    type = factory.Iterator(['DEBIT', 'CREDIT'])
    amount = factory.LazyFunction(
        lambda: Decimal(str(factory.Faker('pydecimal', left_digits=4, right_digits=2, positive=True).generate({})))
    )
    description = factory.Faker('sentence', nb_words=4)
    date = factory.LazyFunction(lambda: factory.Faker('date_between', start_date='-1y', end_date='today').generate({}))
    currency_code = 'BRL'
    category = factory.SubFactory(CategoryFactory)
    
    # Optional merchant information
    merchant = factory.Dict({
        'name': factory.Faker('company'),
        'category': factory.Iterator(['grocery', 'restaurant', 'gas_station', 'retail', 'online']),
    })
    
    # Location data
    location = factory.Dict({
        'city': factory.Faker('city'),
        'state': factory.Faker('state_abbr'),
        'country': 'BR',
    })
    
    @factory.lazy_attribute
    def amount(self):
        """Generate appropriate amount based on transaction type"""
        base_amount = Decimal(str(factory.Faker('pydecimal', left_digits=4, right_digits=2, positive=True).generate({})))
        
        # Adjust amount based on category and type
        if self.category and self.category.type == 'income':
            return base_amount * Decimal('10')  # Income tends to be larger
        elif self.type == 'CREDIT':
            return base_amount
        else:  # DEBIT
            return -abs(base_amount)


class ReportTemplateFactory(factory.django.DjangoModelFactory):
    """Factory for creating ReportTemplate instances"""
    
    class Meta:
        model = ReportTemplate
    
    name = factory.Iterator([
        'Monthly Summary Template',
        'Cash Flow Template',
        'Profit & Loss Template',
        'Category Analysis Template',
        'Executive Summary Template'
    ])
    
    description = factory.LazyAttribute(
        lambda obj: f"Template for generating {obj.name.lower()}"
    )
    
    report_type = factory.Iterator([
        'monthly_summary',
        'cash_flow',
        'profit_loss',
        'category_analysis',
        'quarterly_report'
    ])
    
    is_default = False
    is_public = True
    
    config = factory.Dict({
        'sections': factory.List([
            'executive_summary',
            'income_statement',
            'expense_breakdown',
            'category_analysis',
            'charts_visualizations'
        ]),
        'charts': factory.List([
            factory.Dict({
                'type': 'line',
                'title': 'Monthly Trend',
                'data_key': 'monthly_trends'
            }),
            factory.Dict({
                'type': 'pie',
                'title': 'Category Breakdown',
                'data_key': 'category_breakdown'
            })
        ]),
        'styling': factory.Dict({
            'primary_color': '#1f2937',
            'secondary_color': '#6b7280',
            'font_family': 'Arial, sans-serif',
            'font_size': 12,
            'include_logo': True,
            'include_watermark': False
        }),
        'filters': factory.Dict({
            'exclude_transfers': True,
            'include_pending': False,
            'min_amount_threshold': 0.01
        })
    })
    
    created_by = factory.SubFactory(UserFactory)


class ReportFactory(factory.django.DjangoModelFactory):
    """Factory for creating Report instances"""
    
    class Meta:
        model = Report
    
    company = factory.SubFactory(CompanyFactory)
    report_type = factory.Iterator([
        'monthly_summary',
        'cash_flow',
        'profit_loss',
        'category_analysis',
        'quarterly_report',
        'annual_report',
        'tax_report'
    ])
    
    title = factory.LazyAttribute(
        lambda obj: f"{obj.report_type.replace('_', ' ').title()} - {obj.period_start.strftime('%B %Y')}"
    )
    
    description = factory.LazyAttribute(
        lambda obj: f"Automated {obj.report_type.replace('_', ' ')} report for {obj.period_start.strftime('%B %Y')}"
    )
    
    period_start = factory.LazyFunction(
        lambda: factory.Faker('date_between', start_date='-3m', end_date='-1m').generate({})
    )
    
    period_end = factory.LazyAttribute(
        lambda obj: obj.period_start.replace(day=28) + timedelta(days=4) - timedelta(days=(obj.period_start.replace(day=28) + timedelta(days=4)).day)
    )
    
    file_format = factory.Iterator(['pdf', 'xlsx', 'csv'])
    is_generated = factory.Iterator([True, False])
    
    parameters = factory.Dict({
        'include_charts': True,
        'detailed_breakdown': True,
        'include_comparisons': False,
        'account_ids': factory.List([]),
        'category_ids': factory.List([]),
        'exclude_transfers': True,
        'include_pending': False
    })
    
    filters = factory.Dict({
        'min_amount': 0.01,
        'max_amount': None,
        'transaction_types': factory.List(['DEBIT', 'CREDIT']),
        'date_grouping': 'daily'
    })
    
    metadata = factory.Dict({
        'generation_time_seconds': factory.LazyFunction(lambda: factory.Faker('pyfloat', positive=True, max_value=120).generate({})),
        'total_transactions': factory.LazyFunction(lambda: factory.Faker('pyint', min_value=10, max_value=1000).generate({})),
        'date_range_days': factory.LazyAttribute(lambda obj: (obj.period_end - obj.period_start).days),
        'accounts_included': factory.LazyFunction(lambda: factory.Faker('pyint', min_value=1, max_value=5).generate({})),
        'categories_included': factory.LazyFunction(lambda: factory.Faker('pyint', min_value=3, max_value=15).generate({}))
    })
    
    created_by = factory.SubFactory(UserFactory, company=factory.SelfAttribute('..company'))
    
    @factory.post_generation
    def set_file_data(self, create, extracted, **kwargs):
        """Set file and file_size for generated reports"""
        if not create or not self.is_generated:
            return
        
        # Create mock file content
        if self.file_format == 'pdf':
            content = b'%PDF-1.4 mock pdf content for testing'
            filename = f"{self.title.replace(' ', '_').lower()}.pdf"
        elif self.file_format == 'xlsx':
            content = b'PK mock xlsx content for testing'
            filename = f"{self.title.replace(' ', '_').lower()}.xlsx"
        else:  # csv
            content = b'Header1,Header2,Header3\nValue1,Value2,Value3\n'
            filename = f"{self.title.replace(' ', '_').lower()}.csv"
        
        from django.core.files.base import ContentFile
        self.file.save(filename, ContentFile(content))
        self.file_size = len(content)
        self.save()


class ScheduledReportFactory(factory.django.DjangoModelFactory):
    """Factory for creating ScheduledReport instances"""
    
    class Meta:
        model = ScheduledReport
    
    company = factory.SubFactory(CompanyFactory)
    name = factory.Sequence(lambda n: f"Scheduled Report {n}")
    description = factory.LazyAttribute(
        lambda obj: f"Automated scheduled report: {obj.name}"
    )
    
    report_type = factory.Iterator([
        'daily_summary',
        'weekly_summary', 
        'monthly_summary',
        'quarterly_report',
        'cash_flow'
    ])
    
    frequency = factory.LazyAttribute(
        lambda obj: {
            'daily_summary': 'daily',
            'weekly_summary': 'weekly',
            'monthly_summary': 'monthly',
            'quarterly_report': 'quarterly',
            'cash_flow': 'weekly'
        }.get(obj.report_type, 'monthly')
    )
    
    email_recipients = factory.List([
        factory.Faker('email'),
        factory.Faker('email')
    ])
    
    file_format = factory.Iterator(['pdf', 'xlsx'])
    send_email = True
    is_active = True
    
    parameters = factory.Dict({
        'include_charts': True,
        'detailed_breakdown': factory.Iterator([True, False]),
        'include_comparisons': True,
        'auto_insights': factory.Iterator([True, False])
    })
    
    next_run_at = factory.LazyFunction(
        lambda: timezone.now() + timedelta(
            days=factory.Faker('pyint', min_value=1, max_value=30).generate({})
        )
    )
    
    created_by = factory.SubFactory(UserFactory, company=factory.SelfAttribute('..company'))
    
    @factory.post_generation
    def set_last_run(self, create, extracted, **kwargs):
        """Set last_run_at for some scheduled reports"""
        if not create:
            return
        
        # 70% chance of having run before
        if factory.Faker('pybool', truth_probability=70).generate({}):
            self.last_run_at = timezone.now() - timedelta(
                days=factory.Faker('pyint', min_value=1, max_value=30).generate({})
            )
            self.save()


# Trait classes for creating specific scenarios

class ReportFactory_Generated(ReportFactory):
    """Factory for generated reports with files"""
    is_generated = True
    

class ReportFactory_Failed(ReportFactory):
    """Factory for failed reports with error messages"""
    is_generated = False
    error_message = factory.Iterator([
        'Insufficient data for report generation',
        'Unable to connect to external data source',
        'Report generation timeout',
        'Invalid date range specified',
        'Missing required account information'
    ])


class ReportFactory_Processing(ReportFactory):
    """Factory for reports currently being processed"""
    is_generated = False
    error_message = None
    metadata = factory.Dict({
        'status': 'processing',
        'progress': factory.LazyFunction(lambda: factory.Faker('pyint', min_value=1, max_value=99).generate({})),
        'current_step': factory.Iterator([
            'collecting_data',
            'processing_transactions',
            'generating_charts',
            'creating_document',
            'finalizing'
        ])
    })


class TransactionFactory_Income(TransactionFactory):
    """Factory for income transactions"""
    type = 'CREDIT'
    category = factory.SubFactory(CategoryFactory, type='income')
    amount = factory.LazyFunction(
        lambda: Decimal(str(factory.Faker('pydecimal', left_digits=5, right_digits=2, positive=True).generate({})))
    )


class TransactionFactory_Expense(TransactionFactory):
    """Factory for expense transactions"""
    type = 'DEBIT'
    category = factory.SubFactory(CategoryFactory, type='expense')
    amount = factory.LazyFunction(
        lambda: -abs(Decimal(str(factory.Faker('pydecimal', left_digits=3, right_digits=2, positive=True).generate({}))))
    )


class UserFactory_Admin(UserFactory):
    """Factory for admin users"""
    is_staff = True
    is_superuser = True


class SubscriptionFactory_Premium(SubscriptionFactory):
    """Factory for premium subscriptions"""
    plan = 'premium'
    status = 'active'


class SubscriptionFactory_Expired(SubscriptionFactory):
    """Factory for expired subscriptions"""
    status = 'canceled'
    current_period_end = factory.LazyFunction(lambda: timezone.now() - timedelta(days=1))


# Helper functions for creating test scenarios

def create_test_company_with_data(
    num_accounts=2,
    num_categories=10,
    num_transactions=100,
    num_reports=5
):
    """Create a complete test company with related data"""
    company = CompanyFactory()
    user = UserFactory(company=company)
    subscription = SubscriptionFactory_Premium(company=company)
    
    # Create accounts
    accounts = BankAccountFactory.create_batch(num_accounts, company=company)
    
    # Create categories
    categories = CategoryFactory.create_batch(num_categories)
    
    # Create transactions
    transactions = []
    for account in accounts:
        account_transactions = TransactionFactory.create_batch(
            num_transactions // num_accounts,
            account=account,
            company=company.id,
            category=factory.Iterator(categories)
        )
        transactions.extend(account_transactions)
    
    # Create reports
    reports = ReportFactory.create_batch(
        num_reports,
        company=company,
        created_by=user
    )
    
    return {
        'company': company,
        'user': user,
        'subscription': subscription,
        'accounts': accounts,
        'categories': categories,
        'transactions': transactions,
        'reports': reports
    }


def create_month_of_transactions(company, account, year=2024, month=1):
    """Create a realistic month of transactions for testing"""
    from datetime import date, timedelta
    import random
    
    # Get month date range
    start_date = date(year, month, 1)
    if month == 12:
        end_date = date(year + 1, 1, 1) - timedelta(days=1)
    else:
        end_date = date(year, month + 1, 1) - timedelta(days=1)
    
    transactions = []
    current_date = start_date
    
    while current_date <= end_date:
        # Create 0-5 transactions per day
        num_transactions = random.randint(0, 5)
        
        for _ in range(num_transactions):
            # 70% chance of expense, 30% income
            if random.random() < 0.7:
                transaction = TransactionFactory_Expense(
                    account=account,
                    company=company.id,
                    date=current_date
                )
            else:
                transaction = TransactionFactory_Income(
                    account=account,
                    company=company.id,
                    date=current_date
                )
            transactions.append(transaction)
        
        current_date += timedelta(days=1)
    
    return transactions