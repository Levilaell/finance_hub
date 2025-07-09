"""
Test AI-related views for Categories app
Tests for BulkCategorizationView and CategoryTrainingView
"""
from apps.banking.models import BankAccount, BankProvider, Transaction, TransactionCategory
from apps.categories.models import AITrainingData, CategorySuggestion
from apps.categories.services import AICategorizationService
from apps.companies.models import Company, SubscriptionPlan
from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient
from unittest.mock import Mock, patch
import uuid

User = get_user_model()


@override_settings(CELERY_TASK_ALWAYS_EAGER=True, CELERY_TASK_EAGER_PROPAGATES=True)
class BulkCategorizationViewTests(TestCase):
    """Test bulk categorization operations"""
    
    def setUp(self):
        # Create subscription plan
        self.plan = SubscriptionPlan.objects.create(
            name='Test Plan',
            slug='test-plan',
            plan_type='pro',
            price_monthly=99.90,
            price_yearly=999.00,
            max_users=5,
            max_bank_accounts=5
        )
        
        # Create user and company
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        self.company = Company.objects.create(
            name='Test Company',
            cnpj='11222333000181',
            owner=self.user,
            subscription_plan=self.plan,
            enable_ai_categorization=False
        )
        self.user.company = self.company
        self.user.save()
        
        # Create bank provider
        self.bank_provider = BankProvider.objects.create(
            name='Test Bank',
            code='test-bank',
            is_active=True
        )
        
        # Create bank account
        self.bank_account = BankAccount.objects.create(
            company=self.company,
            bank_provider=self.bank_provider,
            account_type='checking',
            agency='0001',
            account_number='12345',
            current_balance=1000.00
        )
        
        # Create categories
        self.food_category = TransactionCategory.objects.create(
            name='Alimentação',
            slug='alimentacao',
            category_type='expense'
        )
        self.transport_category = TransactionCategory.objects.create(
            name='Transporte',
            slug='transporte',
            category_type='expense'
        )
        
        # Setup API client
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        self.url = reverse('categories:bulk-categorization')
    
    def test_categorize_uncategorized_transactions(self):
        """Test bulk categorization of uncategorized transactions"""
        # Create uncategorized transactions
        for i in range(5):
            Transaction.objects.create(
                bank_account=self.bank_account,
                external_id=f'trans_{i}',
                amount=-50.00,
                description=f'Restaurant payment {i}',
                transaction_date=timezone.now(),
                transaction_type='debit',
                category=None  # Uncategorized
            )
        
        # Mock AI categorization service
        with patch.object(AICategorizationService, 'categorize_transaction') as mock_categorize:
            mock_categorize.return_value = {
                'category': self.food_category,
                'confidence': 0.85,
                'method': 'ai',
                'reason': 'Test categorization'
            }
            
            response = self.client.post(self.url, {
                'operation': 'categorize_uncategorized',
                'limit': 10
            })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'success')
        self.assertEqual(response.data['operation'], 'categorize_uncategorized')
        self.assertIn('results', response.data)
        
        # Verify transactions were categorized
        categorized_count = Transaction.objects.filter(
            bank_account=self.bank_account,
            category__isnull=False
        ).count()
        self.assertEqual(categorized_count, 5)
    
    def test_recategorize_low_confidence_transactions(self):
        """Test recategorization of low confidence transactions"""
        # Create transactions with low confidence
        for i in range(3):
            Transaction.objects.create(
                bank_account=self.bank_account,
                external_id=f'low_conf_{i}',
                amount=-30.00,
                description=f'Unclear payment {i}',
                transaction_date=timezone.now(),
                transaction_type='debit',
                category=self.transport_category,
                ai_category_confidence=0.3,  # Low confidence
                is_ai_categorized=True
            )
        
        # Create high confidence transaction (should not be recategorized)
        Transaction.objects.create(
            bank_account=self.bank_account,
            external_id='high_conf',
            amount=-100.00,
            description='Clear transport payment',
            transaction_date=timezone.now(),
            transaction_type='debit',
            category=self.transport_category,
            ai_category_confidence=0.9,
            is_ai_categorized=True
        )
        
        # Mock AI categorization service
        with patch.object(AICategorizationService, 'categorize_transaction') as mock_categorize:
            mock_categorize.return_value = {
                'category': self.food_category,
                'confidence': 0.75,
                'method': 'ai',
                'reason': 'Test recategorization'
            }
            
            response = self.client.post(self.url, {
                'operation': 'recategorize_low_confidence',
                'confidence_threshold': 0.5
            })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'success')
        self.assertIn('results', response.data)
    
    def test_invalid_operation(self):
        """Test invalid operation handling"""
        response = self.client.post(self.url, {
            'operation': 'invalid_operation'
        })
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
        self.assertEqual(response.data['error'], 'Operação não suportada')
    
    def test_authentication_required(self):
        """Test authentication requirement"""
        self.client.force_authenticate(user=None)
        
        response = self.client.post(self.url, {
            'operation': 'categorize_uncategorized'
        })
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    @patch('apps.categories.services.BulkCategorizationService.categorize_uncategorized_transactions')
    def test_bulk_categorization_with_limit(self, mock_bulk_service):
        """Test bulk categorization respects limit parameter"""
        mock_bulk_service.return_value = {
            'processed': 50,
            'categorized': 45,
            'failed': 5
        }
        
        response = self.client.post(self.url, {
            'operation': 'categorize_uncategorized',
            'limit': 50
        })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        mock_bulk_service.assert_called_once_with(self.company, 50)
    
    @patch('apps.categories.services.BulkCategorizationService.recategorize_low_confidence_transactions')
    def test_recategorization_with_custom_threshold(self, mock_bulk_service):
        """Test recategorization with custom confidence threshold"""
        mock_bulk_service.return_value = {
            'processed': 20,
            'recategorized': 18,
            'failed': 2
        }
        
        response = self.client.post(self.url, {
            'operation': 'recategorize_low_confidence',
            'confidence_threshold': 0.7
        })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        mock_bulk_service.assert_called_once_with(self.company, 0.7)


@override_settings(CELERY_TASK_ALWAYS_EAGER=True, CELERY_TASK_EAGER_PROPAGATES=True)
class CategoryTrainingViewTests(TestCase):
    """Test category training and learning functionality"""
    
    def setUp(self):
        # Create subscription plan
        self.plan = SubscriptionPlan.objects.create(
            name='Test Plan',
            slug='test-plan',
            plan_type='pro',
            price_monthly=99.90,
            price_yearly=999.00,
            max_users=5,
            max_bank_accounts=5
        )
        
        # Create user and company
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        self.company = Company.objects.create(
            name='Test Company',
            cnpj='11222333000181',
            owner=self.user,
            subscription_plan=self.plan,
            enable_ai_categorization=False
        )
        self.user.company = self.company
        self.user.save()
        
        # Create bank provider
        self.bank_provider = BankProvider.objects.create(
            name='Test Bank',
            code='test-bank',
            is_active=True
        )
        
        # Create bank account
        self.bank_account = BankAccount.objects.create(
            company=self.company,
            bank_provider=self.bank_provider,
            account_type='checking',
            agency='0001',
            account_number='12345',
            current_balance=1000.00
        )
        
        # Create categories
        self.food_category = TransactionCategory.objects.create(
            name='Alimentação',
            slug='alimentacao',
            category_type='expense'
        )
        self.transport_category = TransactionCategory.objects.create(
            name='Transporte',
            slug='transporte',
            category_type='expense'
        )
        
        # Create transaction
        self.transaction = Transaction.objects.create(
            bank_account=self.bank_account,
            external_id='test_trans_1',
            amount=-100.00,
            description='Uber ride',
            transaction_date=timezone.now(),
            transaction_type='debit'
        )
        
        # Setup API client
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        self.url = reverse('categories:category-training')
    
    def test_train_with_manual_categorization(self):
        """Test training AI with manual categorization"""
        with patch.object(AICategorizationService, 'learn_from_feedback') as mock_learn:
            response = self.client.post(self.url, {
                'transaction_id': self.transaction.id,
                'category_id': self.transport_category.id
            })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'success')
        self.assertIn('message', response.data)
        
        # Verify transaction was updated
        self.transaction.refresh_from_db()
        self.assertEqual(self.transaction.category, self.transport_category)
        self.assertTrue(self.transaction.is_manually_reviewed)
        
        # Verify AI learning was called
        mock_learn.assert_called_once_with(
            self.transaction,
            self.transport_category,
            self.user
        )
    
    def test_missing_parameters(self):
        """Test error handling for missing parameters"""
        # Missing transaction_id
        response = self.client.post(self.url, {
            'category_id': self.transport_category.id
        })
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
        
        # Missing category_id
        response = self.client.post(self.url, {
            'transaction_id': self.transaction.id
        })
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
    
    def test_invalid_transaction_id(self):
        """Test error handling for invalid transaction ID"""
        # Use a valid UUID format that doesn't exist
        fake_uuid = str(uuid.uuid4())
        response = self.client.post(self.url, {
            'transaction_id': fake_uuid,
            'category_id': self.transport_category.id
        })
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn('error', response.data)
        self.assertEqual(response.data['error'], 'Transação não encontrada')
    
    def test_transaction_from_different_company(self):
        """Test that users cannot train with transactions from other companies"""
        # Create another user and company
        other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='otherpass123',
            first_name='Other',
            last_name='User'
        )
        other_company = Company.objects.create(
            name='Other Company',
            cnpj='22333444000195',
            owner=other_user,
            subscription_plan=self.plan,
            enable_ai_categorization=False
        )
        other_account = BankAccount.objects.create(
            company=other_company,
            bank_provider=self.bank_provider,
            account_type='checking',
            agency='0002',
            account_number='67890'
        )
        other_transaction = Transaction.objects.create(
            bank_account=other_account,
            external_id='other_trans',
            amount=-50.00,
            description='Other transaction',
            transaction_date=timezone.now(),
            transaction_type='debit'
        )
        
        response = self.client.post(self.url, {
            'transaction_id': other_transaction.id,
            'category_id': self.transport_category.id
        })
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_authentication_required(self):
        """Test authentication requirement"""
        self.client.force_authenticate(user=None)
        
        response = self.client.post(self.url, {
            'transaction_id': self.transaction.id,
            'category_id': self.transport_category.id
        })
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_training_creates_ai_training_data(self):
        """Test that training creates AI training data record"""
        initial_count = AITrainingData.objects.count()
        
        with patch.object(AICategorizationService, 'learn_from_feedback') as mock_learn:
            # Configure mock to create training data
            def create_training_data(transaction, category, user):
                AITrainingData.objects.create(
                    company=transaction.bank_account.company,
                    description=transaction.description,
                    amount=transaction.amount,
                    transaction_type=transaction.transaction_type,
                    category=category,
                    verified_by=user,
                    verification_source='user_feedback'
                )
            
            mock_learn.side_effect = create_training_data
            
            response = self.client.post(self.url, {
                'transaction_id': self.transaction.id,
                'category_id': self.food_category.id
            })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(AITrainingData.objects.count(), initial_count + 1)
        
        # Verify training data
        training_data = AITrainingData.objects.latest('created_at')
        self.assertEqual(training_data.company, self.company)
        self.assertEqual(training_data.category, self.food_category)
        self.assertEqual(training_data.verified_by, self.user)
    
    def test_exception_handling(self):
        """Test general exception handling"""
        with patch.object(Transaction.objects, 'get') as mock_get:
            mock_get.side_effect = Exception('Database error')
            
            response = self.client.post(self.url, {
                'transaction_id': self.transaction.id,
                'category_id': self.transport_category.id
            })
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
        self.assertEqual(response.data['error'], 'Database error')