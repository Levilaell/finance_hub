"""
Base test utilities for notification tests
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from apps.companies.models import Company
from datetime import timedelta

User = get_user_model()


class NotificationTestCase(TestCase):
    """Base test case with company and user setup"""
    
    @classmethod
    def setUpClass(cls):
        """Set up test database with required data"""
        super().setUpClass()
        cls.test_plan = None  # We'll handle this per test if needed
    
    def setUp(self):
        """Set up test data for each test"""
        super().setUp()
        
        # Create test user
        self.user = User.objects.create_user(
            email="test@example.com",
            username="testuser",
            password="testpass123"
        )
        
        # Create company with all required fields for the old schema
        self.company = self._create_test_company(self.user)
    
    def _create_test_company(self, owner, name="Test Company"):
        """Create a company with all required fields"""
        company_data = {
            'owner': owner,
            'name': name,
        }
        
        # Add fields that might be required in the database but not in the model
        # These are based on the database schema inspection
        additional_fields = {
            'trade_name': f'{name} Trade',
            'company_type': 'other',
            'business_sector': 'other',
            'email': '',
            'phone': '',
            'website': '',
            'address_street': '',
            'address_number': '',
            'address_complement': '',
            'address_neighborhood': '',
            'address_city': '',
            'address_state': '',
            'address_zipcode': '',
            'employee_count': 1,
            'subscription_status': 'trial',
            'billing_cycle': 'monthly',
            'current_month_transactions': 0,
            'current_month_ai_requests': 0,
            'last_usage_reset': timezone.now(),
            'notified_80_percent': False,
            'notified_90_percent': False,
            'primary_color': '#000000',
            'currency': 'USD',
            'fiscal_year_start': '01',
            'enable_ai_categorization': True,
            'auto_categorize_threshold': 0.8,
            'enable_notifications': True,
            'enable_email_reports': True,
            'is_active': True,
            'trial_ends_at': timezone.now() + timedelta(days=14),
        }
        
        # Try to create with minimal fields first
        try:
            return Company.objects.create(**company_data)
        except Exception:
            # If that fails, use all fields
            company_data.update(additional_fields)
            
            # Check which fields actually exist on the model
            model_fields = {f.name for f in Company._meta.get_fields()}
            final_data = {k: v for k, v in company_data.items() if k in model_fields}
            
            # For fields that exist in DB but not in model, we'll handle them separately
            company = Company(**final_data)
            
            # Save without calling full_clean to bypass model validation
            company.save(force_insert=True)
            
            # Now update any additional fields directly in the database if needed
            missing_fields = set(company_data.keys()) - model_fields
            if missing_fields:
                # Use raw SQL to update fields that exist in DB but not in model
                from django.db import connection
                
                for field in missing_fields:
                    if field in additional_fields:
                        with connection.cursor() as cursor:
                            cursor.execute(
                                f"UPDATE companies SET {field} = %s WHERE id = %s",
                                [additional_fields[field], company.id]
                            )
            
            return company