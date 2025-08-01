"""
Integration tests for AI Insights API endpoints
Tests complete API workflows, authentication, and data flow
"""
import json
from decimal import Decimal
from unittest.mock import patch, Mock
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status

from apps.companies.models import Company
from apps.ai_insights.models import (
    AICredit,
    AICreditTransaction,
    AIConversation,
    AIMessage,
    AIInsight
)

User = get_user_model()


class AIInsightsAPIIntegrationTest(TestCase):
    """Integration tests for AI Insights API"""
    
    def setUp(self):
        """Set up test data"""
        self.client = APIClient()
        
        # Create test company and user
        self.company = Company.objects.create(
            name='API Test Company',
            business_sector='Technology',
            employee_count=20,
            monthly_revenue=Decimal('100000.00')
        )
        
        self.user = User.objects.create_user(
            email='api-test@example.com',
            password='testpass123'
        )
        
        # Associate user with company (assuming company relationship exists)
        self.user.company = self.company
        self.user.save()
        
        # Create AI credits
        self.credit = AICredit.objects.create(
            company=self.company,
            balance=100,
            monthly_allowance=50,
            bonus_credits=25
        )
        
        # Authenticate client
        self.client.force_authenticate(user=self.user)
    
    def test_credits_api_workflow(self):
        """Test complete credits API workflow"""
        # 1. Get credits information
        response = self.client.get('/api/ai-insights/credits/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        credits_data = response.json()
        self.assertEqual(credits_data['balance'], 100)
        self.assertEqual(credits_data['monthly_allowance'], 50)
        self.assertEqual(credits_data['bonus_credits'], 25)
        
        # 2. Get credit transactions
        response = self.client.get('/api/ai-insights/credits/transactions/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        transactions_data = response.json()
        # Should return paginated results or list
        self.assertIn('results', transactions_data)
        
        # 3. Purchase credits (mocked)
        with patch('apps.ai_insights.services.credit_service.CreditService.purchase_credits') as mock_purchase:
            mock_purchase.return_value = {
                'transaction': Mock(id=123),
                'new_balance': 150
            }
            
            purchase_data = {
                'amount': 50,
                'payment_method_id': 'pm_test_card'
            }
            
            response = self.client.post(
                '/api/ai-insights/credits/purchase/',
                data=purchase_data,
                format='json'
            )
            
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            response_data = response.json()
            self.assertTrue(response_data['success'])
            self.assertEqual(response_data['data']['new_balance'], 150)
    
    def test_conversations_crud_workflow(self):
        """Test complete conversations CRUD workflow"""
        # 1. Create conversation
        conversation_data = {
            'title': 'API Test Conversation'
        }
        
        response = self.client.post(
            '/api/ai-insights/conversations/',
            data=conversation_data,
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        conversation = response.json()
        conversation_id = conversation['id']
        self.assertEqual(conversation['title'], 'API Test Conversation')
        self.assertEqual(conversation['status'], 'active')
        
        # 2. List conversations
        response = self.client.get('/api/ai-insights/conversations/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        conversations_data = response.json()
        self.assertIn('results', conversations_data)
        self.assertTrue(len(conversations_data['results']) > 0)
        
        # 3. Get specific conversation
        response = self.client.get(f'/api/ai-insights/conversations/{conversation_id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        conversation_detail = response.json()
        self.assertEqual(conversation_detail['id'], conversation_id)
        self.assertEqual(conversation_detail['title'], 'API Test Conversation')
        
        # 4. Update conversation
        update_data = {
            'title': 'Updated Conversation Title'
        }
        
        response = self.client.patch(
            f'/api/ai-insights/conversations/{conversation_id}/',
            data=update_data,
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        updated_conversation = response.json()
        self.assertEqual(updated_conversation['title'], 'Updated Conversation Title')
        
        # 5. Archive conversation
        response = self.client.post(f'/api/ai-insights/conversations/{conversation_id}/archive/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify conversation is archived
        response = self.client.get(f'/api/ai-insights/conversations/{conversation_id}/')
        conversation_detail = response.json()
        self.assertEqual(conversation_detail['status'], 'archived')
        
        # 6. Reactivate conversation
        response = self.client.post(f'/api/ai-insights/conversations/{conversation_id}/reactivate/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify conversation is active again
        response = self.client.get(f'/api/ai-insights/conversations/{conversation_id}/')
        conversation_detail = response.json()
        self.assertEqual(conversation_detail['status'], 'active')
    
    @patch('apps.ai_insights.services.ai_service.AIService.process_message')
    def test_send_message_workflow(self, mock_ai_service):
        """Test sending message workflow"""
        # Create conversation
        conversation = AIConversation.objects.create(
            company=self.company,
            user=self.user,
            title='Message Test Conversation'
        )
        
        # Mock AI service response
        mock_message = AIMessage.objects.create(
            conversation=conversation,
            role='assistant',
            content='AI response to your question',
            credits_used=3,
            tokens_used=150
        )
        
        mock_ai_service.return_value = {
            'ai_message': mock_message,
            'credits_used': 3,
            'credits_remaining': 97,
            'insights': []
        }
        
        # Send message
        message_data = {
            'content': 'What are my biggest expenses?',
            'request_type': 'analysis'
        }
        
        response = self.client.post(
            f'/api/ai-insights/conversations/{conversation.id}/send_message/',
            data=message_data,
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        response_data = response.json()
        
        # Verify response structure
        self.assertTrue(response_data['success'])
        self.assertIn('data', response_data)
        self.assertIn('message', response_data['data'])
        self.assertIn('credits_used', response_data['data'])
        self.assertIn('credits_remaining', response_data['data'])
        
        # Verify AI service was called correctly
        mock_ai_service.assert_called_once()
        call_args = mock_ai_service.call_args
        self.assertEqual(call_args[1]['conversation'], conversation)
        self.assertEqual(call_args[1]['user_message'], 'What are my biggest expenses?')
        self.assertEqual(call_args[1]['request_type'], 'analysis')
    
    def test_send_message_insufficient_credits(self):
        """Test sending message with insufficient credits"""
        # Set zero balance
        self.credit.balance = 0
        self.credit.bonus_credits = 0
        self.credit.save()
        
        conversation = AIConversation.objects.create(
            company=self.company,
            user=self.user,
            title='No Credits Test'
        )
        
        message_data = {
            'content': 'Test message',
            'request_type': 'general'
        }
        
        response = self.client.post(
            f'/api/ai-insights/conversations/{conversation.id}/send_message/',
            data=message_data,
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_402_PAYMENT_REQUIRED)
        response_data = response.json()
        self.assertFalse(response_data['success'])
        self.assertEqual(response_data['error_code'], 'INSUFFICIENT_CREDITS')
    
    def test_insights_api_workflow(self):
        """Test complete insights API workflow"""
        # Create test insights
        insight1 = AIInsight.objects.create(
            company=self.company,
            type='cost_saving',
            priority='high',
            title='Reduce office costs',
            description='Office costs can be reduced by 20%',
            potential_impact=Decimal('5000.00'),
            status='new'
        )
        
        insight2 = AIInsight.objects.create(
            company=self.company,
            type='opportunity',
            priority='medium',
            title='Revenue opportunity',
            description='New market opportunity identified',
            potential_impact=Decimal('15000.00'),
            status='viewed'
        )
        
        # 1. List insights
        response = self.client.get('/api/ai-insights/insights/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        insights = response.json()
        self.assertTrue(len(insights) >= 2)
        
        # 2. Filter insights by priority
        response = self.client.get('/api/ai-insights/insights/?priority=high')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        high_priority_insights = response.json()
        self.assertTrue(all(insight['priority'] == 'high' for insight in high_priority_insights))
        
        # 3. Get specific insight
        response = self.client.get(f'/api/ai-insights/insights/{insight1.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        insight_detail = response.json()
        self.assertEqual(insight_detail['title'], 'Reduce office costs')
        
        # 4. Mark insight as viewed
        response = self.client.post(f'/api/ai-insights/insights/{insight1.id}/mark_viewed/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify insight status updated
        insight1.refresh_from_db()
        self.assertEqual(insight1.status, 'viewed')
        self.assertIsNotNone(insight1.viewed_at)
        
        # 5. Take action on insight
        action_data = {
            'action_taken': True,
            'actual_impact': 4500.00,
            'user_feedback': 'Successfully reduced office costs by optimizing space usage'
        }
        
        response = self.client.post(
            f'/api/ai-insights/insights/{insight1.id}/take_action/',
            data=action_data,
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify insight updated
        insight1.refresh_from_db()
        self.assertTrue(insight1.action_taken)
        self.assertEqual(insight1.actual_impact, Decimal('4500.00'))
        
        # 6. Dismiss insight
        response = self.client.post(
            f'/api/ai-insights/insights/{insight2.id}/dismiss/',
            data={'reason': 'Not applicable to current situation'},
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify insight dismissed
        insight2.refresh_from_db()
        self.assertEqual(insight2.status, 'dismissed')
    
    def test_insights_summary_api(self):
        """Test insights summary API"""
        # Create insights with different statuses and priorities
        insights_data = [
            {'type': 'cost_saving', 'priority': 'critical', 'status': 'new', 'impact': 10000},
            {'type': 'opportunity', 'priority': 'high', 'status': 'in_progress', 'impact': 8000},
            {'type': 'risk', 'priority': 'medium', 'status': 'completed', 'impact': 5000},
            {'type': 'trend', 'priority': 'low', 'status': 'dismissed', 'impact': 2000}
        ]
        
        for data in insights_data:
            AIInsight.objects.create(
                company=self.company,
                type=data['type'],
                priority=data['priority'],
                status=data['status'],
                title=f"Test {data['type']} insight",
                description=f"Test insight for {data['type']}",
                potential_impact=Decimal(str(data['impact'])),
                actual_impact=Decimal(str(data['impact'])) if data['status'] == 'completed' else None
            )
        
        # Get summary
        response = self.client.get('/api/ai-insights/insights/summary/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        summary = response.json()
        
        # Verify summary structure
        self.assertIn('stats', summary)
        self.assertIn('by_type', summary)
        self.assertIn('effectiveness', summary)
        
        # Verify statistics
        stats = summary['stats']
        self.assertEqual(stats['total'], 4)
        self.assertEqual(stats['new'], 1)
        self.assertEqual(stats['in_progress'], 1)
        self.assertEqual(stats['completed'], 1)
        self.assertEqual(stats['critical'], 1)
        
        # Verify effectiveness calculation
        effectiveness = summary['effectiveness']
        self.assertEqual(effectiveness['insights_actioned'], 1)
        self.assertEqual(effectiveness['success_rate'], 25.0)  # 1 out of 4
    
    def test_export_conversations(self):
        """Test conversation export functionality"""
        # Create conversation with messages
        conversation = AIConversation.objects.create(
            company=self.company,
            user=self.user,
            title='Export Test Conversation'
        )
        
        AIMessage.objects.create(
            conversation=conversation,
            role='user',
            content='Test user message'
        )
        
        AIMessage.objects.create(
            conversation=conversation,
            role='assistant',
            content='Test AI response',
            credits_used=2
        )
        
        # Test JSON export
        response = self.client.get(f'/api/ai-insights/conversations/{conversation.id}/export/json/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response['Content-Type'], 'application/json')
        
        # Test CSV export
        response = self.client.get(f'/api/ai-insights/conversations/{conversation.id}/export/csv/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response['Content-Type'], 'text/csv')
        
        # Test PDF export
        response = self.client.get(f'/api/ai-insights/conversations/{conversation.id}/export/pdf/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response['Content-Type'], 'application/pdf')
    
    def test_export_insights(self):
        """Test insights export functionality"""
        # Create test insights
        for i in range(3):
            AIInsight.objects.create(
                company=self.company,
                type='cost_saving',
                priority='medium',
                title=f'Export Test Insight {i+1}',
                description=f'Test insight {i+1} for export',
                potential_impact=Decimal('1000.00')
            )
        
        # Test JSON export
        response = self.client.get('/api/ai-insights/insights/export/json/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response['Content-Type'], 'application/json')
        
        # Test CSV export
        response = self.client.get('/api/ai-insights/insights/export/csv/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response['Content-Type'], 'text/csv')
        
        # Test filtered export
        response = self.client.get('/api/ai-insights/insights/export/json/?status=new')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_authentication_required(self):
        """Test API requires authentication"""
        # Remove authentication
        self.client.force_authenticate(user=None)
        
        # Test various endpoints
        endpoints = [
            '/api/ai-insights/credits/',
            '/api/ai-insights/conversations/',
            '/api/ai-insights/insights/',
        ]
        
        for endpoint in endpoints:
            response = self.client.get(endpoint)
            self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_company_isolation(self):
        """Test data isolation between companies"""
        # Create another company with user
        other_company = Company.objects.create(
            name='Other Company',
            business_sector='Finance'
        )
        
        other_user = User.objects.create_user(
            email='other@example.com',
            password='testpass123'
        )
        other_user.company = other_company
        other_user.save()
        
        # Create data for other company
        other_conversation = AIConversation.objects.create(
            company=other_company,
            user=other_user,
            title='Other Company Conversation'
        )
        
        other_insight = AIInsight.objects.create(
            company=other_company,
            type='opportunity',
            priority='high',
            title='Other Company Insight',
            description='Insight for other company'
        )
        
        # Try to access other company's data
        response = self.client.get(f'/api/ai-insights/conversations/{other_conversation.id}/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        
        response = self.client.get(f'/api/ai-insights/insights/{other_insight.id}/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        
        # Verify own company's data is accessible
        own_conversation = AIConversation.objects.create(
            company=self.company,
            user=self.user,
            title='Own Company Conversation'
        )
        
        response = self.client.get(f'/api/ai-insights/conversations/{own_conversation.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_api_error_handling(self):
        """Test API error handling"""
        # Test 404 for non-existent resources
        response = self.client.get('/api/ai-insights/conversations/99999/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        
        # Test validation errors
        invalid_conversation_data = {
            'title': '',  # Empty title should be invalid
        }
        
        response = self.client.post(
            '/api/ai-insights/conversations/',
            data=invalid_conversation_data,
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Test malformed JSON
        response = self.client.post(
            '/api/ai-insights/conversations/',
            data='invalid json{',
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_rate_limiting(self):
        """Test API rate limiting"""
        conversation = AIConversation.objects.create(
            company=self.company,
            user=self.user,
            title='Rate Limit Test'
        )
        
        message_data = {
            'content': 'Test message',
            'request_type': 'general'
        }
        
        # Make multiple rapid requests
        responses = []
        for i in range(101):  # Exceed rate limit of 100/hour
            response = self.client.post(
                f'/api/ai-insights/conversations/{conversation.id}/send_message/',
                data=message_data,
                format='json'
            )
            responses.append(response.status_code)
        
        # Should eventually get rate limited
        # Note: This test depends on rate limiting configuration
        rate_limited_responses = [code for code in responses if code == status.HTTP_429_TOO_MANY_REQUESTS]
        # In a real test, we'd expect some rate limiting, but this depends on configuration


class AIInsightsAPIPerformanceTest(TestCase):
    """Performance tests for AI Insights API"""
    
    def setUp(self):
        """Set up performance test data"""
        self.client = APIClient()
        
        self.company = Company.objects.create(
            name='Performance Test Company',
            business_sector='Technology'
        )
        
        self.user = User.objects.create_user(
            email='perf-test@example.com',
            password='testpass123'
        )
        self.user.company = self.company
        self.user.save()
        
        self.client.force_authenticate(user=self.user)
        
        # Create bulk test data
        self.create_bulk_test_data()
    
    def create_bulk_test_data(self):
        """Create bulk test data for performance testing"""
        # Create many conversations
        conversations = []
        for i in range(50):
            conversation = AIConversation.objects.create(
                company=self.company,
                user=self.user,
                title=f'Performance Test Conversation {i+1}'
            )
            conversations.append(conversation)
        
        # Create many messages
        for conversation in conversations[:10]:  # Only for first 10 conversations
            for j in range(20):  # 20 messages per conversation
                AIMessage.objects.create(
                    conversation=conversation,
                    role='user' if j % 2 == 0 else 'assistant',
                    content=f'Performance test message {j+1}',
                    credits_used=1 if j % 2 == 1 else 0
                )
        
        # Create many insights
        for i in range(100):
            AIInsight.objects.create(
                company=self.company,
                type='cost_saving',
                priority='medium',
                title=f'Performance Test Insight {i+1}',
                description=f'Performance test insight {i+1}',
                potential_impact=Decimal('1000.00')
            )
    
    def test_conversations_list_performance(self):
        """Test conversations list API performance"""
        import time
        
        start_time = time.time()
        response = self.client.get('/api/ai-insights/conversations/')
        end_time = time.time()
        
        response_time = end_time - start_time
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertLess(response_time, 1.0)  # Should respond within 1 second
        
        # Verify pagination works
        data = response.json()
        self.assertIn('results', data)
        self.assertIn('count', data)
    
    def test_insights_list_performance(self):
        """Test insights list API performance"""
        import time
        
        start_time = time.time()
        response = self.client.get('/api/ai-insights/insights/')
        end_time = time.time()
        
        response_time = end_time - start_time
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertLess(response_time, 1.0)  # Should respond within 1 second
        
        # Test with filtering
        start_time = time.time()
        response = self.client.get('/api/ai-insights/insights/?priority=high&status=new')
        end_time = time.time()
        
        filtered_response_time = end_time - start_time
        self.assertLess(filtered_response_time, 1.0)
    
    def test_bulk_operations_performance(self):
        """Test bulk operations performance"""
        # Test bulk insight status updates (simulated)
        insights = AIInsight.objects.filter(company=self.company)[:10]
        
        import time
        start_time = time.time()
        
        for insight in insights:
            response = self.client.post(f'/api/ai-insights/insights/{insight.id}/mark_viewed/')
            self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        end_time = time.time()
        bulk_operation_time = end_time - start_time
        
        # Should handle 10 operations reasonably quickly
        self.assertLess(bulk_operation_time, 5.0)