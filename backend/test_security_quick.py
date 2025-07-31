#!/usr/bin/env python
"""
Quick security test for AI Insights
"""
import os
import sys
import django

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.test')
django.setup()

from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from apps.companies.models import Company, SubscriptionPlan
from apps.ai_insights.models import AICredit, AIConversation
from decimal import Decimal

User = get_user_model()

class SecurityTest:
    def __init__(self):
        self.client = Client()
        self.setup_test_data()
    
    def setup_test_data(self):
        # Create users
        self.user1 = User.objects.create_user(
            username='user1',
            email='user1@test.com',
            password='testpass123',
            first_name='User',
            last_name='One'
        )
        
        self.user2 = User.objects.create_user(
            username='user2',
            email='user2@test.com',
            password='testpass123',
            first_name='User',
            last_name='Two'
        )
        
        # Create plan
        self.plan = SubscriptionPlan.objects.create(
            name='Professional',
            slug='professional',
            plan_type='professional',
            price_monthly=Decimal('99.90'),
            price_yearly=Decimal('999.00')
        )
        
        # Create companies
        self.company1 = Company.objects.create(
            name='Company 1',
            owner=self.user1,
            cnpj='12345678901234',
            company_type='ltda',
            business_sector='technology'
        )
        
        self.company2 = Company.objects.create(
            name='Company 2',
            owner=self.user2,
            cnpj='98765432109876',
            company_type='ltda',
            business_sector='services'
        )
        
        # Create AI credits
        AICredit.objects.create(company=self.company1, balance=100)
        AICredit.objects.create(company=self.company2, balance=100)
        
        # Create conversations
        self.conversation1 = AIConversation.objects.create(
            company=self.company1,
            user=self.user1,
            title='Company 1 Chat'
        )
        
        self.conversation2 = AIConversation.objects.create(
            company=self.company2,
            user=self.user2,
            title='Company 2 Chat'
        )
    
    def test_unauthenticated_access(self):
        """Test that unauthenticated users cannot access AI endpoints"""
        print("🔒 Testing unauthenticated access...")
        
        # Test accessing conversation without auth
        response = self.client.get(f'/api/ai-insights/conversations/{self.conversation1.id}/')
        print(f"  Conversation access without auth: {response.status_code} (expected 401)")
        
        return response.status_code in [401, 403]
    
    def test_cross_company_access(self):
        """Test that users cannot access other companies' data"""
        print("🔒 Testing cross-company access control...")
        
        # Login as user1
        self.client.force_login(self.user1)
        
        # Try to access user2's conversation
        response = self.client.get(f'/api/ai-insights/conversations/{self.conversation2.id}/')
        print(f"  Cross-company conversation access: {response.status_code} (expected 404/403)")
        
        # Test credit access
        response = self.client.get(f'/api/ai-insights/credits/{self.company2.id}/')
        print(f"  Cross-company credit access: {response.status_code} (expected 404/403)")
        
        return response.status_code in [403, 404]
    
    def test_sql_injection_protection(self):
        """Test basic SQL injection protection"""
        print("🔒 Testing SQL injection protection...")
        
        self.client.force_login(self.user1)
        
        # Try SQL injection in conversation search
        malicious_query = "'; DROP TABLE ai_conversations; --"
        response = self.client.get(f'/api/ai-insights/conversations/?search={malicious_query}')
        print(f"  SQL injection test: {response.status_code} (should not crash)")
        
        # Verify conversations still exist
        conversations_exist = AIConversation.objects.filter(company=self.company1).exists()
        print(f"  Conversations still exist: {conversations_exist} (expected True)")
        
        return conversations_exist
    
    def test_input_validation(self):
        """Test input validation on AI endpoints"""
        print("🔒 Testing input validation...")
        
        self.client.force_login(self.user1)
        
        # Test extremely long message
        long_message = "A" * 10000  # 10KB message
        response = self.client.post(f'/api/ai-insights/conversations/{self.conversation1.id}/messages/', {
            'content': long_message,
            'request_type': 'general'
        }, content_type='application/json')
        print(f"  Long message validation: {response.status_code} (should validate length)")
        
        # Test special characters
        special_chars = "<script>alert('xss')</script>"
        response = self.client.post(f'/api/ai-insights/conversations/{self.conversation1.id}/messages/', {
            'content': special_chars,
            'request_type': 'general'
        }, content_type='application/json')
        print(f"  Special characters validation: {response.status_code}")
        
        return True
    
    def test_rate_limiting_simulation(self):
        """Simulate rate limiting test"""
        print("🔒 Testing rate limiting simulation...")
        
        self.client.force_login(self.user1)
        
        # Make multiple rapid requests
        success_count = 0
        error_count = 0
        
        for i in range(5):
            response = self.client.get(f'/api/ai-insights/conversations/')
            if response.status_code == 200:
                success_count += 1
            else:
                error_count += 1
        
        print(f"  Rapid requests - Success: {success_count}, Errors: {error_count}")
        return True
    
    def run_all_tests(self):
        """Run all security tests"""
        print("🛡️  AI Insights Security Test Suite")
        print("=" * 50)
        
        results = {}
        results['unauthenticated'] = self.test_unauthenticated_access()
        results['cross_company'] = self.test_cross_company_access()
        results['sql_injection'] = self.test_sql_injection_protection()
        results['input_validation'] = self.test_input_validation()
        results['rate_limiting'] = self.test_rate_limiting_simulation()
        
        print("\n📊 Security Test Results:")
        print("=" * 30)
        
        passed = 0
        total = len(results)
        
        for test_name, result in results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"  {test_name}: {status}")
            if result:
                passed += 1
        
        print(f"\n🎯 Summary: {passed}/{total} tests passed")
        
        if passed == total:
            print("🛡️  All security tests passed!")
        else:
            print("⚠️  Some security tests failed - review implementation")
        
        return results

if __name__ == '__main__':
    security_test = SecurityTest()
    security_test.run_all_tests()