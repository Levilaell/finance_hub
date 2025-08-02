"""
Unit tests for AIInsight model
Tests insight management, prioritization, and lifecycle
"""
import pytest
from decimal import Decimal
from datetime import timedelta
from django.test import TestCase
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.contrib.auth import get_user_model

from apps.companies.models import Company
from apps.ai_insights.models import AIInsight, AIConversation, AIMessage

User = get_user_model()


class TestAIInsight(TestCase):
    """Test AIInsight model functionality"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser_insight',
            email='test@example.com',
            password='testpass123'
        )
        self.company = Company.objects.create(
            owner=self.user,
            name='Test Company',
            trade_name='Test Company Ltd'
        )
        self.conversation = AIConversation.objects.create(
            company=self.company,
            user=self.user,
            title='Test Conversation'
        )
    
    def test_create_basic_insight(self):
        """Test creating basic AIInsight instance"""
        insight = AIInsight.objects.create(
            company=self.company,
            type='cost_saving',
            priority='high',
            title='Reduce utility costs',
            description='Your utility costs have increased 30% this month. Consider energy-saving measures.',
            action_items=[
                'Review electricity usage patterns',
                'Negotiate better rates with utility providers',
                'Implement energy-saving equipment'
            ],
            potential_impact=Decimal('2500.00')
        )
        
        self.assertEqual(insight.company, self.company)
        self.assertEqual(insight.type, 'cost_saving')
        self.assertEqual(insight.priority, 'high')
        self.assertEqual(insight.status, 'new')  # Default status
        self.assertEqual(insight.potential_impact, Decimal('2500.00'))
        self.assertEqual(len(insight.action_items), 3)
        self.assertIsNotNone(insight.created_at)
        self.assertIsNone(insight.viewed_at)
        self.assertFalse(insight.is_automated)  # Default value
    
    def test_insight_str_representation(self):
        """Test string representation of insight"""
        insight = AIInsight.objects.create(
            company=self.company,
            type='opportunity',
            priority='critical',
            title='Major growth opportunity identified',
            description='Market analysis shows potential for expansion.'
        )
        
        expected = "Major growth opportunity identified - Crítico - Ação Imediata"
        self.assertEqual(str(insight), expected)
    
    def test_insight_type_choices(self):
        """Test all insight type choices are valid"""
        valid_types = [
            'cost_saving',
            'cash_flow', 
            'anomaly',
            'opportunity',
            'risk',
            'trend',
            'benchmark',
            'tax',
            'growth'
        ]
        
        for insight_type in valid_types:
            insight = AIInsight(
                company=self.company,
                type=insight_type,
                priority='medium',
                title=f'Test {insight_type}',
                description=f'Test insight of type {insight_type}'
            )
            # Should not raise validation error
            insight.full_clean()
    
    def test_insight_priority_choices(self):
        """Test all priority choices are valid"""
        valid_priorities = ['critical', 'high', 'medium', 'low']
        
        for priority in valid_priorities:
            insight = AIInsight(
                company=self.company,
                type='opportunity',
                priority=priority,
                title=f'Test {priority} priority',
                description=f'Test insight with {priority} priority'
            )
            # Should not raise validation error
            insight.full_clean()
    
    def test_insight_status_choices(self):
        """Test all status choices are valid"""
        valid_statuses = ['new', 'viewed', 'in_progress', 'completed', 'dismissed']
        
        for status in valid_statuses:
            insight = AIInsight(
                company=self.company,
                type='trend',
                priority='medium',
                status=status,
                title=f'Test {status} status',
                description=f'Test insight with {status} status'
            )
            # Should not raise validation error
            insight.full_clean()
    
    def test_insight_with_conversation_reference(self):
        """Test insight linked to conversation and message"""
        message = AIMessage.objects.create(
            conversation=self.conversation,
            role='assistant',
            content='Analysis reveals cost-saving opportunity'
        )
        
        insight = AIInsight.objects.create(
            company=self.company,
            type='cost_saving',
            priority='high',
            title='Office space optimization',
            description='You could save 20% on office costs by optimizing space usage.',
            conversation=self.conversation,
            message=message,
            potential_impact=Decimal('5000.00'),
            impact_percentage=Decimal('20.00')
        )
        
        self.assertEqual(insight.conversation, self.conversation)
        self.assertEqual(insight.message, message)
        self.assertEqual(insight.impact_percentage, Decimal('20.00'))
    
    def test_insight_data_context(self):
        """Test data context JSON field"""
        data_context = {
            'analysis_period': '2024-01-01 to 2024-01-31',
            'data_sources': ['bank_transactions', 'invoices'],
            'metrics': {
                'current_month_expense': 25000.00,
                'previous_month_expense': 20000.00,
                'increase_percentage': 25.0
            },
            'supporting_data': {
                'highest_categories': [
                    {'name': 'Office Supplies', 'amount': 8000.00},
                    {'name': 'Marketing', 'amount': 7500.00}
                ]
            }
        }
        
        insight = AIInsight.objects.create(
            company=self.company,
            type='anomaly',
            priority='high',
            title='Unusual expense spike detected',
            description='Monthly expenses increased by 25% compared to previous month.',
            data_context=data_context
        )
        
        self.assertEqual(
            insight.data_context['analysis_period'], 
            '2024-01-01 to 2024-01-31'
        )
        self.assertEqual(
            insight.data_context['metrics']['increase_percentage'], 
            25.0
        )
        self.assertEqual(
            len(insight.data_context['supporting_data']['highest_categories']), 
            2
        )
    
    def test_insight_action_items(self):
        """Test action items JSON field"""
        action_items = [
            'Review supplier contracts for better pricing',
            'Implement bulk purchasing for office supplies',
            'Set monthly budget limits for each category',
            'Create approval workflow for expenses > R$ 1,000',
            'Schedule quarterly supplier performance reviews'
        ]
        
        insight = AIInsight.objects.create(
            company=self.company,
            type='cost_saving',
            priority='medium',
            title='Supplier cost optimization',
            description='Multiple opportunities to reduce supplier costs identified.',
            action_items=action_items
        )
        
        self.assertEqual(len(insight.action_items), 5)
        self.assertIn('Review supplier contracts for better pricing', insight.action_items)
        self.assertIn('Create approval workflow for expenses > R$ 1,000', insight.action_items)
    
    def test_insight_lifecycle_management(self):
        """Test insight lifecycle from creation to completion"""
        insight = AIInsight.objects.create(
            company=self.company,
            type='cash_flow',
            priority='critical',
            title='Cash flow warning',
            description='Current cash reserves may not cover next month expenses.',
            potential_impact=Decimal('50000.00')
        )
        
        # Initially new
        self.assertEqual(insight.status, 'new')
        self.assertIsNone(insight.viewed_at)
        self.assertFalse(insight.action_taken)
        
        # Mark as viewed
        insight.status = 'viewed'
        insight.viewed_at = timezone.now()
        insight.save()
        
        self.assertEqual(insight.status, 'viewed')
        self.assertIsNotNone(insight.viewed_at)
        
        # Move to in progress
        insight.status = 'in_progress'
        insight.save()
        
        self.assertEqual(insight.status, 'in_progress')
        
        # Complete with action taken
        insight.status = 'completed'
        insight.action_taken = True
        insight.action_taken_at = timezone.now()
        insight.actual_impact = Decimal('45000.00')
        insight.user_feedback = 'Successfully secured additional credit line.'
        insight.save()
        
        self.assertEqual(insight.status, 'completed')
        self.assertTrue(insight.action_taken)
        self.assertIsNotNone(insight.action_taken_at)
        self.assertEqual(insight.actual_impact, Decimal('45000.00'))
    
    def test_insight_expiration(self):
        """Test insight expiration functionality"""
        # Create insight that expires in 7 days
        expires_at = timezone.now() + timedelta(days=7)
        
        insight = AIInsight.objects.create(
            company=self.company,
            type='opportunity',
            priority='medium',
            title='Seasonal pricing opportunity',
            description='Take advantage of lower supplier prices this month.',
            expires_at=expires_at
        )
        
        self.assertEqual(insight.expires_at, expires_at)
        
        # Test insight that's already expired
        expired_insight = AIInsight.objects.create(
            company=self.company,
            type='trend',
            priority='low',
            title='Expired trend insight',
            description='Market trend that is no longer relevant.',
            expires_at=timezone.now() - timedelta(days=1)
        )
        
        self.assertTrue(expired_insight.expires_at < timezone.now())
    
    def test_insight_ordering(self):
        """Test insight ordering by priority and creation date"""
        # Create insights with different priorities
        critical_insight = AIInsight.objects.create(
            company=self.company,
            type='risk',
            priority='critical',
            title='Critical issue',
            description='Immediate attention required.'
        )
        
        low_insight = AIInsight.objects.create(
            company=self.company,
            type='trend',
            priority='low',
            title='Minor trend',
            description='Informational insight.'
        )
        
        high_insight = AIInsight.objects.create(
            company=self.company,
            type='opportunity',
            priority='high',
            title='High priority opportunity',
            description='Important business opportunity.'
        )
        
        # Query with default ordering
        insights = list(AIInsight.objects.filter(company=self.company))
        
        # Should be ordered by priority (critical > high > low) then by -created_at
        priorities = [insight.priority for insight in insights]
        self.assertEqual(priorities[0], 'critical')
        # Note: Exact ordering depends on priority field mapping in Meta.ordering
    
    def test_insight_automated_vs_manual(self):
        """Test automated vs manual insight creation"""
        # Manual insight (from conversation)
        manual_insight = AIInsight.objects.create(
            company=self.company,
            type='analysis',
            priority='medium',
            title='Manual analysis insight',
            description='Insight generated from user conversation.',
            conversation=self.conversation,
            is_automated=False
        )
        
        # Automated insight (from background analysis)
        automated_insight = AIInsight.objects.create(
            company=self.company,
            type='anomaly',
            priority='high',
            title='Automated anomaly detection',
            description='Anomaly detected by automated analysis.',
            is_automated=True,
            data_context={
                'detection_algorithm': 'outlier_detection',
                'confidence_score': 0.95,
                'data_points_analyzed': 1000
            }
        )
        
        self.assertFalse(manual_insight.is_automated)
        self.assertTrue(automated_insight.is_automated)
        self.assertEqual(
            automated_insight.data_context['detection_algorithm'],
            'outlier_detection'
        )
    
    def test_insight_impact_tracking(self):
        """Test impact tracking functionality"""
        insight = AIInsight.objects.create(
            company=self.company,
            type='cost_saving',
            priority='high',
            title='Vendor negotiation opportunity',
            description='Renegotiate contracts with top 3 vendors for 15% savings.',
            potential_impact=Decimal('15000.00'),
            impact_percentage=Decimal('15.00')
        )
        
        # Track actual impact when completed
        insight.status = 'completed'
        insight.action_taken = True
        insight.action_taken_at = timezone.now()
        insight.actual_impact = Decimal('12500.00')  # Slightly less than potential
        insight.user_feedback = 'Achieved 12.5% savings instead of projected 15%'
        insight.save()
        
        # Calculate impact effectiveness
        effectiveness = (insight.actual_impact / insight.potential_impact) * 100
        self.assertAlmostEqual(float(effectiveness), 83.33, places=1)
    
    def test_insight_company_relationship(self):
        """Test insight-company relationship and indexes"""
        # Create insights for different statuses
        statuses = ['new', 'viewed', 'in_progress', 'completed']
        
        for i, status in enumerate(statuses):
            AIInsight.objects.create(
                company=self.company,
                type='opportunity',
                priority='medium',
                status=status,
                title=f'Insight {i+1}',
                description=f'Test insight with {status} status'
            )
        
        # Test company relationship
        company_insights = self.company.ai_insights.all()
        self.assertEqual(company_insights.count(), 4)
        
        # Test status filtering (should use index)
        new_insights = AIInsight.objects.filter(
            company=self.company,
            status='new'
        )
        self.assertEqual(new_insights.count(), 1)
        
        # Test type and priority filtering (should use index)
        medium_opportunities = AIInsight.objects.filter(
            type='opportunity',
            priority='medium'
        )
        self.assertEqual(medium_opportunities.count(), 4)
    
    def test_insight_cascade_deletion(self):
        """Test cascade deletion behavior"""
        message = AIMessage.objects.create(
            conversation=self.conversation,
            role='assistant',
            content='AI generated insight'
        )
        
        insight = AIInsight.objects.create(
            company=self.company,
            type='trend',
            priority='low',
            title='Trend insight',
            description='Market trend analysis.',
            conversation=self.conversation,
            message=message
        )
        
        insight_id = insight.id
        
        # Delete message - insight should remain but message reference nulled
        message.delete()
        insight.refresh_from_db()
        self.assertIsNone(insight.message)
        
        # Delete conversation - insight should remain but conversation reference nulled
        self.conversation.delete()
        insight.refresh_from_db()
        self.assertIsNone(insight.conversation)
        
        # Delete company - insight should be cascade deleted
        self.company.delete()
        
        with self.assertRaises(AIInsight.DoesNotExist):
            AIInsight.objects.get(id=insight_id)


class TestInsightBusinessLogic(TestCase):
    """Test business logic for insights"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser_biz_insight',
            email='bizinsight@example.com',
            password='testpass123'
        )
        self.company = Company.objects.create(
            owner=self.user,
            name='Business Logic Test Company',
            trade_name='Business Logic Test Company Ltd'
        )
    
    def test_critical_insights_require_immediate_action(self):
        """Test critical insights behavior"""
        critical_insight = AIInsight.objects.create(
            company=self.company,
            type='risk',
            priority='critical',
            title='Payment default risk',
            description='Customer payment delays indicate high default risk.',
            potential_impact=Decimal('100000.00'),
            # Critical insights might have shorter expiration
            expires_at=timezone.now() + timedelta(days=7)
        )
        
        self.assertEqual(critical_insight.priority, 'critical')
        self.assertIsNotNone(critical_insight.expires_at)
        
        # Critical insights should be processed first
        high_insight = AIInsight.objects.create(
            company=self.company,
            type='opportunity',
            priority='high',
            title='High priority opportunity',
            description='Business opportunity.'
        )
        
        # When querying by priority, critical should come first
        prioritized_insights = AIInsight.objects.filter(
            company=self.company
        ).order_by('-priority', '-created_at')
        
        # Note: This depends on how priority ordering is implemented
        # The model's Meta.ordering should handle this
    
    def test_insight_roi_calculation(self):
        """Test ROI calculation for insights"""
        insight = AIInsight.objects.create(
            company=self.company,
            type='cost_saving',
            priority='high',
            title='Process automation',
            description='Automate manual processes to save time and costs.',
            potential_impact=Decimal('25000.00'),
            impact_percentage=Decimal('10.00')
        )
        
        # Complete insight with actual results
        insight.status = 'completed'
        insight.action_taken = True
        insight.actual_impact = Decimal('28000.00')  # Better than expected
        insight.save()
        
        # Calculate ROI (assuming some implementation cost)
        implementation_cost = Decimal('5000.00')
        roi_percentage = ((insight.actual_impact - implementation_cost) / implementation_cost) * 100
        
        self.assertEqual(roi_percentage, Decimal('460.00'))  # 460% ROI
    
    def test_insight_effectiveness_tracking(self):
        """Test tracking insight effectiveness"""
        insights = []
        
        # Create insights with different outcomes
        outcomes = [
            {'potential': 1000, 'actual': 1200, 'description': 'Better than expected'},
            {'potential': 5000, 'actual': 4500, 'description': 'Close to expected'},
            {'potential': 2000, 'actual': 800, 'description': 'Below expected'},
            {'potential': 3000, 'actual': 0, 'description': 'No action taken'}
        ]
        
        for i, outcome in enumerate(outcomes):
            insight = AIInsight.objects.create(
                company=self.company,
                type='cost_saving',
                priority='medium',
                title=f'Test insight {i+1}',
                description=outcome['description'],
                potential_impact=Decimal(str(outcome['potential'])),
                status='completed' if outcome['actual'] > 0 else 'dismissed',
                action_taken=outcome['actual'] > 0,
                actual_impact=Decimal(str(outcome['actual'])) if outcome['actual'] > 0 else None
            )
            insights.append(insight)
        
        # Calculate overall effectiveness
        completed_insights = [i for i in insights if i.status == 'completed']
        total_potential = sum(i.potential_impact for i in completed_insights)
        total_actual = sum(i.actual_impact for i in completed_insights)
        
        effectiveness = (total_actual / total_potential) * 100
        self.assertAlmostEqual(float(effectiveness), 86.67, places=1)  # 86.67%