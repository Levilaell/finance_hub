"""
Base test classes for integration tests
"""
from django.test import TestCase
from .test_fixtures import create_default_subscription_plans, create_default_categories


class IntegrationTestCase(TestCase):
    """Base test case for integration tests with common fixtures"""
    
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Create default data that all tests need
        cls.subscription_plans = create_default_subscription_plans()
        cls.default_categories = create_default_categories()
    
    def setUp(self):
        """Set up test dependencies"""
        super().setUp()
        # Ensure default plans and categories exist
        if not hasattr(self.__class__, 'subscription_plans'):
            self.__class__.subscription_plans = create_default_subscription_plans()
        if not hasattr(self.__class__, 'default_categories'):
            self.__class__.default_categories = create_default_categories()