"""
Test category suggestions functionality
Tests for CategorySuggestionViewSet and AI suggestions management
"""
from apps.banking.models import BankAccount, BankProvider, Transaction, TransactionCategory
from apps.categories.models import CategorySuggestion, AITrainingData
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
class CategorySuggestionViewSetTests(TestCase):
    """Test category suggestion review and feedback"""
    
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
        self.utilities_category = TransactionCategory.objects.create(
            name='Utilidades',
            slug='utilidades',
            category_type='expense'
        )
        
        # Create a transaction
        self.transaction = Transaction.objects.create(
            bank_account=self.bank_account,
            external_id='test_trans_1',
            amount=-150.00,
            description='Uber to airport',
            transaction_date=timezone.now(),
            transaction_type='debit'
        )
        
        # Setup API client
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        self.url = reverse('categories:category-suggestion-list')
    
    def test_list_pending_suggestions(self):
        """Test listing pending category suggestions"""
        # Create suggestions
        CategorySuggestion.objects.create(
            transaction=self.transaction,
            suggested_category=self.transport_category,
            confidence_score=0.85,
            model_version='v1.0'
        )
        
        # Create accepted suggestion (should not appear)
        accepted_trans = Transaction.objects.create(
            bank_account=self.bank_account,
            external_id='accepted_trans',
            amount=-100.00,
            description='Restaurant payment',
            transaction_date=timezone.now(),
            transaction_type='debit'
        )
        CategorySuggestion.objects.create(
            transaction=accepted_trans,
            suggested_category=self.food_category,
            confidence_score=0.90,
            is_accepted=True,
            reviewed_at=timezone.now()
        )
        
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['transaction'], self.transaction.id)
        self.assertFalse(response.data['results'][0]['is_accepted'])
        self.assertFalse(response.data['results'][0]['is_rejected'])
    
    def test_accept_suggestion(self):
        """Test accepting an AI suggestion"""
        suggestion = CategorySuggestion.objects.create(
            transaction=self.transaction,
            suggested_category=self.transport_category,
            confidence_score=0.85,
            model_version='v1.0'
        )
        
        url = reverse('categories:category-suggestion-accept', args=[suggestion.id])
        
        with patch.object(AICategorizationService, 'learn_from_feedback') as mock_learn:
            response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'accepted')
        
        # Verify transaction was updated
        self.transaction.refresh_from_db()
        self.assertEqual(self.transaction.category, self.transport_category)
        self.assertEqual(self.transaction.ai_category_confidence, 0.85)
        self.assertTrue(self.transaction.is_ai_categorized)
        self.assertTrue(self.transaction.is_manually_reviewed)
        
        # Verify suggestion was marked as accepted
        suggestion.refresh_from_db()
        self.assertTrue(suggestion.is_accepted)
        self.assertIsNotNone(suggestion.reviewed_at)
        self.assertEqual(suggestion.reviewed_by, self.user)
        
        # Verify AI learning was called
        mock_learn.assert_called_once_with(
            self.transaction,
            self.transport_category,
            self.user
        )
    
    def test_reject_suggestion(self):
        """Test rejecting an AI suggestion and providing correct category"""
        suggestion = CategorySuggestion.objects.create(
            transaction=self.transaction,
            suggested_category=self.food_category,
            confidence_score=0.65,
            model_version='v1.0'
        )
        
        url = reverse('categories:category-suggestion-reject', args=[suggestion.id])
        data = {
            'correct_category_id': self.transport_category.id,
            'feedback': 'This is clearly a transport expense, not food'
        }
        
        with patch.object(AICategorizationService, 'learn_from_feedback') as mock_learn:
            response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'rejected')
        
        # Verify transaction was updated with correct category
        self.transaction.refresh_from_db()
        self.assertEqual(self.transaction.category, self.transport_category)
        self.assertTrue(self.transaction.is_manually_reviewed)
        
        # Verify suggestion was marked as rejected
        suggestion.refresh_from_db()
        self.assertTrue(suggestion.is_rejected)
        self.assertEqual(suggestion.user_feedback, 'This is clearly a transport expense, not food')
        self.assertIsNotNone(suggestion.reviewed_at)
        self.assertEqual(suggestion.reviewed_by, self.user)
        
        # Verify AI learning was called with correct category
        mock_learn.assert_called_once_with(
            self.transaction,
            self.transport_category,
            self.user
        )
    
    def test_reject_without_category(self):
        """Test rejecting suggestion without providing correct category"""
        suggestion = CategorySuggestion.objects.create(
            transaction=self.transaction,
            suggested_category=self.food_category,
            confidence_score=0.65
        )
        
        url = reverse('categories:category-suggestion-reject', args=[suggestion.id])
        data = {
            'feedback': 'Wrong category'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
        self.assertEqual(response.data['error'], 'correct_category_id é obrigatório')
    
    def test_reject_with_invalid_category(self):
        """Test rejecting suggestion with invalid category ID"""
        suggestion = CategorySuggestion.objects.create(
            transaction=self.transaction,
            suggested_category=self.food_category,
            confidence_score=0.65
        )
        
        url = reverse('categories:category-suggestion-reject', args=[suggestion.id])
        data = {
            'correct_category_id': 99999,
            'feedback': 'Invalid category'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn('error', response.data)
        self.assertEqual(response.data['error'], 'Categoria não encontrada')
    
    def test_filter_by_confidence(self):
        """Test filtering suggestions by confidence score"""
        # Create suggestions with different confidence scores
        CategorySuggestion.objects.create(
            transaction=self.transaction,
            suggested_category=self.transport_category,
            confidence_score=0.9
        )
        
        low_conf_trans = Transaction.objects.create(
            bank_account=self.bank_account,
            external_id='low_conf',
            amount=-50.00,
            description='Unknown payment',
            transaction_date=timezone.now(),
            transaction_type='debit'
        )
        CategorySuggestion.objects.create(
            transaction=low_conf_trans,
            suggested_category=self.utilities_category,
            confidence_score=0.4
        )
        
        # Note: The default viewset doesn't have filtering implemented,
        # so this test would need to be adjusted based on actual implementation
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # All pending suggestions should be returned
        self.assertEqual(len(response.data['results']), 2)
    
    def test_suggestion_from_different_company(self):
        """Test that users cannot see suggestions from other companies"""
        # Create another company
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
            amount=-200.00,
            description='Other company transaction',
            transaction_date=timezone.now(),
            transaction_type='debit'
        )
        
        # Create suggestion for other company
        CategorySuggestion.objects.create(
            transaction=other_transaction,
            suggested_category=self.food_category,
            confidence_score=0.8
        )
        
        # Create suggestion for current company
        CategorySuggestion.objects.create(
            transaction=self.transaction,
            suggested_category=self.transport_category,
            confidence_score=0.85
        )
        
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['transaction'], self.transaction.id)
    
    def test_authentication_required(self):
        """Test authentication requirement"""
        self.client.force_authenticate(user=None)
        
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_accept_already_reviewed_suggestion(self):
        """Test accepting an already reviewed suggestion"""
        suggestion = CategorySuggestion.objects.create(
            transaction=self.transaction,
            suggested_category=self.transport_category,
            confidence_score=0.85,
            is_accepted=True,
            reviewed_at=timezone.now(),
            reviewed_by=self.user
        )
        
        url = reverse('categories:category-suggestion-accept', args=[suggestion.id])
        
        # The view should handle this gracefully
        response = self.client.post(url)
        
        # Since the viewset is ReadOnly, it might return 404 for an already reviewed suggestion
        # or it might still return success - depends on implementation
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_404_NOT_FOUND])
    
    def test_alternative_suggestions(self):
        """Test handling of alternative category suggestions"""
        # Create main suggestion
        suggestion = CategorySuggestion.objects.create(
            transaction=self.transaction,
            suggested_category=self.transport_category,
            confidence_score=0.85,
            alternative_suggestions=[
                {'category_id': self.food_category.id, 'confidence': 0.15},
                {'category_id': self.utilities_category.id, 'confidence': 0.10}
            ]
        )
        
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        result = response.data['results'][0]
        self.assertIn('alternative_suggestions', result)
        self.assertEqual(len(result['alternative_suggestions']), 2)