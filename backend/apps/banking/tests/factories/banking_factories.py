"""
Test factories for banking models
"""
import uuid
from decimal import Decimal
from datetime import datetime, timedelta

import factory
from factory import fuzzy
from django.utils import timezone

from apps.banking.models import (
    PluggyConnector,
    PluggyItem,
    BankAccount,
    PluggyCategory,
    Transaction,
    TransactionCategory,
    ItemWebhook
)
from apps.companies.tests.factories import CompanyFactory


class PluggyConnectorFactory(factory.django.DjangoModelFactory):
    """Factory for PluggyConnector model"""
    
    class Meta:
        model = PluggyConnector
        django_get_or_create = ('pluggy_id',)
    
    pluggy_id = factory.Sequence(lambda n: n + 1000)
    name = factory.Faker('company')
    institution_url = factory.Faker('url')
    image_url = factory.Faker('image_url')
    primary_color = factory.Faker('hex_color')
    type = fuzzy.FuzzyChoice(['PERSONAL_BANK', 'BUSINESS_BANK', 'INVESTMENT'])
    country = 'BR'
    has_mfa = factory.Faker('boolean')
    has_oauth = factory.Faker('boolean')
    is_open_finance = factory.Faker('boolean')
    is_sandbox = False
    products = factory.LazyFunction(lambda: ['ACCOUNTS', 'TRANSACTIONS'])
    credentials = factory.LazyFunction(lambda: [
        {
            'name': 'username',
            'type': 'text',
            'label': 'Username',
            'validation': 'required'
        },
        {
            'name': 'password',
            'type': 'password',
            'label': 'Password',
            'validation': 'required'
        }
    ])


class PluggyItemFactory(factory.django.DjangoModelFactory):
    """Factory for PluggyItem model"""
    
    class Meta:
        model = PluggyItem
    
    pluggy_item_id = factory.LazyFunction(lambda: str(uuid.uuid4()))
    company = factory.SubFactory(CompanyFactory)
    connector = factory.SubFactory(PluggyConnectorFactory)
    client_user_id = factory.Faker('uuid4')
    webhook_url = factory.Faker('url')
    next_auto_sync_at = factory.LazyFunction(
        lambda: timezone.now() + timedelta(hours=6)
    )
    products = factory.LazyFunction(lambda: ['ACCOUNTS', 'TRANSACTIONS'])
    parameter = factory.Dict({})
    status = 'UPDATED'
    execution_status = 'SUCCESS'
    pluggy_created_at = factory.LazyFunction(lambda: timezone.now())
    pluggy_updated_at = factory.LazyFunction(lambda: timezone.now())
    last_successful_update = factory.LazyFunction(lambda: timezone.now())
    error_code = ''
    error_message = ''
    status_detail = factory.Dict({})
    consent_id = ''
    consent_expires_at = None
    metadata = factory.Dict({})


class BankAccountFactory(factory.django.DjangoModelFactory):
    """Factory for BankAccount model"""
    
    class Meta:
        model = BankAccount
    
    pluggy_account_id = factory.LazyFunction(lambda: str(uuid.uuid4()))
    item = factory.SubFactory(PluggyItemFactory)
    company = factory.LazyAttribute(lambda obj: obj.item.company)
    type = fuzzy.FuzzyChoice(['BANK', 'CREDIT', 'INVESTMENT'])
    subtype = fuzzy.FuzzyChoice(['CHECKING_ACCOUNT', 'SAVINGS_ACCOUNT', 'CREDIT_CARD'])
    number = factory.Faker('bban')
    name = factory.Faker('catch_phrase')
    marketing_name = factory.Faker('bs')
    owner = factory.Faker('name')
    tax_number = factory.Faker('ssn')
    balance = fuzzy.FuzzyDecimal(0, 10000, 2)
    balance_in_account_currency = factory.LazyAttribute(lambda obj: obj.balance)
    balance_date = factory.LazyFunction(lambda: timezone.now())
    currency_code = 'BRL'
    investment_status = ''
    bank_data = factory.Dict({})
    credit_data = factory.Dict({})
    is_active = True
    pluggy_created_at = factory.LazyFunction(lambda: timezone.now())
    pluggy_updated_at = factory.LazyFunction(lambda: timezone.now())


class TransactionCategoryFactory(factory.django.DjangoModelFactory):
    """Factory for TransactionCategory model"""
    
    class Meta:
        model = TransactionCategory
    
    name = factory.Sequence(lambda n: f"Category {n}")
    slug = factory.LazyAttribute(lambda obj: obj.name.lower().replace(' ', '-'))
    type = fuzzy.FuzzyChoice(['income', 'expense', 'transfer'])
    parent = None
    icon = '📁'
    color = factory.Faker('hex_color')
    is_system = False
    is_active = True
    order = factory.Sequence(lambda n: n)
    company = factory.SubFactory(CompanyFactory)


class PluggyCategoryFactory(factory.django.DjangoModelFactory):
    """Factory for PluggyCategory model"""
    
    class Meta:
        model = PluggyCategory
    
    id = factory.Faker('uuid4')
    description = factory.Faker('word')
    parent_id = None
    parent_description = ''
    internal_category = factory.SubFactory(TransactionCategoryFactory)


class TransactionFactory(factory.django.DjangoModelFactory):
    """Factory for Transaction model"""
    
    class Meta:
        model = Transaction
    
    pluggy_transaction_id = factory.LazyFunction(lambda: str(uuid.uuid4()))
    account = factory.SubFactory(BankAccountFactory)
    company = factory.LazyAttribute(lambda obj: obj.account.company)
    type = fuzzy.FuzzyChoice(['DEBIT', 'CREDIT'])
    status = 'POSTED'
    description = factory.Faker('sentence', nb_words=4)
    description_raw = factory.LazyAttribute(lambda obj: obj.description)
    amount = fuzzy.FuzzyDecimal(1, 1000, 2)
    amount_in_account_currency = factory.LazyAttribute(lambda obj: obj.amount)
    balance = fuzzy.FuzzyDecimal(0, 10000, 2)
    currency_code = 'BRL'
    date = fuzzy.FuzzyDateTime(
        start_dt=timezone.now() - timedelta(days=30),
        end_dt=timezone.now()
    )
    provider_code = factory.Faker('uuid4')
    provider_id = factory.Faker('uuid4')
    merchant = factory.Dict({})
    payment_data = factory.Dict({})
    pluggy_category_id = factory.Faker('uuid4')
    pluggy_category_description = factory.Faker('word')
    category = factory.SubFactory(TransactionCategoryFactory)
    operation_type = ''
    payment_method = ''
    credit_card_metadata = factory.Dict({})
    notes = ''
    tags = factory.List([])
    metadata = factory.Dict({})
    pluggy_created_at = factory.LazyFunction(lambda: timezone.now())
    pluggy_updated_at = factory.LazyFunction(lambda: timezone.now())
    is_deleted = False
    deleted_at = None


class ItemWebhookFactory(factory.django.DjangoModelFactory):
    """Factory for ItemWebhook model"""
    
    class Meta:
        model = ItemWebhook
    
    item = factory.SubFactory(PluggyItemFactory)
    event_type = fuzzy.FuzzyChoice([
        'item.created', 'item.updated', 'item.error',
        'transactions.created', 'transactions.updated'
    ])
    event_id = factory.Faker('uuid4')
    payload = factory.Dict({})
    processed = False
    processed_at = None
    triggered_by = fuzzy.FuzzyChoice(['USER', 'CLIENT', 'SYNC', 'INTERNAL'])
    error = ''