"""
Tests for Pluggy webhook handling
"""
import json
import hmac
import hashlib
from unittest.mock import patch, MagicMock
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from django.conf import settings
from rest_framework import status

from apps.authentication.models import User
from apps.companies.models import Company
from apps.banking.models import PluggyItem, BankAccount, ItemWebhook, Transaction
from apps.banking.tasks import process_webhook_event, sync_bank_account


class PluggyWebhookTestCase(TestCase):
    """
    Test cases for Pluggy webhook endpoint
    """
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        self.webhook_url = reverse('pluggy-webhook')
        
        # Create test company and user
        self.company = Company.objects.create(
            name='Test Company',
            document_number='12345678901234'
        )
        
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            company=self.company
        )
        
        # Create test item
        self.item = PluggyItem.objects.create(
            company=self.company,
            pluggy_item_id='test-item-123',
            connector_id=1,
            status='UPDATED'
        )
        
        # Create test account
        self.account = BankAccount.objects.create(
            item=self.item,
            company=self.company,
            pluggy_account_id='test-account-456',
            name='Test Account',
            type='BANK',
            sub_type='CHECKING_ACCOUNT',
            number='12345',
            balance=1000.00
        )
        
        # Set webhook secret for testing
        self.webhook_secret = 'test-webhook-secret'
        settings.PLUGGY_WEBHOOK_SECRET = self.webhook_secret
    
    def generate_signature(self, payload):
        """Generate webhook signature"""
        return hmac.new(
            self.webhook_secret.encode('utf-8'),
            payload.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
    
    def test_webhook_valid_signature(self):
        """Test webhook with valid signature"""
        event_data = {
            'event': 'item.updated',
            'eventId': 'evt-123',
            'itemId': self.item.pluggy_item_id,
            'clientId': 'client-123',
            'triggeredBy': 'SYNC'
        }
        
        payload = json.dumps(event_data)
        signature = self.generate_signature(payload)
        
        response = self.client.post(
            self.webhook_url,
            data=payload,
            content_type='application/json',
            HTTP_X_PLUGGY_SIGNATURE=signature
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['status'], 'accepted')
        
        # Check webhook was stored
        webhook = ItemWebhook.objects.filter(event_id='evt-123').first()
        self.assertIsNotNone(webhook)
        self.assertEqual(webhook.event_type, 'item.updated')
        self.assertEqual(webhook.triggered_by, 'SYNC')
    
    def test_webhook_invalid_signature(self):
        """Test webhook with invalid signature"""
        event_data = {
            'event': 'item.updated',
            'eventId': 'evt-124',
            'itemId': self.item.pluggy_item_id
        }
        
        payload = json.dumps(event_data)
        
        response = self.client.post(
            self.webhook_url,
            data=payload,
            content_type='application/json',
            HTTP_X_PLUGGY_SIGNATURE='invalid-signature'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_webhook_no_signature_when_not_configured(self):
        """Test webhook without signature when not configured"""
        # Remove webhook secret
        delattr(settings, 'PLUGGY_WEBHOOK_SECRET')
        
        event_data = {
            'event': 'item.updated',
            'eventId': 'evt-125',
            'itemId': self.item.pluggy_item_id
        }
        
        payload = json.dumps(event_data)
        
        response = self.client.post(
            self.webhook_url,
            data=payload,
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_webhook_invalid_json(self):
        """Test webhook with invalid JSON"""
        response = self.client.post(
            self.webhook_url,
            data='invalid-json',
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    @patch('apps.banking.tasks.process_webhook_event.delay')
    def test_webhook_async_processing(self, mock_task):
        """Test webhook triggers async processing"""
        event_data = {
            'event': 'item.updated',
            'eventId': 'evt-126',
            'itemId': self.item.pluggy_item_id
        }
        
        payload = json.dumps(event_data)
        signature = self.generate_signature(payload)
        
        response = self.client.post(
            self.webhook_url,
            data=payload,
            content_type='application/json',
            HTTP_X_PLUGGY_SIGNATURE=signature
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        mock_task.assert_called_once_with('item.updated', event_data)


class WebhookProcessingTestCase(TestCase):
    """
    Test cases for webhook event processing
    """
    
    def setUp(self):
        """Set up test data"""
        # Create test company
        self.company = Company.objects.create(
            name='Test Company',
            document_number='12345678901234'
        )
        
        # Create test item
        self.item = PluggyItem.objects.create(
            company=self.company,
            pluggy_item_id='test-item-123',
            connector_id=1,
            status='UPDATING'
        )
        
        # Create test account
        self.account = BankAccount.objects.create(
            item=self.item,
            company=self.company,
            pluggy_account_id='test-account-456',
            name='Test Account',
            type='BANK',
            sub_type='CHECKING_ACCOUNT',
            number='12345',
            balance=1000.00
        )
    
    @patch('apps.banking.integrations.pluggy.client.PluggyClient.get_item')
    @patch('apps.banking.tasks.sync_bank_account.delay')
    def test_item_updated_event(self, mock_sync, mock_get_item):
        """Test processing item.updated event"""
        # Mock Pluggy API response
        mock_get_item.return_value = {
            'id': self.item.pluggy_item_id,
            'status': 'UPDATED',
            'executionStatus': 'SUCCESS',
            'updatedAt': '2024-01-01T12:00:00Z'
        }
        
        event_data = {
            'event': 'item.updated',
            'eventId': 'evt-200',
            'id': self.item.pluggy_item_id,
            'status': 'UPDATED'
        }
        
        # Process event synchronously for testing
        from apps.banking.tasks import _handle_item_updated
        _handle_item_updated(event_data)
        
        # Check item was updated
        self.item.refresh_from_db()
        self.assertEqual(self.item.status, 'UPDATED')
        self.assertEqual(self.item.execution_status, 'SUCCESS')
        
        # Check sync was triggered
        mock_sync.assert_called_once_with(str(self.item.id))
    
    @patch('apps.banking.integrations.pluggy.client.PluggyClient.get_item')
    def test_item_error_event(self, mock_get_item):
        """Test processing item.error event"""
        # Mock Pluggy API response
        mock_get_item.return_value = {
            'id': self.item.pluggy_item_id,
            'status': 'ERROR',
            'error': {
                'code': 'INVALID_CREDENTIALS',
                'message': 'Invalid credentials provided'
            },
            'executionStatus': 'ERROR',
            'updatedAt': '2024-01-01T12:00:00Z'
        }
        
        event_data = {
            'event': 'item.error',
            'eventId': 'evt-201',
            'id': self.item.pluggy_item_id,
            'error': {
                'code': 'INVALID_CREDENTIALS',
                'message': 'Invalid credentials provided'
            }
        }
        
        # Process event
        from apps.banking.tasks import _handle_item_error
        _handle_item_error(event_data)
        
        # Check item was updated with error
        self.item.refresh_from_db()
        self.assertEqual(self.item.status, 'ERROR')
        self.assertEqual(self.item.error_code, 'INVALID_CREDENTIALS')
        self.assertEqual(self.item.error_message, 'Invalid credentials provided')
    
    def test_item_deleted_event(self):
        """Test processing item.deleted event"""
        event_data = {
            'event': 'item.deleted',
            'eventId': 'evt-202',
            'id': self.item.pluggy_item_id
        }
        
        # Process event
        from apps.banking.tasks import _handle_item_deleted
        _handle_item_deleted(event_data)
        
        # Check item and accounts were updated
        self.item.refresh_from_db()
        self.assertEqual(self.item.status, 'DELETED')
        
        self.account.refresh_from_db()
        self.assertFalse(self.account.is_active)
    
    @patch('apps.banking.integrations.pluggy.client.PluggyClient.get_item')
    def test_item_waiting_input_event(self, mock_get_item):
        """Test processing item.waiting_user_input event"""
        # Mock Pluggy API response
        mock_get_item.return_value = {
            'id': self.item.pluggy_item_id,
            'status': 'WAITING_USER_INPUT',
            'executionStatus': 'WAITING_USER_INPUT',
            'parameter': {
                'type': 'token',
                'label': 'SMS Token',
                'validation': '^[0-9]{6}$'
            }
        }
        
        event_data = {
            'event': 'item.waiting_user_input',
            'eventId': 'evt-203',
            'id': self.item.pluggy_item_id
        }
        
        # Process event
        from apps.banking.tasks import _handle_item_waiting_input
        _handle_item_waiting_input(event_data)
        
        # Check item was updated
        self.item.refresh_from_db()
        self.assertEqual(self.item.status, 'WAITING_USER_INPUT')
        self.assertIsNotNone(self.item.parameter)
        self.assertEqual(self.item.parameter.get('type'), 'token')
    
    def test_transactions_deleted_event(self):
        """Test processing transactions.deleted event"""
        # Create test transactions
        trans1 = Transaction.objects.create(
            pluggy_transaction_id='trans-1',
            account=self.account,
            company=self.company,
            type='DEBIT',
            amount=100.00,
            description='Test Transaction 1',
            date=timezone.now(),
            pluggy_created_at=timezone.now(),
            pluggy_updated_at=timezone.now()
        )
        
        trans2 = Transaction.objects.create(
            pluggy_transaction_id='trans-2',
            account=self.account,
            company=self.company,
            type='CREDIT',
            amount=200.00,
            description='Test Transaction 2',
            date=timezone.now(),
            pluggy_created_at=timezone.now(),
            pluggy_updated_at=timezone.now()
        )
        
        event_data = {
            'event': 'transactions.deleted',
            'eventId': 'evt-204',
            'itemId': self.item.pluggy_item_id,
            'transactionIds': ['trans-1', 'trans-2']
        }
        
        # Process event
        from apps.banking.tasks import _handle_transactions_deleted
        _handle_transactions_deleted(event_data)
        
        # Check transactions were soft deleted
        trans1.refresh_from_db()
        trans2.refresh_from_db()
        
        self.assertTrue(trans1.is_deleted)
        self.assertTrue(trans2.is_deleted)
        self.assertIsNotNone(trans1.deleted_at)
        self.assertIsNotNone(trans2.deleted_at)
    
    @patch('apps.banking.tasks.sync_bank_account.delay')
    def test_accounts_created_event(self, mock_sync):
        """Test processing accounts.created event"""
        event_data = {
            'event': 'accounts.created',
            'eventId': 'evt-205',
            'itemId': self.item.pluggy_item_id,
            'accountIds': ['new-account-1', 'new-account-2']
        }
        
        # Process event
        from apps.banking.tasks import _handle_accounts_created
        _handle_accounts_created(event_data)
        
        # Check sync was triggered
        mock_sync.assert_called_once_with(str(self.item.id))