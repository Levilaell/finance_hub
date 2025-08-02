"""
Unit tests for banking models
"""
import uuid
from decimal import Decimal
from datetime import datetime, timedelta

from django.test import TestCase
from django.utils import timezone
from django.db import IntegrityError

from apps.banking.models import (
    PluggyConnector,
    PluggyItem,
    BankAccount,
    PluggyCategory,
    Transaction,
    TransactionCategory,
    ItemWebhook
)
from apps.banking.tests.factories.banking_factories import (
    PluggyConnectorFactory,
    PluggyItemFactory,
    BankAccountFactory,
    PluggyCategoryFactory,
    TransactionFactory,
    TransactionCategoryFactory,
    ItemWebhookFactory
)
from apps.companies.tests.factories import CompanyFactory


class PluggyConnectorModelTest(TestCase):
    """Test cases for PluggyConnector model"""
    
    def setUp(self):
        self.connector = PluggyConnectorFactory()
    
    def test_create_connector(self):
        """Test creating a PluggyConnector"""
        self.assertIsNotNone(self.connector.id)
        self.assertIsNotNone(self.connector.pluggy_id)
        self.assertTrue(self.connector.name)
        self.assertEqual(self.connector.country, 'BR')
    
    def test_connector_str_representation(self):
        """Test string representation of connector"""
        expected = f"{self.connector.name} ({self.connector.pluggy_id})"
        self.assertEqual(str(self.connector), expected)
    
    def test_unique_pluggy_id_constraint(self):
        """Test that pluggy_id must be unique"""
        with self.assertRaises(IntegrityError):
            PluggyConnectorFactory(pluggy_id=self.connector.pluggy_id)
    
    def test_connector_products_field(self):
        """Test products JSON field"""
        connector = PluggyConnectorFactory(
            products=['ACCOUNTS', 'TRANSACTIONS', 'INVESTMENTS']
        )
        self.assertEqual(len(connector.products), 3)
        self.assertIn('ACCOUNTS', connector.products)
    
    def test_connector_credentials_schema(self):
        """Test credentials JSON field structure"""
        self.assertIsInstance(self.connector.credentials, list)
        if self.connector.credentials:
            cred = self.connector.credentials[0]
            self.assertIn('name', cred)
            self.assertIn('type', cred)


class PluggyItemModelTest(TestCase):
    """Test cases for PluggyItem model"""
    
    def setUp(self):
        self.company = CompanyFactory()
        self.connector = PluggyConnectorFactory()
        self.item = PluggyItemFactory(
            company=self.company,
            connector=self.connector
        )
    
    def test_create_item(self):
        """Test creating a PluggyItem"""
        self.assertIsNotNone(self.item.id)
        self.assertIsNotNone(self.item.pluggy_item_id)
        self.assertEqual(self.item.company, self.company)
        self.assertEqual(self.item.connector, self.connector)
    
    def test_item_str_representation(self):
        """Test string representation of item"""
        expected = f"{self.connector.name} - {self.item.pluggy_item_id}"
        self.assertEqual(str(self.item), expected)
    
    def test_unique_item_id_constraint(self):
        """Test that pluggy_item_id must be unique"""
        with self.assertRaises(IntegrityError):
            PluggyItemFactory(pluggy_item_id=self.item.pluggy_item_id)
    
    def test_item_status_choices(self):
        """Test item status field choices"""
        valid_statuses = [
            'LOGIN_IN_PROGRESS', 'WAITING_USER_INPUT', 'UPDATING',
            'UPDATED', 'LOGIN_ERROR', 'OUTDATED', 'ERROR',
            'DELETED', 'CONSENT_REVOKED'
        ]
        for status in valid_statuses:
            self.item.status = status
            self.item.save()
            self.assertEqual(self.item.status, status)
    
    def test_item_execution_status_choices(self):
        """Test execution status field choices"""
        valid_statuses = [
            'CREATED', 'SUCCESS', 'PARTIAL_SUCCESS', 'LOGIN_ERROR',
            'INVALID_CREDENTIALS', 'USER_INPUT_TIMEOUT',
            'USER_AUTHORIZATION_PENDING', 'USER_AUTHORIZATION_NOT_GRANTED',
            'SITE_NOT_AVAILABLE', 'ERROR'
        ]
        for status in valid_statuses:
            self.item.execution_status = status
            self.item.save()
            self.assertEqual(self.item.execution_status, status)
    
    def test_item_mfa_parameter(self):
        """Test MFA parameter JSON field"""
        mfa_data = {
            'type': 'numeric',
            'label': 'Enter SMS code',
            'name': 'sms_code'
        }
        self.item.parameter = mfa_data
        self.item.save()
        self.assertEqual(self.item.parameter, mfa_data)
    
    def test_item_cascade_delete(self):
        """Test that deleting company cascades to items"""
        company_id = self.company.id
        item_id = self.item.id
        self.company.delete()
        
        self.assertFalse(
            PluggyItem.objects.filter(id=item_id).exists()
        )


class BankAccountModelTest(TestCase):
    """Test cases for BankAccount model"""
    
    def setUp(self):
        self.company = CompanyFactory()
        self.item = PluggyItemFactory(company=self.company)
        self.account = BankAccountFactory(
            item=self.item,
            company=self.company
        )
    
    def test_create_bank_account(self):
        """Test creating a BankAccount"""
        self.assertIsNotNone(self.account.id)
        self.assertIsNotNone(self.account.pluggy_account_id)
        self.assertEqual(self.account.company, self.company)
        self.assertEqual(self.account.item, self.item)
    
    def test_account_str_representation(self):
        """Test string representation of account"""
        result = str(self.account)
        self.assertIn(self.account.get_type_display(), result)
    
    def test_masked_number_property(self):
        """Test masked account number property"""
        self.account.number = '1234567890'
        self.assertEqual(self.account.masked_number, '****7890')
        
        self.account.number = '123'
        self.assertEqual(self.account.masked_number, '123')
        
        self.account.number = ''
        self.assertEqual(self.account.masked_number, '')
    
    def test_display_name_property(self):
        """Test display name property priority"""
        # Test with name
        self.account.name = 'My Checking Account'
        self.account.marketing_name = 'Premium Account'
        self.assertEqual(self.account.display_name, 'My Checking Account')
        
        # Test with only marketing name
        self.account.name = ''
        self.assertEqual(self.account.display_name, 'Premium Account')
        
        # Test with neither
        self.account.marketing_name = ''
        self.account.number = '1234567890'
        display = self.account.display_name
        self.assertIn(self.account.item.connector.name, display)
        self.assertIn('****7890', display)
    
    def test_account_type_choices(self):
        """Test account type field choices"""
        valid_types = ['BANK', 'CREDIT', 'INVESTMENT', 'LOAN', 'OTHER']
        for acc_type in valid_types:
            self.account.type = acc_type
            self.account.save()
            self.assertEqual(self.account.type, acc_type)
    
    def test_balance_decimal_field(self):
        """Test balance field with decimal values"""
        self.account.balance = Decimal('1234.56')
        self.account.save()
        self.assertEqual(self.account.balance, Decimal('1234.56'))
    
    def test_unique_together_constraint(self):
        """Test unique together constraint for company and pluggy_account_id"""
        with self.assertRaises(IntegrityError):
            BankAccountFactory(
                company=self.company,
                pluggy_account_id=self.account.pluggy_account_id
            )
    
    def test_account_cascade_delete(self):
        """Test that deleting item cascades to accounts"""
        account_id = self.account.id
        self.item.delete()
        
        self.assertFalse(
            BankAccount.objects.filter(id=account_id).exists()
        )


class TransactionCategoryModelTest(TestCase):
    """Test cases for TransactionCategory model"""
    
    def setUp(self):
        self.company = CompanyFactory()
        self.category = TransactionCategoryFactory(company=self.company)
    
    def test_create_category(self):
        """Test creating a TransactionCategory"""
        self.assertIsNotNone(self.category.id)
        self.assertTrue(self.category.name)
        self.assertTrue(self.category.slug)
        self.assertEqual(self.category.company, self.company)
    
    def test_category_str_representation(self):
        """Test string representation of category"""
        self.assertEqual(str(self.category), self.category.name)
        
        # Test with parent
        subcategory = TransactionCategoryFactory(
            parent=self.category,
            company=self.company
        )
        expected = f"{self.category.name} > {subcategory.name}"
        self.assertEqual(str(subcategory), expected)
    
    def test_auto_slug_generation(self):
        """Test automatic slug generation"""
        category = TransactionCategory(
            name='Test Category',
            type='expense',
            company=self.company
        )
        category.save()
        self.assertEqual(category.slug, 'test-category')
    
    def test_unique_slug_per_company(self):
        """Test slug uniqueness per company"""
        # Same slug for different companies should work
        other_company = CompanyFactory()
        category2 = TransactionCategoryFactory(
            slug=self.category.slug,
            company=other_company
        )
        self.assertEqual(category2.slug, self.category.slug)
        
        # Same slug for same company should fail
        with self.assertRaises(IntegrityError):
            TransactionCategoryFactory(
                slug=self.category.slug,
                company=self.company
            )
    
    def test_category_hierarchy(self):
        """Test category parent-child relationship"""
        parent = TransactionCategoryFactory(company=self.company)
        child1 = TransactionCategoryFactory(
            parent=parent,
            company=self.company
        )
        child2 = TransactionCategoryFactory(
            parent=parent,
            company=self.company
        )
        
        self.assertEqual(parent.subcategories.count(), 2)
        self.assertIn(child1, parent.subcategories.all())
        self.assertIn(child2, parent.subcategories.all())


class TransactionModelTest(TestCase):
    """Test cases for Transaction model"""
    
    def setUp(self):
        self.company = CompanyFactory()
        self.account = BankAccountFactory(company=self.company)
        self.category = TransactionCategoryFactory(company=self.company)
        self.transaction = TransactionFactory(
            account=self.account,
            company=self.company,
            category=self.category
        )
    
    def test_create_transaction(self):
        """Test creating a Transaction"""
        self.assertIsNotNone(self.transaction.id)
        self.assertIsNotNone(self.transaction.pluggy_transaction_id)
        self.assertEqual(self.transaction.company, self.company)
        self.assertEqual(self.transaction.account, self.account)
    
    def test_transaction_str_representation(self):
        """Test string representation of transaction"""
        result = str(self.transaction)
        self.assertIn(self.transaction.description, result)
        self.assertIn(str(abs(self.transaction.amount)), result)
    
    def test_get_amount_display(self):
        """Test formatted amount display"""
        # Test debit
        self.transaction.type = 'DEBIT'
        self.transaction.amount = Decimal('100.50')
        self.transaction.currency_code = 'BRL'
        self.assertEqual(
            self.transaction.get_amount_display(),
            '-BRL 100.50'
        )
        
        # Test credit
        self.transaction.type = 'CREDIT'
        self.assertEqual(
            self.transaction.get_amount_display(),
            '+BRL 100.50'
        )
    
    def test_is_income_property(self):
        """Test is_income property"""
        self.transaction.type = 'CREDIT'
        self.assertTrue(self.transaction.is_income)
        self.assertFalse(self.transaction.is_expense)
        
        self.transaction.type = 'DEBIT'
        self.assertFalse(self.transaction.is_income)
        self.assertTrue(self.transaction.is_expense)
    
    def test_unique_transaction_id_constraint(self):
        """Test that pluggy_transaction_id must be unique"""
        with self.assertRaises(IntegrityError):
            TransactionFactory(
                pluggy_transaction_id=self.transaction.pluggy_transaction_id
            )
    
    def test_soft_delete_functionality(self):
        """Test soft delete functionality"""
        self.assertFalse(self.transaction.is_deleted)
        self.assertIsNone(self.transaction.deleted_at)
        
        # Soft delete
        self.transaction.is_deleted = True
        self.transaction.deleted_at = timezone.now()
        self.transaction.save()
        
        # Should still exist in database
        self.assertTrue(
            Transaction.objects.filter(id=self.transaction.id).exists()
        )
        
        # But not in active manager
        self.assertFalse(
            Transaction.active.filter(id=self.transaction.id).exists()
        )
    
    def test_transaction_metadata_fields(self):
        """Test JSON metadata fields"""
        merchant_data = {
            'name': 'Store ABC',
            'category': 'Shopping',
            'location': 'São Paulo'
        }
        self.transaction.merchant = merchant_data
        self.transaction.save()
        self.assertEqual(self.transaction.merchant, merchant_data)
        
        tags = ['groceries', 'essential']
        self.transaction.tags = tags
        self.transaction.save()
        self.assertEqual(self.transaction.tags, tags)
    
    def test_transaction_cascade_delete(self):
        """Test that deleting account cascades to transactions"""
        transaction_id = self.transaction.id
        self.account.delete()
        
        self.assertFalse(
            Transaction.objects.filter(id=transaction_id).exists()
        )


class ItemWebhookModelTest(TestCase):
    """Test cases for ItemWebhook model"""
    
    def setUp(self):
        self.item = PluggyItemFactory()
        self.webhook = ItemWebhookFactory(item=self.item)
    
    def test_create_webhook(self):
        """Test creating an ItemWebhook"""
        self.assertIsNotNone(self.webhook.id)
        self.assertEqual(self.webhook.item, self.item)
        self.assertTrue(self.webhook.event_id)
    
    def test_webhook_str_representation(self):
        """Test string representation of webhook"""
        result = str(self.webhook)
        self.assertIn(self.webhook.event_type, result)
        self.assertIn(str(self.item), result)
    
    def test_webhook_event_types(self):
        """Test various webhook event types"""
        event_types = [
            'item.created', 'item.updated', 'item.error',
            'transactions.created', 'transactions.updated'
        ]
        
        for event_type in event_types:
            webhook = ItemWebhookFactory(
                item=self.item,
                event_type=event_type
            )
            self.assertEqual(webhook.event_type, event_type)
    
    def test_webhook_status_tracking(self):
        """Test webhook status tracking"""
        # Test success
        self.webhook.status = 'SUCCESS'
        self.webhook.save()
        self.assertEqual(self.webhook.status, 'SUCCESS')
        
        # Test failure
        self.webhook.status = 'FAILED'
        self.webhook.error_message = 'Connection timeout'
        self.webhook.attempts = 3
        self.webhook.save()
        self.assertEqual(self.webhook.status, 'FAILED')
        self.assertEqual(self.webhook.error_message, 'Connection timeout')
        self.assertEqual(self.webhook.attempts, 3)