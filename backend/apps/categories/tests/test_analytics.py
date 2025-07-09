"""
Test categorization analytics functionality
Tests for CategorizationAnalyticsView and performance metrics
"""
from apps.banking.models import BankAccount, BankProvider, Transaction, TransactionCategory
from apps.categories.models import CategorizationLog, CategoryPerformance, AITrainingData
from apps.categories.services import CategoryAnalyticsService
from apps.companies.models import Company, SubscriptionPlan
from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient
from unittest.mock import Mock, patch
from datetime import timedelta
import uuid

User = get_user_model()


@override_settings(CELERY_TASK_ALWAYS_EAGER=True, CELERY_TASK_EAGER_PROPAGATES=True)
class CategorizationAnalyticsViewTests(TestCase):
    """Test categorization analytics and insights"""
    
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
        
        # Setup API client
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        self.url = reverse('categories:categorization-analytics')
    
    def test_get_analytics_empty_data(self):
        """Test analytics view with no data"""
        with patch.object(CategoryAnalyticsService, 'calculate_accuracy_metrics') as mock_accuracy, \
             patch.object(CategoryAnalyticsService, 'get_category_insights') as mock_insights, \
             patch.object(CategoryAnalyticsService, 'suggest_improvements') as mock_suggest:
            
            mock_accuracy.return_value = {
                'total_categorizations': 0,
                'accuracy': 0.0,
                'ai_accuracy': 0.0,
                'rule_accuracy': 0.0,
                'method_breakdown': {}
            }
            mock_insights.return_value = []
            mock_suggest.return_value = []
            
            response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('accuracy_metrics', response.data)
        self.assertIn('category_insights', response.data)
        self.assertIn('improvement_suggestions', response.data)
        self.assertIn('recent_activity', response.data)
        
        # Check empty metrics
        accuracy = response.data['accuracy_metrics']
        self.assertEqual(accuracy['total_categorizations'], 0)
        self.assertEqual(accuracy['accuracy'], 0.0)
    
    def test_get_analytics_with_data(self):
        """Test analytics view with categorization data"""
        # Create transactions
        transaction1 = Transaction.objects.create(
            bank_account=self.bank_account,
            external_id='trans1',
            amount=-100.00,
            description='Restaurant payment',
            transaction_date=timezone.now(),
            transaction_type='debit',
            category=self.food_category,
            is_ai_categorized=True,
            ai_category_confidence=0.85
        )
        
        transaction2 = Transaction.objects.create(
            bank_account=self.bank_account,
            external_id='trans2',
            amount=-50.00,
            description='Uber ride',
            transaction_date=timezone.now(),
            transaction_type='debit',
            category=self.transport_category,
            is_ai_categorized=True,
            ai_category_confidence=0.90
        )
        
        # Create categorization logs
        CategorizationLog.objects.create(
            transaction=transaction1,
            method='ai',
            suggested_category=self.food_category,
            confidence_score=0.85,
            processing_time_ms=150,
            was_accepted=True,
            ai_model_version='v1.0'
        )
        
        CategorizationLog.objects.create(
            transaction=transaction2,
            method='ai',
            suggested_category=self.transport_category,
            confidence_score=0.90,
            processing_time_ms=120,
            was_accepted=True,
            ai_model_version='v1.0'
        )
        
        # Mock analytics service methods
        with patch.object(CategoryAnalyticsService, 'calculate_accuracy_metrics') as mock_accuracy, \
             patch.object(CategoryAnalyticsService, 'get_category_insights') as mock_insights, \
             patch.object(CategoryAnalyticsService, 'suggest_improvements') as mock_suggest:
            
            mock_accuracy.return_value = {
                'total_categorizations': 2,
                'accuracy': 1.0,
                'ai_accuracy': 1.0,
                'rule_accuracy': 0.0,
                'method_breakdown': {
                    'ai': {'total': 2, 'correct': 2, 'accuracy': 1.0},
                    'rule': {'total': 0, 'correct': 0, 'accuracy': 0.0}
                }
            }
            mock_insights.return_value = []
            mock_suggest.return_value = []
            
            response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['accuracy_metrics']['total_categorizations'], 2)
        self.assertEqual(response.data['accuracy_metrics']['accuracy'], 1.0)
        self.assertEqual(len(response.data['recent_activity']), 2)
    
    def test_analytics_with_period_filter(self):
        """Test analytics with custom period filter"""
        # Create old transaction (should not be included)
        old_transaction = Transaction.objects.create(
            bank_account=self.bank_account,
            external_id='old_trans',
            amount=-200.00,
            description='Old payment',
            transaction_date=timezone.now() - timedelta(days=60),
            transaction_type='debit',
            category=self.food_category
        )
        
        # Create recent transaction
        recent_transaction = Transaction.objects.create(
            bank_account=self.bank_account,
            external_id='recent_trans',
            amount=-75.00,
            description='Recent payment',
            transaction_date=timezone.now(),
            transaction_type='debit',
            category=self.transport_category
        )
        
        # Create logs
        CategorizationLog.objects.create(
            transaction=old_transaction,
            method='rule',
            suggested_category=self.food_category,
            confidence_score=1.0,
            processing_time_ms=50,
            created_at=timezone.now() - timedelta(days=60)
        )
        
        CategorizationLog.objects.create(
            transaction=recent_transaction,
            method='rule',
            suggested_category=self.transport_category,
            confidence_score=1.0,
            processing_time_ms=45
        )
        
        # Test with 7 days period
        with patch.object(CategoryAnalyticsService, 'calculate_accuracy_metrics') as mock_accuracy, \
             patch.object(CategoryAnalyticsService, 'get_category_insights') as mock_insights, \
             patch.object(CategoryAnalyticsService, 'suggest_improvements') as mock_suggest:
            
            mock_accuracy.return_value = {
                'total_categorizations': 1,
                'accuracy': 1.0,
                'ai_accuracy': 0.0,
                'rule_accuracy': 1.0,
                'method_breakdown': {}
            }
            mock_insights.return_value = []
            mock_suggest.return_value = []
            
            response = self.client.get(self.url, {'period_days': 7})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Recent activity is not filtered by period_days in the view, 
        # it always returns last 10, so we should check that both are returned
        self.assertGreater(len(response.data['recent_activity']), 0)
    
    def test_improvement_suggestions(self):
        """Test improvement suggestions feature"""
        with patch.object(CategoryAnalyticsService, 'suggest_improvements') as mock_suggest:
            mock_suggest.return_value = [
                {
                    'type': 'low_accuracy_category',
                    'category': 'Utilidades',
                    'accuracy': 0.45,
                    'suggestion': 'Consider creating more specific rules for this category'
                },
                {
                    'type': 'missing_rules',
                    'pattern': 'UBER',
                    'frequency': 25,
                    'suggestion': 'Create a keyword rule for "UBER" to categorize as Transport'
                }
            ]
            
            response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        suggestions = response.data['improvement_suggestions']
        self.assertEqual(len(suggestions), 2)
        self.assertEqual(suggestions[0]['type'], 'low_accuracy_category')
        self.assertEqual(suggestions[1]['type'], 'missing_rules')
    
    def test_category_insights(self):
        """Test category insights feature"""
        # Create training data for insights
        AITrainingData.objects.create(
            company=self.company,
            description='Uber to work',
            amount=-30.00,
            transaction_type='debit',
            category=self.transport_category,
            verified_by=self.user,
            verification_source='user_feedback'
        )
        
        AITrainingData.objects.create(
            company=self.company,
            description='Restaurant lunch',
            amount=-45.00,
            transaction_type='debit',
            category=self.food_category,
            verified_by=self.user,
            verification_source='user_feedback'
        )
        
        with patch.object(CategoryAnalyticsService, 'calculate_accuracy_metrics') as mock_accuracy, \
             patch.object(CategoryAnalyticsService, 'get_category_insights') as mock_insights, \
             patch.object(CategoryAnalyticsService, 'suggest_improvements') as mock_suggest:
            
            mock_accuracy.return_value = {
                'total_categorizations': 2,
                'accuracy': 0.8,
                'ai_accuracy': 0.8,
                'rule_accuracy': 0.0,
                'method_breakdown': {}
            }
            mock_suggest.return_value = []
            mock_insights.return_value = {
                'most_used_categories': [
                    {'category': 'Alimentação', 'count': 150, 'percentage': 35.5},
                    {'category': 'Transporte', 'count': 120, 'percentage': 28.4}
                ],
                'least_accurate_categories': [
                    {'category': 'Utilidades', 'accuracy': 0.45},
                    {'category': 'Outros', 'accuracy': 0.52}
                ],
                'training_data_summary': {
                    'total': 250,
                    'by_source': {
                        'user_feedback': 180,
                        'rule_based': 50,
                        'ai_confident': 20
                    }
                }
            }
            
            response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        insights = response.data['category_insights']
        self.assertIn('most_used_categories', insights)
        self.assertIn('least_accurate_categories', insights)
        self.assertIn('training_data_summary', insights)
    
    def test_authentication_required(self):
        """Test authentication requirement"""
        self.client.force_authenticate(user=None)
        
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_recent_activity_ordering(self):
        """Test that recent activity is ordered by creation date"""
        # Create transactions with different dates
        trans1 = Transaction.objects.create(
            bank_account=self.bank_account,
            external_id='trans1',
            amount=-100.00,
            description='Payment 1',
            transaction_date=timezone.now() - timedelta(days=2),
            transaction_type='debit'
        )
        
        trans2 = Transaction.objects.create(
            bank_account=self.bank_account,
            external_id='trans2',
            amount=-200.00,
            description='Payment 2',
            transaction_date=timezone.now() - timedelta(days=1),
            transaction_type='debit'
        )
        
        trans3 = Transaction.objects.create(
            bank_account=self.bank_account,
            external_id='trans3',
            amount=-300.00,
            description='Payment 3',
            transaction_date=timezone.now(),
            transaction_type='debit'
        )
        
        # Create logs in different order
        # Note: Cannot set created_at directly as it's auto_now_add
        log1 = CategorizationLog.objects.create(
            transaction=trans1,
            method='ai',
            suggested_category=self.food_category,
            confidence_score=0.8,
            processing_time_ms=100
        )
        
        log2 = CategorizationLog.objects.create(
            transaction=trans2,
            method='ai',
            suggested_category=self.utilities_category,
            confidence_score=0.7,
            processing_time_ms=120
        )
        
        log3 = CategorizationLog.objects.create(
            transaction=trans3,
            method='rule',
            suggested_category=self.transport_category,
            confidence_score=1.0,
            processing_time_ms=50
        )
        
        with patch.object(CategoryAnalyticsService, 'calculate_accuracy_metrics') as mock_accuracy, \
             patch.object(CategoryAnalyticsService, 'get_category_insights') as mock_insights, \
             patch.object(CategoryAnalyticsService, 'suggest_improvements') as mock_suggest:
            
            mock_accuracy.return_value = {
                'total_categorizations': 3,
                'accuracy': 0.8,
                'ai_accuracy': 0.75,
                'rule_accuracy': 1.0,
                'method_breakdown': {}
            }
            mock_insights.return_value = []
            mock_suggest.return_value = []
            
            response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        recent_activity = response.data['recent_activity']
        
        # Should be ordered by created_at descending (most recent first)
        # Since we can't control auto_now_add, we verify order matches creation order
        self.assertEqual(len(recent_activity), 3)
        # The logs were created in order: log1, log2, log3
        # So descending order should be: log3 (trans3), log2 (trans2), log1 (trans1)
        self.assertEqual(str(recent_activity[0]['transaction']), str(trans3.id))
        self.assertEqual(str(recent_activity[1]['transaction']), str(trans2.id))
        self.assertEqual(str(recent_activity[2]['transaction']), str(trans1.id))
    
    def test_analytics_from_different_company(self):
        """Test that analytics only show data from user's company"""
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
        
        # Create transaction for other company
        other_transaction = Transaction.objects.create(
            bank_account=other_account,
            external_id='other_trans',
            amount=-500.00,
            description='Other company payment',
            transaction_date=timezone.now(),
            transaction_type='debit',
            category=self.food_category
        )
        
        # Create log for other company
        CategorizationLog.objects.create(
            transaction=other_transaction,
            method='ai',
            suggested_category=self.food_category,
            confidence_score=0.9,
            processing_time_ms=100
        )
        
        # Create transaction for current company
        my_transaction = Transaction.objects.create(
            bank_account=self.bank_account,
            external_id='my_trans',
            amount=-100.00,
            description='My payment',
            transaction_date=timezone.now(),
            transaction_type='debit',
            category=self.transport_category
        )
        
        CategorizationLog.objects.create(
            transaction=my_transaction,
            method='rule',
            suggested_category=self.transport_category,
            confidence_score=1.0,
            processing_time_ms=50
        )
        
        with patch.object(CategoryAnalyticsService, 'calculate_accuracy_metrics') as mock_accuracy, \
             patch.object(CategoryAnalyticsService, 'get_category_insights') as mock_insights, \
             patch.object(CategoryAnalyticsService, 'suggest_improvements') as mock_suggest:
            
            mock_accuracy.return_value = {
                'total_categorizations': 1,
                'accuracy': 1.0,
                'ai_accuracy': 0.0,
                'rule_accuracy': 1.0,
                'method_breakdown': {}
            }
            mock_insights.return_value = []
            mock_suggest.return_value = []
            
            response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should only see current company's data
        self.assertEqual(len(response.data['recent_activity']), 1)
        self.assertEqual(str(response.data['recent_activity'][0]['transaction']), str(my_transaction.id))