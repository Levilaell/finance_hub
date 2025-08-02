"""
Unit tests for banking serializers
"""
from decimal import Decimal
from datetime import date, timedelta

from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIRequestFactory
from rest_framework.exceptions import ValidationError

from apps.banking.serializers import (
    PluggyConnectorSerializer,
    PluggyItemSerializer,
    BankAccountSerializer,
    TransactionCategorySerializer,
    TransactionSerializer,
    PluggyConnectTokenSerializer,
    PluggyCallbackSerializer,
    AccountSyncSerializer,
    BulkCategorizeSerializer,
    TransactionFilterSerializer
)
from apps.banking.tests.factories.banking_factories import (
    PluggyConnectorFactory,
    PluggyItemFactory,
    BankAccountFactory,
    TransactionCategoryFactory,
    TransactionFactory
)
from apps.companies.tests.factories import CompanyFactory, UserFactory


class PluggyConnectorSerializerTest(TestCase):
    """Test cases for PluggyConnectorSerializer"""
    
    def setUp(self):
        self.connector = PluggyConnectorFactory()
        self.serializer = PluggyConnectorSerializer(instance=self.connector)
    
    def test_contains_expected_fields(self):
        """Test serializer contains all expected fields"""
        data = self.serializer.data
        expected_fields = {
            'pluggy_id', 'name', 'institution_url', 'image_url',
            'primary_color', 'type', 'country', 'has_mfa',
            'has_oauth', 'is_open_finance', 'is_sandbox',
            'products', 'credentials'
        }
        self.assertEqual(set(data.keys()), expected_fields)
    
    def test_pluggy_id_read_only(self):
        """Test that pluggy_id is read-only"""
        data = {'pluggy_id': 9999, 'name': 'Test Bank'}
        serializer = PluggyConnectorSerializer(data=data)
        self.assertFalse(serializer.is_valid())
    
    def test_serializes_json_fields(self):
        """Test JSON fields are properly serialized"""
        data = self.serializer.data
        self.assertIsInstance(data['products'], list)
        self.assertIsInstance(data['credentials'], list)


class PluggyItemSerializerTest(TestCase):
    """Test cases for PluggyItemSerializer"""
    
    def setUp(self):
        self.company = CompanyFactory()
        self.item = PluggyItemFactory(company=self.company)
        # Create some accounts
        BankAccountFactory.create_batch(3, item=self.item, company=self.company)
        self.serializer = PluggyItemSerializer(instance=self.item)
    
    def test_contains_expected_fields(self):
        """Test serializer contains all expected fields"""
        data = self.serializer.data
        expected_fields = {
            'id', 'pluggy_item_id', 'connector', 'status', 'execution_status',
            'pluggy_created_at', 'pluggy_updated_at', 'last_successful_update',
            'error_code', 'error_message', 'status_detail',
            'consent_expires_at', 'accounts_count'
        }
        self.assertEqual(set(data.keys()), expected_fields)
    
    def test_connector_nested_serialization(self):
        """Test connector is properly nested"""
        data = self.serializer.data
        self.assertIsInstance(data['connector'], dict)
        self.assertIn('name', data['connector'])
        self.assertIn('pluggy_id', data['connector'])
    
    def test_accounts_count(self):
        """Test accounts_count field"""
        data = self.serializer.data
        self.assertEqual(data['accounts_count'], 3)


class BankAccountSerializerTest(TestCase):
    """Test cases for BankAccountSerializer"""
    
    def setUp(self):
        self.company = CompanyFactory()
        self.account = BankAccountFactory(
            company=self.company,
            number='1234567890',
            name='Test Account'
        )
        self.serializer = BankAccountSerializer(instance=self.account)
    
    def test_contains_expected_fields(self):
        """Test serializer contains all expected fields"""
        data = self.serializer.data
        self.assertIn('id', data)
        self.assertIn('item_id', data)
        self.assertIn('type', data)
        self.assertIn('balance', data)
        self.assertIn('display_name', data)
        self.assertIn('masked_number', data)
        self.assertIn('connector', data)
    
    def test_get_connector_method(self):
        """Test get_connector method returns correct data"""
        data = self.serializer.data
        connector_data = data['connector']
        
        self.assertEqual(connector_data['id'], self.account.item.connector.pluggy_id)
        self.assertEqual(connector_data['name'], self.account.item.connector.name)
        self.assertIn('image_url', connector_data)
        self.assertIn('primary_color', connector_data)
        self.assertIn('is_open_finance', connector_data)
    
    def test_get_item_method(self):
        """Test get_item method returns minimal item info"""
        data = self.serializer.data
        item_data = data['item']
        
        self.assertEqual(item_data['id'], str(self.account.item.id))
        self.assertEqual(item_data['pluggy_item_id'], self.account.item.pluggy_item_id)
        self.assertEqual(item_data['status'], self.account.item.status)
    
    def test_masked_number_field(self):
        """Test masked_number is properly included"""
        data = self.serializer.data
        self.assertEqual(data['masked_number'], '****7890')


class TransactionCategorySerializerTest(TestCase):
    """Test cases for TransactionCategorySerializer"""
    
    def setUp(self):
        self.company = CompanyFactory()
        self.parent_category = TransactionCategoryFactory(
            name='Parent',
            company=self.company
        )
        self.category = TransactionCategoryFactory(
            name='Child',
            parent=self.parent_category,
            company=self.company
        )
        self.serializer = TransactionCategorySerializer(instance=self.category)
    
    def test_contains_expected_fields(self):
        """Test serializer contains all expected fields"""
        data = self.serializer.data
        expected_fields = {
            'id', 'name', 'slug', 'type', 'parent', 'icon', 'color',
            'is_system', 'is_active', 'order', 'full_name'
        }
        self.assertEqual(set(data.keys()), expected_fields)
    
    def test_get_full_name_with_parent(self):
        """Test full_name includes parent category"""
        data = self.serializer.data
        self.assertEqual(data['full_name'], 'Parent > Child')
    
    def test_get_full_name_without_parent(self):
        """Test full_name without parent"""
        serializer = TransactionCategorySerializer(instance=self.parent_category)
        data = serializer.data
        self.assertEqual(data['full_name'], 'Parent')


class TransactionSerializerTest(TestCase):
    """Test cases for TransactionSerializer"""
    
    def setUp(self):
        self.company = CompanyFactory()
        self.account = BankAccountFactory(company=self.company)
        self.category = TransactionCategoryFactory(company=self.company)
        self.transaction = TransactionFactory(
            account=self.account,
            company=self.company,
            category=self.category,
            type='DEBIT',
            amount=Decimal('100.00')
        )
        self.serializer = TransactionSerializer(instance=self.transaction)
    
    def test_contains_expected_fields(self):
        """Test serializer contains all expected fields"""
        data = self.serializer.data
        self.assertIn('id', data)
        self.assertIn('type', data)
        self.assertIn('amount', data)
        self.assertIn('description', data)
        self.assertIn('category_detail', data)
        self.assertIn('account_info', data)
        self.assertIn('amount_display', data)
        self.assertIn('is_income', data)
        self.assertIn('is_expense', data)
    
    def test_get_account_info(self):
        """Test account_info method field"""
        data = self.serializer.data
        account_info = data['account_info']
        
        self.assertEqual(account_info['id'], str(self.account.id))
        self.assertEqual(account_info['name'], self.account.display_name)
        self.assertEqual(account_info['type'], self.account.type)
    
    def test_category_detail_nested(self):
        """Test category is properly nested"""
        data = self.serializer.data
        self.assertIsInstance(data['category_detail'], dict)
        self.assertEqual(data['category_detail']['name'], self.category.name)
    
    def test_amount_display_format(self):
        """Test amount_display formatting"""
        data = self.serializer.data
        self.assertIn('-BRL 100.00', data['amount_display'])


class PluggyConnectTokenSerializerTest(TestCase):
    """Test cases for PluggyConnectTokenSerializer"""
    
    def test_valid_data(self):
        """Test serializer with valid data"""
        data = {
            'item_id': 'test-item-id',
            'client_user_id': 'user-123',
            'webhook_url': 'https://example.com/webhook',
            'country_codes': ['BR', 'US'],
            'connector_types': ['PERSONAL_BANK']
        }
        serializer = PluggyConnectTokenSerializer(data=data)
        self.assertTrue(serializer.is_valid())
    
    def test_validate_updating_requires_item_id(self):
        """Test validation when updating requires item_id"""
        data = {'client_user_id': 'user-123'}
        serializer = PluggyConnectTokenSerializer(
            data=data,
            context={'updating': True}
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn('item_id', serializer.errors)
    
    def test_list_fields_validation(self):
        """Test list field validations"""
        data = {
            'country_codes': ['BR', 'INVALID'],  # Invalid country code (too long)
            'connector_ids': [1, 'not-a-number']  # Invalid ID type
        }
        serializer = PluggyConnectTokenSerializer(data=data)
        self.assertFalse(serializer.is_valid())


class TransactionFilterSerializerTest(TestCase):
    """Test cases for TransactionFilterSerializer"""
    
    def test_valid_filters(self):
        """Test serializer with valid filter data"""
        data = {
            'start_date': date.today() - timedelta(days=30),
            'end_date': date.today(),
            'min_amount': '100.00',
            'max_amount': '1000.00',
            'type': 'DEBIT',
            'search': 'coffee'
        }
        serializer = TransactionFilterSerializer(data=data)
        self.assertTrue(serializer.is_valid())
    
    def test_invalid_date_range(self):
        """Test validation fails for invalid date range"""
        data = {
            'start_date': date.today(),
            'end_date': date.today() - timedelta(days=30)
        }
        serializer = TransactionFilterSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('end_date', serializer.errors)
    
    def test_invalid_amount_range(self):
        """Test validation fails for invalid amount range"""
        data = {
            'min_amount': '1000.00',
            'max_amount': '100.00'
        }
        serializer = TransactionFilterSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('max_amount', serializer.errors)
    
    def test_invalid_type_choice(self):
        """Test validation fails for invalid type"""
        data = {'type': 'INVALID'}
        serializer = TransactionFilterSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('type', serializer.errors)


class BulkCategorizeSerializerTest(TestCase):
    """Test cases for BulkCategorizeSerializer"""
    
    def setUp(self):
        self.user = UserFactory()
        self.company = CompanyFactory()
        self.user.company = self.company
        self.user.save()
        
        self.category = TransactionCategoryFactory(company=self.company)
        self.request_factory = APIRequestFactory()
    
    def test_valid_data(self):
        """Test serializer with valid data"""
        data = {
            'transaction_ids': [
                'f47ac10b-58cc-4372-a567-0e02b2c3d479',
                'f47ac10b-58cc-4372-a567-0e02b2c3d480'
            ],
            'category_id': str(self.category.id)
        }
        request = self.request_factory.post('/')
        request.user = self.user
        
        serializer = BulkCategorizeSerializer(data=data, context={'request': request})
        self.assertTrue(serializer.is_valid())
    
    def test_empty_transaction_ids(self):
        """Test validation fails for empty transaction list"""
        data = {
            'transaction_ids': [],
            'category_id': str(self.category.id)
        }
        serializer = BulkCategorizeSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('transaction_ids', serializer.errors)
    
    def test_invalid_category_id(self):
        """Test validation fails for non-existent category"""
        data = {
            'transaction_ids': ['f47ac10b-58cc-4372-a567-0e02b2c3d479'],
            'category_id': 'f47ac10b-58cc-4372-a567-0e02b2c3d499'
        }
        request = self.request_factory.post('/')
        request.user = self.user
        
        serializer = BulkCategorizeSerializer(data=data, context={'request': request})
        self.assertFalse(serializer.is_valid())
        self.assertIn('category_id', serializer.errors)