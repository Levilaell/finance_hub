"""
Tests for AI Insights API endpoints
"""
from decimal import Decimal
from unittest.mock import patch, MagicMock
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model

from apps.companies.models import Company, SubscriptionPlan, CompanyUser
from apps.ai_insights.models import (
    AICredit, AICreditTransaction, AIConversation, 
    AIMessage, AIInsight
)

User = get_user_model()


class BaseAIInsightsAPITest(TestCase):
    """Base test class with common setup"""
    
    def setUp(self):
        self.client = APIClient()
        
        # Create user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        
        # Create plan
        self.plan = SubscriptionPlan.objects.create(
            name='Professional',
            slug='professional',
            plan_type='professional',
            price_monthly=Decimal('99.90'),
            price_yearly=Decimal('999.00'),
            max_bank_accounts=10,
            max_transactions=5000
        )
        
        # Create company
        self.company = Company.objects.create(
            name='Test Company',
            owner=self.user,
            cnpj='12345678901234',
            company_type='ltda',
            business_sector='technology'
        )
        
        # Create company user
        CompanyUser.objects.create(
            user=self.user,
            company=self.company,
            role='admin',
            is_active=True
        )
        
        # Set subscription plan on company
        self.company.subscription_plan = self.plan
        self.company.subscription_status = 'active'
        self.company.save()
        
        # Create AI credits
        self.ai_credit = AICredit.objects.create(
            company=self.company,
            balance=100,
            monthly_allowance=100
        )
        
        # Authenticate
        self.client.force_authenticate(user=self.user)


class CreditAPITest(BaseAIInsightsAPITest):
    """Test Credit-related endpoints"""
    
    def test_get_credit_balance(self):
        """Test getting credit balance"""
        # Use list endpoint instead of detail with company ID
        url = reverse('ai_insights:aicredit-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreater(response.data['count'], 0)
        
        # Get first credit record
        credit_data = response.data['results'][0]
        self.assertEqual(credit_data['balance'], 100)
        self.assertEqual(credit_data['monthly_allowance'], 100)
    
    def test_get_credit_transactions(self):
        """Test getting credit transaction history"""
        # Create some transactions
        AICreditTransaction.objects.create(
            company=self.company,
            type='usage',
            amount=-5,
            balance_before=100,
            balance_after=95,
            description='Chat usage'
        )
        
        url = reverse('ai_insights:aicredit-transactions')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['amount'], -5)
    
    @patch('apps.payments.services.StripeService.process_credit_purchase')
    @patch('apps.companies.models.PaymentMethod.objects.get')
    def test_purchase_credits(self, mock_payment_method, mock_stripe):
        """Test purchasing additional credits"""
        # Mock payment method
        mock_payment_method.return_value = MagicMock(
            id='pm_test123',
            company=self.company,
            is_active=True,
            stripe_payment_method_id='pm_stripe_123'
        )
        
        # Mock Stripe response
        mock_stripe.return_value = {
            'success': True,
            'payment_id': 'pi_test123',
            'status': 'succeeded',
            'gateway': 'stripe'
        }
        
        url = reverse('ai_insights:aicredit-purchase')
        data = {
            'amount': 100,  # 100 credits
            'payment_method_id': 'pm_test123'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['success'])
        self.assertIn('transaction_id', response.data['data'])
        
        # Check credits were added
        self.ai_credit.refresh_from_db()
        self.assertEqual(self.ai_credit.balance, 200)  # 100 + 100
        
        # Check transaction was created
        transaction = AICreditTransaction.objects.filter(
            company=self.company,
            type='purchase'
        ).first()
        self.assertIsNotNone(transaction)
        self.assertEqual(transaction.amount, 100)


class ConversationAPITest(BaseAIInsightsAPITest):
    """Test Conversation-related endpoints"""
    
    def test_create_conversation(self):
        """Test creating a new conversation"""
        url = reverse('ai_insights:aiconversation-list')
        data = {
            'title': 'Financial Analysis Chat'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['title'], 'Financial Analysis Chat')
        self.assertEqual(response.data['status'], 'active')
        self.assertEqual(response.data['company'], str(self.company.id))
    
    def test_list_conversations(self):
        """Test listing user's conversations"""
        # Create conversations
        AIConversation.objects.create(
            company=self.company,
            user=self.user,
            title='Chat 1'
        )
        AIConversation.objects.create(
            company=self.company,
            user=self.user,
            title='Chat 2',
            status='archived'
        )
        
        url = reverse('ai_insights:aiconversation-list')
        # Request all conversations to get both active and archived
        response = self.client.get(url, {'status': 'all'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)
        
        # Test filtering by status
        response = self.client.get(url, {'status': 'active'})
        self.assertEqual(response.data['count'], 1)
    
    def test_get_conversation_messages(self):
        """Test getting messages for a conversation"""
        conversation = AIConversation.objects.create(
            company=self.company,
            user=self.user,
            title='Test Chat'
        )
        
        # Create messages
        AIMessage.objects.create(
            conversation=conversation,
            role='user',
            content='Hello'
        )
        AIMessage.objects.create(
            conversation=conversation,
            role='assistant',
            content='Hello! How can I help you?'
        )
        
        url = reverse('ai_insights:aimessage-list') + f'?conversation={conversation.id}'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)
    
    @patch('apps.ai_insights.services.ai_service.AIService.process_message')
    def test_send_message(self, mock_process):
        """Test sending a message in conversation"""
        conversation = AIConversation.objects.create(
            company=self.company,
            user=self.user,
            title='Test Chat'
        )
        
        # Create mock AI message object
        mock_ai_message = MagicMock()
        mock_ai_message.id = 'msg123'
        mock_ai_message.content = 'Your expenses are...'
        mock_ai_message.structured_data = None
        mock_ai_message.insights = None
        
        # Mock AI service response with proper structure
        mock_process.return_value = {
            'ai_message': mock_ai_message,
            'credits_used': 3,
            'credits_remaining': 97,
            'insights': []
        }
        
        url = reverse('ai_insights:aiconversation-send-message', kwargs={'pk': conversation.id})
        data = {
            'content': 'What are my expenses?',
            'request_type': 'general'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['success'])
        self.assertIn('message', response.data['data'])
        self.assertEqual(response.data['data']['credits_used'], 3)
        
        # Verify mock was called
        mock_process.assert_called_once()
    
    def test_archive_conversation(self):
        """Test archiving a conversation"""
        conversation = AIConversation.objects.create(
            company=self.company,
            user=self.user,
            title='Test Chat'
        )
        
        url = reverse('ai_insights:aiconversation-archive', kwargs={'pk': conversation.id})
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        conversation.refresh_from_db()
        self.assertEqual(conversation.status, 'archived')


class InsightAPITest(BaseAIInsightsAPITest):
    """Test Insight-related endpoints"""
    
    def test_list_insights(self):
        """Test listing company insights"""
        # Create insights
        AIInsight.objects.create(
            company=self.company,
            type='cost_saving',
            priority='high',
            title='Reduce costs',
            description='Save money'
        )
        AIInsight.objects.create(
            company=self.company,
            type='risk',
            priority='critical',
            title='Cash flow risk',
            description='Low cash'
        )
        
        url = reverse('ai_insights:aiinsight-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)
        
        # Test filtering by priority
        response = self.client.get(url, {'priority': 'critical'})
        self.assertEqual(response.data['count'], 1)
    
    def test_get_insight_detail(self):
        """Test getting insight details"""
        insight = AIInsight.objects.create(
            company=self.company,
            type='opportunity',
            priority='medium',
            title='Growth opportunity',
            description='Expand to new market',
            potential_impact=Decimal('50000.00'),
            action_items=['Research market', 'Create plan']
        )
        
        url = reverse('ai_insights:aiinsight-detail', kwargs={'pk': insight.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'Growth opportunity')
        self.assertEqual(response.data['potential_impact'], '50000.00')
        self.assertEqual(len(response.data['action_items']), 2)
    
    def test_mark_insight_viewed(self):
        """Test marking insight as viewed"""
        insight = AIInsight.objects.create(
            company=self.company,
            type='anomaly',
            priority='high',
            title='Unusual transaction',
            description='Check this transaction'
        )
        
        url = reverse('ai_insights:aiinsight-mark-viewed', kwargs={'pk': insight.id})
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        insight.refresh_from_db()
        self.assertEqual(insight.status, 'viewed')
        self.assertIsNotNone(insight.viewed_at)
    
    def test_take_action_on_insight(self):
        """Test marking insight action as taken"""
        insight = AIInsight.objects.create(
            company=self.company,
            type='cost_saving',
            priority='high',
            title='Reduce supplier cost',
            description='Renegotiate contract',
            potential_impact=Decimal('10000.00')
        )
        
        url = reverse('ai_insights:aiinsight-take-action', kwargs={'pk': insight.id})
        data = {
            'action_taken': True,
            'actual_impact': '8500.00',
            'user_feedback': 'Saved R$ 8,500 by renegotiating'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        insight.refresh_from_db()
        self.assertEqual(insight.status, 'completed')
        self.assertTrue(insight.action_taken)
        self.assertEqual(insight.actual_impact, Decimal('8500.00'))
        self.assertIsNotNone(insight.action_taken_at)
    
    def test_dismiss_insight(self):
        """Test dismissing an insight"""
        insight = AIInsight.objects.create(
            company=self.company,
            type='risk',
            priority='low',
            title='Minor risk',
            description='Low priority issue'
        )
        
        url = reverse('ai_insights:aiinsight-dismiss', kwargs={'pk': insight.id})
        data = {
            'reason': 'Not relevant to our business'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        insight.refresh_from_db()
        self.assertEqual(insight.status, 'dismissed')
        self.assertIn('Not relevant', insight.user_feedback)
    
    def test_insight_summary(self):
        """Test getting insight summary statistics"""
        # Create various insights
        insights_data = [
            ('critical', 'risk', 'Critical issue'),
            ('high', 'cost_saving', 'High savings'),
            ('medium', 'opportunity', 'Medium opportunity'),
            ('low', 'trend', 'Low priority trend')
        ]
        
        for priority, insight_type, title in insights_data:
            AIInsight.objects.create(
                company=self.company,
                type=insight_type,
                priority=priority,
                title=title,
                description=f'{title} description'
            )
        
        url = reverse('ai_insights:aiinsight-summary')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('stats', response.data)
        self.assertIn('by_type', response.data)
        self.assertIn('effectiveness', response.data)
        
        # Check stats
        stats = response.data['stats']
        self.assertEqual(stats['total'], 4)
        self.assertEqual(stats['new'], 4)  # All new by default
        self.assertEqual(stats['critical'], 1)


class MessageFeedbackAPITest(BaseAIInsightsAPITest):
    """Test message feedback endpoints"""
    
    def test_provide_message_feedback(self):
        """Test providing feedback on AI message"""
        conversation = AIConversation.objects.create(
            company=self.company,
            user=self.user,
            title='Test Chat'
        )
        
        message = AIMessage.objects.create(
            conversation=conversation,
            role='assistant',
            content='Here is my analysis...'
        )
        
        url = reverse('ai_insights:aimessage-feedback', kwargs={'pk': message.id})
        data = {
            'helpful': True,
            'user_feedback': 'Very insightful analysis!'  # Changed from 'feedback' to 'user_feedback'
        }
        
        response = self.client.post(url, data, format='json')  # Changed from PATCH to POST
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        
        message.refresh_from_db()
        self.assertTrue(message.helpful)
        self.assertEqual(message.user_feedback, 'Very insightful analysis!')


class PermissionTest(BaseAIInsightsAPITest):
    """Test API permissions"""
    
    def test_unauthorized_access(self):
        """Test that unauthenticated users cannot access endpoints"""
        self.client.force_authenticate(user=None)
        
        urls = [
            reverse('ai_insights:aicredit-list'),  # Changed from detail to list
            reverse('ai_insights:aiconversation-list'),
            reverse('ai_insights:aiinsight-list'),
        ]
        
        for url in urls:
            response = self.client.get(url)
            self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_cross_company_access_denied(self):
        """Test that users cannot access other companies' data"""
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
            owner=other_user,
            cnpj='09876543210987',
            company_type='ltda',
            business_sector='services'
        )
        
        # Create conversation for other company
        other_conversation = AIConversation.objects.create(
            company=other_company,
            user=other_user,
            title='Other Chat'
        )
        
        # Try to access with our user
        url = reverse('ai_insights:aiconversation-detail', kwargs={'pk': other_conversation.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)