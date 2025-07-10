"""
Test Performance Metrics functionality for AI & Rules
Tests for CategoryPerformance model and performance tracking
"""
from apps.banking.models import BankAccount, BankProvider, Transaction, TransactionCategory
from apps.categories.models import CategoryPerformance, CategoryRule, CategorizationLog
from apps.categories.services import AICategorizationService, CategoryAnalyticsService
from apps.companies.models import Company, SubscriptionPlan
from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.utils import timezone
from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import Mock, patch

User = get_user_model()


@override_settings(CELERY_TASK_ALWAYS_EAGER=True, CELERY_TASK_EAGER_PROPAGATES=True)
class CategoryPerformanceModelTests(TestCase):
    """Test CategoryPerformance model functionality"""
    
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
            enable_ai_categorization=True
        )
        
        # Create category
        self.category = TransactionCategory.objects.create(
            name='Test Category',
            slug='test-category',
            category_type='expense'
        )
        
        # Create performance metrics
        self.performance = CategoryPerformance.objects.create(
            company=self.company,
            category=self.category,
            period_start=date.today() - timedelta(days=30),
            period_end=date.today(),
            total_predictions=100,
            correct_predictions=85,
            false_positives=10,
            false_negatives=15
        )
    
    def test_performance_metrics_creation(self):
        """Test creating performance metrics"""
        self.assertEqual(self.performance.company, self.company)
        self.assertEqual(self.performance.category, self.category)
        self.assertEqual(self.performance.total_predictions, 100)
        self.assertEqual(self.performance.correct_predictions, 85)
        self.assertEqual(self.performance.false_positives, 10)
        self.assertEqual(self.performance.false_negatives, 15)
    
    def test_update_metrics_calculation(self):
        """Test that update_metrics calculates metrics correctly"""
        # Reset metrics to known values
        self.performance.total_predictions = 100
        self.performance.correct_predictions = 80
        self.performance.false_positives = 15
        self.performance.false_negatives = 20
        self.performance.accuracy = 0.0
        self.performance.precision = 0.0
        self.performance.recall = 0.0
        self.performance.f1_score = 0.0
        
        # Update metrics
        self.performance.update_metrics()
        
        # Check calculated values
        self.assertEqual(self.performance.accuracy, 0.8)  # 80/100
        self.assertEqual(self.performance.precision, 80/95)  # 80/(80+15)
        self.assertEqual(self.performance.recall, 80/100)  # 80/(80+20)
        
        # Calculate expected F1 score
        expected_f1 = 2 * (self.performance.precision * self.performance.recall) / (self.performance.precision + self.performance.recall)
        self.assertAlmostEqual(self.performance.f1_score, expected_f1, places=5)
    
    def test_update_metrics_edge_cases(self):
        """Test update_metrics with edge cases"""
        # Test with zero predictions
        self.performance.total_predictions = 0
        self.performance.correct_predictions = 0
        self.performance.false_positives = 0
        self.performance.false_negatives = 0
        self.performance.update_metrics()
        
        self.assertEqual(self.performance.accuracy, 0.0)
        self.assertEqual(self.performance.precision, 0.0)
        self.assertEqual(self.performance.recall, 0.0)
        self.assertEqual(self.performance.f1_score, 0.0)
    
    def test_performance_string_representation(self):
        """Test string representation of performance metrics"""
        self.performance.update_metrics()
        str_repr = str(self.performance)
        self.assertIn(self.category.name, str_repr)
        self.assertIn('accuracy', str_repr)
    
    def test_unique_constraint(self):
        """Test unique constraint on company, category, and period"""
        with self.assertRaises(Exception):
            CategoryPerformance.objects.create(
                company=self.company,
                category=self.category,
                period_start=self.performance.period_start,
                period_end=self.performance.period_end,
                total_predictions=50,
                correct_predictions=40
            )


class AICategorizationServicePerformanceTests(TestCase):
    """Test performance tracking in AI categorization service"""
    
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
            enable_ai_categorization=True
        )
        self.user.company = self.company
        self.user.save()
        
        # Create bank provider and account
        self.bank_provider = BankProvider.objects.create(
            name='Test Bank',
            code='test-bank',
            is_active=True
        )
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
        
        # Create test transaction
        self.transaction = Transaction.objects.create(
            bank_account=self.bank_account,
            external_id='test_trans',
            amount=-100.00,
            description='Test transaction',
            transaction_date=timezone.now(),
            transaction_type='debit'
        )
        
        # Create AI service without OpenAI key (it will be disabled)
        with patch('apps.categories.services.settings.OPENAI_API_KEY', None):
            self.ai_service = AICategorizationService()
    
    def test_ai_performance_metrics_update(self):
        """Test that AI categorization updates performance metrics"""
        # Clean up any existing performance metrics
        CategoryPerformance.objects.all().delete()
        
        # Test that no performance metrics exist initially
        self.assertEqual(CategoryPerformance.objects.count(), 0)
        
        # Simulate user feedback (this should trigger performance metrics update)
        CategorizationLog.objects.create(
            transaction=self.transaction,
            method='ai',
            suggested_category=self.food_category,
            confidence_score=0.85
        )
        
        # Call learn_from_feedback to trigger performance update
        self.ai_service.learn_from_feedback(self.transaction, self.food_category, self.user)
        
        # Check that performance metrics were created
        self.assertEqual(CategoryPerformance.objects.count(), 1)
        
        performance = CategoryPerformance.objects.first()
        self.assertEqual(performance.company, self.company)
        self.assertEqual(performance.category, self.food_category)
        self.assertEqual(performance.total_predictions, 1)
        self.assertEqual(performance.correct_predictions, 1)
    
    def test_ai_performance_metrics_false_positive(self):
        """Test performance metrics for false positive AI predictions"""
        # Clean up any existing performance metrics
        CategoryPerformance.objects.all().delete()
        
        # Create categorization log with incorrect prediction
        CategorizationLog.objects.create(
            transaction=self.transaction,
            method='ai',
            suggested_category=self.transport_category,
            confidence_score=0.75
        )
        
        # User provides correct feedback (different from AI prediction)
        self.ai_service.learn_from_feedback(self.transaction, self.food_category, self.user)
        
        # Check that false positive was recorded for transport category
        transport_performance = CategoryPerformance.objects.filter(category=self.transport_category).first()
        self.assertIsNotNone(transport_performance)
        self.assertEqual(transport_performance.false_positives, 1)
        
        # Check that false negative was recorded for food category
        food_performance = CategoryPerformance.objects.filter(category=self.food_category).first()
        self.assertIsNotNone(food_performance)
        self.assertEqual(food_performance.false_negatives, 1)
    
    def test_get_performance_metrics(self):
        """Test getting performance metrics summary"""
        # Create some performance data
        CategoryPerformance.objects.create(
            company=self.company,
            category=self.food_category,
            period_start=date.today() - timedelta(days=30),
            period_end=date.today(),
            total_predictions=50,
            correct_predictions=45,
            false_positives=3,
            false_negatives=2
        )
        
        CategoryPerformance.objects.create(
            company=self.company,
            category=self.transport_category,
            period_start=date.today() - timedelta(days=30),
            period_end=date.today(),
            total_predictions=30,
            correct_predictions=28,
            false_positives=1,
            false_negatives=1
        )
        
        # Update metrics
        for perf in CategoryPerformance.objects.all():
            perf.update_metrics()
        
        # Get performance summary
        metrics = self.ai_service.get_performance_metrics(self.company)
        
        self.assertEqual(metrics['total_categories'], 2)
        self.assertEqual(metrics['summary']['total_predictions'], 80)
        self.assertEqual(metrics['summary']['correct_predictions'], 73)
        self.assertAlmostEqual(metrics['summary']['overall_accuracy'], 73/80, places=5)
        
        # Check category breakdown
        self.assertEqual(len(metrics['category_breakdown']), 2)
        
        food_category_metrics = next(
            (item for item in metrics['category_breakdown'] if item['category'] == 'Alimentação'),
            None
        )
        self.assertIsNotNone(food_category_metrics)
        self.assertEqual(food_category_metrics['total_predictions'], 50)
        self.assertEqual(food_category_metrics['correct_predictions'], 45)
        self.assertEqual(food_category_metrics['accuracy'], 0.9)
    
    def test_get_performance_metrics_empty(self):
        """Test getting performance metrics when no data exists"""
        metrics = self.ai_service.get_performance_metrics(self.company)
        
        self.assertEqual(metrics['total_categories'], 0)
        self.assertEqual(metrics['average_accuracy'], 0.0)
        self.assertEqual(metrics['summary']['total_predictions'], 0)
        self.assertEqual(len(metrics['category_breakdown']), 0)


class RulePerformanceTests(TestCase):
    """Test performance tracking for rule-based categorization"""
    
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
            enable_ai_categorization=True
        )
        self.user.company = self.company
        self.user.save()
        
        # Create bank provider and account
        self.bank_provider = BankProvider.objects.create(
            name='Test Bank',
            code='test-bank',
            is_active=True
        )
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
        
        # Create rule
        self.rule = CategoryRule.objects.create(
            company=self.company,
            category=self.food_category,
            name='Food Rule',
            rule_type='keyword',
            conditions={'keywords': ['restaurant', 'food']},
            created_by=self.user
        )
        
        # Create AI service without OpenAI key (it will be disabled)
        with patch('apps.categories.services.settings.OPENAI_API_KEY', None):
            self.ai_service = AICategorizationService()
    
    def test_rule_performance_metrics_update(self):
        """Test that rule application updates performance metrics"""
        # Create transaction that matches rule
        transaction = Transaction.objects.create(
            bank_account=self.bank_account,
            external_id='test_trans',
            amount=-50.00,
            description='Restaurant payment',
            transaction_date=timezone.now(),
            transaction_type='debit'
        )
        
        # Clean up any existing performance metrics
        CategoryPerformance.objects.all().delete()
        
        # Test that no performance metrics exist initially
        self.assertEqual(CategoryPerformance.objects.count(), 0)
        
        # Apply rule (this should trigger performance metrics update)
        with patch.object(self.ai_service, '_ai_categorize', return_value=None):
            result = self.ai_service.categorize_transaction(transaction)
        
        # Check that rule was applied
        self.assertEqual(result['method'], 'rule')
        self.assertEqual(result['rule'], self.rule)
        
        # Check that performance metrics were created
        self.assertEqual(CategoryPerformance.objects.count(), 1)
        
        performance = CategoryPerformance.objects.first()
        self.assertEqual(performance.company, self.company)
        self.assertEqual(performance.category, self.food_category)
        self.assertEqual(performance.total_predictions, 1)
        self.assertEqual(performance.correct_predictions, 1)
    
    def test_get_rule_performance_summary(self):
        """Test getting rule performance summary"""
        # Create some categorization logs for rules
        transaction1 = Transaction.objects.create(
            bank_account=self.bank_account,
            external_id='trans1',
            amount=-50.00,
            description='Restaurant 1',
            transaction_date=timezone.now(),
            transaction_type='debit'
        )
        
        transaction2 = Transaction.objects.create(
            bank_account=self.bank_account,
            external_id='trans2',
            amount=-30.00,
            description='Food delivery',
            transaction_date=timezone.now(),
            transaction_type='debit'
        )
        
        # Create categorization logs
        CategorizationLog.objects.create(
            transaction=transaction1,
            method='rule',
            suggested_category=self.food_category,
            confidence_score=1.0,
            rule_used=self.rule,
            was_accepted=True
        )
        
        CategorizationLog.objects.create(
            transaction=transaction2,
            method='rule',
            suggested_category=self.food_category,
            confidence_score=1.0,
            rule_used=self.rule,
            was_accepted=False
        )
        
        # Get rule performance summary
        summary = self.ai_service.get_rule_performance_summary(self.company)
        
        self.assertEqual(summary['total_rules'], 1)
        self.assertEqual(summary['total_rule_applications'], 2)
        self.assertEqual(summary['correct_rule_applications'], 1)
        self.assertEqual(summary['rule_accuracy'], 0.5)
        
        # Check rule breakdown
        self.assertEqual(len(summary['rule_breakdown']), 1)
        rule_metrics = summary['rule_breakdown'][0]
        self.assertEqual(rule_metrics['rule_name'], 'Food Rule')
        self.assertEqual(rule_metrics['total_applications'], 2)
        self.assertEqual(rule_metrics['correct_applications'], 1)
        self.assertEqual(rule_metrics['accuracy'], 0.5)
    
    def test_get_rule_performance_summary_empty(self):
        """Test getting rule performance summary when no data exists"""
        summary = self.ai_service.get_rule_performance_summary(self.company)
        
        self.assertEqual(summary['total_rules'], 1)  # Rule exists but no applications
        self.assertEqual(summary['total_rule_applications'], 0)
        self.assertEqual(summary['correct_rule_applications'], 0)
        self.assertEqual(summary['rule_accuracy'], 0.0)


class CategoryAnalyticsServicePerformanceTests(TestCase):
    """Test CategoryAnalyticsService with performance metrics"""
    
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
            enable_ai_categorization=True
        )
        
        # Create categories
        self.food_category = TransactionCategory.objects.create(
            name='Alimentação',
            slug='alimentacao',
            category_type='expense'
        )
        
        self.analytics_service = CategoryAnalyticsService()
    
    def test_calculate_accuracy_metrics_with_performance_data(self):
        """Test accuracy calculation using CategoryPerformance data"""
        # Create performance metrics
        CategoryPerformance.objects.create(
            company=self.company,
            category=self.food_category,
            period_start=date.today() - timedelta(days=30),
            period_end=date.today(),
            total_predictions=100,
            correct_predictions=85,
            false_positives=10,
            false_negatives=5
        )
        
        # Update metrics
        for perf in CategoryPerformance.objects.all():
            perf.update_metrics()
        
        # Calculate accuracy metrics
        metrics = self.analytics_service.calculate_accuracy_metrics(self.company)
        
        self.assertEqual(metrics['total_categorizations'], 100)
        self.assertEqual(metrics['accuracy'], 0.85)
        
        # Check performance summary
        perf_summary = metrics['performance_summary']
        self.assertEqual(perf_summary['total_predictions'], 100)
        self.assertEqual(perf_summary['correct_predictions'], 85)
        self.assertEqual(perf_summary['false_positives'], 10)
        self.assertEqual(perf_summary['false_negatives'], 5)
        self.assertAlmostEqual(perf_summary['precision'], 85/95, places=5)  # 85/(85+10)
        self.assertAlmostEqual(perf_summary['recall'], 85/90, places=5)  # 85/(85+5)
    
    def test_calculate_accuracy_metrics_fallback_to_logs(self):
        """Test accuracy calculation fallback to logs when no performance data exists"""
        # Create categorization logs (no performance metrics)
        from apps.banking.models import BankAccount, BankProvider, Transaction
        
        # Create bank provider and account
        bank_provider = BankProvider.objects.create(
            name='Test Bank',
            code='test-bank',
            is_active=True
        )
        bank_account = BankAccount.objects.create(
            company=self.company,
            bank_provider=bank_provider,
            account_type='checking',
            agency='0001',
            account_number='12345',
            current_balance=1000.00
        )
        
        # Create transactions
        transaction1 = Transaction.objects.create(
            bank_account=bank_account,
            external_id='trans1',
            amount=-50.00,
            description='Test transaction 1',
            transaction_date=timezone.now(),
            transaction_type='debit'
        )
        
        transaction2 = Transaction.objects.create(
            bank_account=bank_account,
            external_id='trans2',
            amount=-30.00,
            description='Test transaction 2',
            transaction_date=timezone.now(),
            transaction_type='debit'
        )
        
        # Create categorization logs
        CategorizationLog.objects.create(
            transaction=transaction1,
            method='ai',
            suggested_category=self.food_category,
            confidence_score=0.8,
            was_accepted=True
        )
        
        CategorizationLog.objects.create(
            transaction=transaction2,
            method='ai',
            suggested_category=self.food_category,
            confidence_score=0.6,
            was_accepted=False
        )
        
        # Calculate accuracy metrics (should fallback to logs)
        metrics = self.analytics_service.calculate_accuracy_metrics(self.company)
        
        self.assertEqual(metrics['total_categorizations'], 2)
        self.assertEqual(metrics['accuracy'], 0.5)  # 1 correct out of 2
        self.assertEqual(metrics['ai_accuracy'], 0.5)
        
        # Check performance summary fallback
        perf_summary = metrics['performance_summary']
        self.assertEqual(perf_summary['total_predictions'], 2)
        self.assertEqual(perf_summary['correct_predictions'], 1)
        self.assertEqual(perf_summary['precision'], 0.5)
        self.assertEqual(perf_summary['recall'], 0.5)
    
    def test_calculate_accuracy_metrics_empty_data(self):
        """Test accuracy calculation with no data"""
        metrics = self.analytics_service.calculate_accuracy_metrics(self.company)
        
        self.assertEqual(metrics['total_categorizations'], 0)
        self.assertEqual(metrics['accuracy'], 0.0)
        self.assertEqual(metrics['ai_accuracy'], 0.0)
        self.assertEqual(metrics['rule_accuracy'], 0.0)
        
        # Check performance summary
        perf_summary = metrics['performance_summary']
        self.assertEqual(perf_summary['total_predictions'], 0)
        self.assertEqual(perf_summary['correct_predictions'], 0)
        self.assertEqual(perf_summary['precision'], 0.0)
        self.assertEqual(perf_summary['recall'], 0.0)