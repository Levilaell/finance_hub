"""
Comprehensive tests for Companies app user management
Testing user invitations, role management, and team member operations
"""
import json
from decimal import Decimal
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta

from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core import mail
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework import status

from apps.companies.models import SubscriptionPlan, Company, CompanyUser
from apps.companies.serializers import CompanyUserSerializer

User = get_user_model()


class InviteUserViewTest(TestCase):
    """Test InviteUserView functionality"""
    
    def setUp(self):
        """Set up test data"""
        self.client = APIClient()
        
        # Create subscription plans
        self.starter_plan = SubscriptionPlan.objects.create(
            name='Starter Plan',
            slug='starter',
            plan_type='starter',
            price_monthly=Decimal('29.90'),
            price_yearly=Decimal('299.00'),
            max_users=1  # Limited users
        )
        
        self.enterprise_plan = SubscriptionPlan.objects.create(
            name='Enterprise Plan',
            slug='enterprise',
            plan_type='enterprise',
            price_monthly=Decimal('199.90'),
            price_yearly=Decimal('1999.00'),
            max_users=10  # More users allowed
        )
        
        # Create owner user
        self.owner_user = User.objects.create_user(
            username='testuser', email='test@example.com',
            password='testpass123',
            first_name='Owner', last_name='User'
        )
        
        # Create company
        self.company = Company.objects.create(
            owner=self.owner_user,
            name='Test Company',
            company_type='ltda',
            business_sector='technology',
            subscription_plan=self.enterprise_plan  # Use enterprise plan for user limits
        )
        
        # Create existing user to invite
        self.existing_user = User.objects.create_user(
            username='existinguser',
            email='existing@example.com',
            password='testpass123',
            first_name='Existing',
            last_name='User'
        )
        
        # Authenticate as owner
        self.client.force_authenticate(user=self.owner_user)
        
        # Mock email service
        self.email_service_patcher = patch('apps.notifications.email_service.EmailService')
        self.mock_email_service = self.email_service_patcher.start()
    
    def tearDown(self):
        """Clean up patches"""
        self.email_service_patcher.stop()
    
    def test_invite_existing_user_success(self):
        """Test inviting an existing user to company"""
        invitation_data = {
            'email': self.existing_user.email,
            'role': 'manager',
            'permissions': {
                'can_view_reports': True,
                'can_manage_transactions': False
            }
        }
        
        response = self.client.post('/api/companies/users/invite/', invitation_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)
        self.assertIn('user', response.data)
        self.assertEqual(response.data['message'], 'User added to company')
        
        # Verify CompanyUser was created
        company_user = CompanyUser.objects.get(
            company=self.company,
            user=self.existing_user
        )
        self.assertEqual(company_user.role, 'manager')
        self.assertEqual(company_user.permissions['can_view_reports'], True)
        self.assertIsNotNone(company_user.joined_at)
        
        # Verify email was sent
        self.mock_email_service.send_invitation_email.assert_called_once()
    
    def test_invite_new_user_success(self):
        """Test inviting a new user (user doesn't exist)"""
        invitation_data = {
            'email': 'newuser@example.com',
            'role': 'viewer',
            'permissions': {}
        }
        
        response = self.client.post('/api/companies/users/invite/', invitation_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)
        self.assertEqual(response.data['message'], 'Invitation sent to new user')
        self.assertEqual(response.data['email'], 'newuser@example.com')
        
        # Verify no CompanyUser was created (user doesn't exist yet)
        self.assertFalse(
            CompanyUser.objects.filter(
                company=self.company,
                user__email='newuser@example.com'
            ).exists()
        )
        
        # Verify invitation email was sent
        self.mock_email_service.send_invitation_email.assert_called_once()
        args, kwargs = self.mock_email_service.send_invitation_email.call_args
        self.assertEqual(kwargs['email'], 'newuser@example.com')
        self.assertEqual(kwargs['inviter'], self.owner_user)
        self.assertEqual(kwargs['company'], self.company)
        self.assertIn('accept-invitation', kwargs['invitation_url'])
    
    def test_invite_user_limit_reached(self):
        """Test invitation when user limit is reached"""
        # Change to starter plan with max_users=1
        self.company.subscription_plan = self.starter_plan
        self.company.save()
        
        invitation_data = {
            'email': self.existing_user.email,
            'role': 'viewer'
        }
        
        response = self.client.post('/api/companies/users/invite/', invitation_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn('error', response.data)
        self.assertEqual(
            response.data['error'],
            'User limit reached for current subscription plan'
        )
        
        # Verify no CompanyUser was created
        self.assertFalse(
            CompanyUser.objects.filter(
                company=self.company,
                user=self.existing_user
            ).exists()
        )
    
    def test_invite_user_with_existing_active_users(self):
        """Test invitation counting existing active users"""
        # Create an existing company user
        CompanyUser.objects.create(
            company=self.company,
            user=self.existing_user,
            role='manager',
            is_active=True
        )
        
        # Try to invite another user (should be within enterprise limit)
        new_user = User.objects.create_user(
            username='anotheruser', email='another@example.com',
            password='testpass123',
            first_name='Another', last_name='User'
        )
        
        invitation_data = {
            'email': new_user.email,
            'role': 'viewer'
        }
        
        response = self.client.post('/api/companies/users/invite/', invitation_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify both users are in company
        self.assertEqual(
            CompanyUser.objects.filter(company=self.company, is_active=True).count(),
            2
        )
    
    def test_invite_user_serializer_validation(self):
        """Test invitation with invalid data"""
        # Missing email
        response = self.client.post('/api/companies/users/invite/', {
            'role': 'manager'
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Invalid email format
        response = self.client.post('/api/companies/users/invite/', {
            'email': 'invalid-email',
            'role': 'manager'
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Invalid role
        response = self.client.post('/api/companies/users/invite/', {
            'email': self.existing_user.email,
            'role': 'invalid_role'
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_invite_user_unauthenticated(self):
        """Test invitation without authentication"""
        self.client.logout()
        
        invitation_data = {
            'email': self.existing_user.email,
            'role': 'viewer'
        }
        
        response = self.client.post('/api/companies/users/invite/', invitation_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_invite_user_duplicate_invitation(self):
        """Test inviting user that's already in company"""
        # First invitation
        CompanyUser.objects.create(
            company=self.company,
            user=self.existing_user,
            role='viewer'
        )
        
        # Try to invite again
        invitation_data = {
            'email': self.existing_user.email,
            'role': 'manager'
        }
        
        response = self.client.post('/api/companies/users/invite/', invitation_data, format='json')
        
        # Should fail due to unique constraint
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_invite_user_with_complex_permissions(self):
        """Test invitation with complex permission structure"""
        complex_permissions = {
            'banking': {
                'view': True,
                'edit': False,
                'delete': False
            },
            'reports': {
                'view': True,
                'generate': True,
                'export': False
            },
            'team': {
                'invite': False,
                'remove': False
            }
        }
        
        invitation_data = {
            'email': self.existing_user.email,
            'role': 'manager',
            'permissions': complex_permissions
        }
        
        response = self.client.post('/api/companies/users/invite/', invitation_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify permissions were saved correctly
        company_user = CompanyUser.objects.get(
            company=self.company,
            user=self.existing_user
        )
        self.assertEqual(company_user.permissions, complex_permissions)


class RemoveUserViewTest(TestCase):
    """Test RemoveUserView functionality"""
    
    def setUp(self):
        """Set up test data"""
        self.client = APIClient()
        
        # Create subscription plan
        self.subscription_plan = SubscriptionPlan.objects.create(
            name='Enterprise Plan',
            slug='enterprise',
            plan_type='enterprise',
            price_monthly=Decimal('199.90'),
            price_yearly=Decimal('1999.00'),
            max_users=10
        )
        
        # Create owner user
        self.owner_user = User.objects.create_user(
            username='owneruser', email='owner@example.com',
            password='testpass123',
            first_name='Owner', last_name='User'
        )
        
        # Create company
        self.company = Company.objects.create(
            owner=self.owner_user,
            name='Test Company',
            company_type='ltda',
            business_sector='technology',
            subscription_plan=self.subscription_plan
        )
        
        # Create users to be removed
        self.manager_user = User.objects.create_user(
            username='manageruser',
            email='manager@example.com',
            password='testpass123',
            first_name='Manager', last_name='User'
        )
        
        self.viewer_user = User.objects.create_user(
            username='vieweruser',
            email='viewer@example.com',
            password='testpass123',
            first_name='Viewer', last_name='User'
        )
        
        # Create company users
        self.manager_company_user = CompanyUser.objects.create(
            company=self.company,
            user=self.manager_user,
            role='manager'
        )
        
        self.viewer_company_user = CompanyUser.objects.create(
            company=self.company,
            user=self.viewer_user,
            role='viewer'
        )
        
        # Authenticate as owner
        self.client.force_authenticate(user=self.owner_user)
    
    def test_remove_user_success(self):
        """Test successful user removal"""
        response = self.client.delete(f'/api/companies/users/{self.manager_user.id}/remove/')
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertIn('message', response.data)
        self.assertEqual(response.data['message'], 'User removed successfully')
        
        # Verify user was removed
        self.assertFalse(
            CompanyUser.objects.filter(
                company=self.company,
                user=self.manager_user
            ).exists()
        )
    
    def test_remove_user_not_found(self):
        """Test removing non-existent user"""
        non_existent_user_id = 99999
        
        response = self.client.delete(f'/api/companies/users/{non_existent_user_id}/remove/')
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn('error', response.data)
        self.assertEqual(response.data['error'], 'User not found')
    
    def test_remove_owner_user(self):
        """Test attempting to remove company owner"""
        response = self.client.delete(f'/api/companies/users/{self.owner_user.id}/remove/')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
        self.assertEqual(response.data['error'], 'Cannot remove company owner')
        
        # Verify owner is still associated with company
        self.assertEqual(self.company.owner, self.owner_user)
    
    def test_remove_user_non_owner_permission(self):
        """Test user removal by non-owner user"""
        # Authenticate as manager instead of owner
        self.client.force_authenticate(user=self.manager_user)
        
        response = self.client.delete(f'/api/companies/users/{self.viewer_user.id}/remove/')
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn('error', response.data)
        self.assertEqual(response.data['error'], 'Only company owner can remove users')
        
        # Verify user was not removed
        self.assertTrue(
            CompanyUser.objects.filter(
                company=self.company,
                user=self.viewer_user
            ).exists()
        )
    
    def test_remove_user_unauthenticated(self):
        """Test user removal without authentication"""
        self.client.logout()
        
        response = self.client.delete(f'/api/companies/users/{self.manager_user.id}/remove/')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
        # Verify user was not removed
        self.assertTrue(
            CompanyUser.objects.filter(
                company=self.company,
                user=self.manager_user
            ).exists()
        )
    
    def test_remove_user_from_different_company(self):
        """Test removing user that belongs to different company"""
        # Create another company and user
        other_owner = User.objects.create_user(
            username='otherowner', email='otherowner@example.com',
            password='testpass123',
            first_name='Other', last_name='Owner'
        )
        
        other_company = Company.objects.create(
            owner=other_owner,
            name='Other Company',
            company_type='mei',
            business_sector='services',
            subscription_plan=self.subscription_plan
        )
        
        other_user = User.objects.create_user(
            username='otheruser', email='otheruser@example.com',
            password='testpass123',
            first_name='Other', last_name='User'
        )
        
        CompanyUser.objects.create(
            company=other_company,
            user=other_user,
            role='manager'
        )
        
        # Try to remove user from other company
        response = self.client.delete(f'/api/companies/users/{other_user.id}/remove/')
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn('error', response.data)
        self.assertEqual(response.data['error'], 'User not found')
        
        # Verify user still exists in other company
        self.assertTrue(
            CompanyUser.objects.filter(
                company=other_company,
                user=other_user
            ).exists()
        )


class CompanyUsersViewTest(TestCase):
    """Test CompanyUsersView functionality"""
    
    def setUp(self):
        """Set up test data"""
        self.client = APIClient()
        
        # Create subscription plan
        self.subscription_plan = SubscriptionPlan.objects.create(
            name='Enterprise Plan',
            slug='enterprise',
            plan_type='enterprise',
            price_monthly=Decimal('199.90'),
            price_yearly=Decimal('1999.00')
        )
        
        # Create owner user
        self.owner_user = User.objects.create_user(
            username='owneruser2', email='owner2@example.com',
            password='testpass123',
            first_name='Owner', last_name='User'
        )
        
        # Create company
        self.company = Company.objects.create(
            owner=self.owner_user,
            name='Test Company',
            company_type='ltda',
            business_sector='technology',
            subscription_plan=self.subscription_plan
        )
        
        # Create team members
        self.manager_user = User.objects.create_user(
            username='manageruser2',
            email='manager2@example.com',
            password='testpass123',
            first_name='Manager', last_name='User'
        )
        
        self.accountant_user = User.objects.create_user(
            username='accountantuser',
            email='accountant@example.com',
            password='testpass123',
            first_name='Accountant', last_name='User'
        )
        
        self.viewer_user = User.objects.create_user(
            username='vieweruser2',
            email='viewer2@example.com',
            password='testpass123',
            first_name='Viewer', last_name='User'
        )
        
        # Create company users
        self.manager_company_user = CompanyUser.objects.create(
            company=self.company,
            user=self.manager_user,
            role='manager',
            is_active=True,
            joined_at=timezone.now()
        )
        
        self.accountant_company_user = CompanyUser.objects.create(
            company=self.company,
            user=self.accountant_user,
            role='accountant',
            is_active=True,
            joined_at=timezone.now()
        )
        
        self.inactive_company_user = CompanyUser.objects.create(
            company=self.company,
            user=self.viewer_user,
            role='viewer',
            is_active=False  # Inactive user
        )
        
        # Authenticate as owner
        self.client.force_authenticate(user=self.owner_user)
    
    def test_list_company_users_success(self):
        """Test successful listing of company users"""
        response = self.client.get('/api/companies/users/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Handle pagination
        if 'results' in response.data:
            data = response.data['results']
        else:
            data = response.data
            
        self.assertEqual(len(data), 3)  # All users including inactive
        
        # Verify user data structure
        user_data = data[0]
        expected_fields = ['id', 'user', 'role', 'permissions', 'is_active', 'invited_at', 'joined_at']
        
        for field in expected_fields:
            self.assertIn(field, user_data)
        
        # Verify user details are included
        self.assertIn('id', user_data['user'])
        self.assertIn('name', user_data['user'])
        self.assertIn('email', user_data['user'])
    
    def test_list_company_users_filtering(self):
        """Test filtering company users by role or status"""
        # Get all users
        response = self.client.get('/api/companies/users/')
        
        # Handle pagination
        if 'results' in response.data:
            data = response.data['results']
        else:
            data = response.data
            
        self.assertEqual(len(data), 3)
        
        # Verify roles are correct
        roles = [user['role'] for user in data]
        self.assertIn('manager', roles)
        self.assertIn('accountant', roles)
        self.assertIn('viewer', roles)
        
        # Verify active/inactive status
        active_users = [user for user in data if user['is_active']]
        inactive_users = [user for user in data if not user['is_active']]
        
        self.assertEqual(len(active_users), 2)
        self.assertEqual(len(inactive_users), 1)
    
    def test_list_company_users_company_isolation(self):
        """Test that only users from current company are returned"""
        # First check how many users are already in our company
        initial_response = self.client.get('/api/companies/users/')
        
        # Handle pagination
        if 'results' in initial_response.data:
            initial_count = len(initial_response.data['results'])
            initial_data = initial_response.data['results']
        else:
            initial_count = len(initial_response.data)
            initial_data = initial_response.data
        
        # Create another company with users
        other_owner = User.objects.create_user(
            username='otherowner2', email='otherowner2@example.com',
            password='testpass123',
            first_name='Other', last_name='Owner'
        )
        
        other_company = Company.objects.create(
            owner=other_owner,
            name='Other Company',
            company_type='mei',
            business_sector='services',
            subscription_plan=self.subscription_plan
        )
        
        other_user = User.objects.create_user(
            username='otheruser2', email='otheruser2@example.com',
            password='testpass123',
            first_name='Other', last_name='User'
        )
        
        CompanyUser.objects.create(
            company=other_company,
            user=other_user,
            role='manager'
        )
        
        response = self.client.get('/api/companies/users/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Handle pagination in response
        if 'results' in response.data:
            current_count = len(response.data['results'])
            current_data = response.data['results']
        else:
            current_count = len(response.data)
            current_data = response.data
        
        self.assertEqual(current_count, initial_count)  # Should be same as before adding other company
        
        # Verify no users from other company
        user_emails = [user['user']['email'] for user in current_data]
        self.assertNotIn('otheruser2@example.com', user_emails)
    
    def test_list_company_users_unauthenticated(self):
        """Test listing users without authentication"""
        self.client.logout()
        
        response = self.client.get('/api/companies/users/')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_list_company_users_permissions_check(self):
        """Test that regular users can also list company users"""
        # Authenticate as manager instead of owner
        self.client.force_authenticate(user=self.manager_user)
        
        response = self.client.get('/api/companies/users/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Handle pagination
        if 'results' in response.data:
            data = response.data['results']
        else:
            data = response.data
            
        self.assertEqual(len(data), 3)
    
    def test_list_company_users_with_select_related(self):
        """Test that user data is efficiently loaded with select_related"""
        response = self.client.get('/api/companies/users/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Handle pagination
        if 'results' in response.data:
            data = response.data['results']
        else:
            data = response.data
            
        # Verify user data is properly loaded (not lazy)
        for company_user_data in data:
            user_data = company_user_data['user']
            self.assertIsInstance(user_data, dict)
            self.assertIn('name', user_data)
            self.assertIn('email', user_data)
    
    def test_list_company_users_serialization(self):
        """Test proper serialization of company users"""
        response = self.client.get('/api/companies/users/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Handle pagination
        if 'results' in response.data:
            data = response.data['results']
        else:
            data = response.data
            
        # Find manager user in response
        manager_data = next(
            user for user in data 
            if user['user']['email'] == self.manager_user.email
        )
        
        # Verify serialization matches expected format
        expected_serialized = CompanyUserSerializer(self.manager_company_user).data
        
        # Compare key fields (excluding auto-generated timestamps)
        self.assertEqual(manager_data['role'], expected_serialized['role'])
        self.assertEqual(manager_data['is_active'], expected_serialized['is_active'])
        self.assertEqual(manager_data['permissions'], expected_serialized['permissions'])


class UserManagementIntegrationTest(TestCase):
    """Integration tests for complete user management workflow"""
    
    def setUp(self):
        """Set up test data"""
        self.client = APIClient()
        
        # Create subscription plan
        self.subscription_plan = SubscriptionPlan.objects.create(
            name='Enterprise Plan',
            slug='enterprise',
            plan_type='enterprise',
            price_monthly=Decimal('199.90'),
            price_yearly=Decimal('1999.00'),
            max_users=5
        )
        
        # Create owner user
        self.owner_user = User.objects.create_user(
            username='integrationowner', email='integrationowner@example.com',
            password='testpass123',
            first_name='Owner', last_name='User'
        )
        
        # Create company
        self.company = Company.objects.create(
            owner=self.owner_user,
            name='Test Company',
            company_type='ltda',
            business_sector='technology',
            subscription_plan=self.subscription_plan
        )
        
        # Create user to invite
        self.invitee_user = User.objects.create_user(
            username='inviteeuser', email='invitee@example.com',
            password='testpass123',
            first_name='Invitee', last_name='User'
        )
        
        # Authenticate as owner
        self.client.force_authenticate(user=self.owner_user)
    
    @patch('apps.companies.views.EmailService')
    def test_complete_user_management_workflow(self, mock_email_service):
        """Test complete workflow: invite -> list -> remove user"""
        # Step 1: Invite user
        invitation_data = {
            'email': self.invitee_user.email,
            'role': 'manager',
            'permissions': {'can_view_reports': True}
        }
        
        invite_response = self.client.post('/api/companies/users/invite/', invitation_data, format='json')
        self.assertEqual(invite_response.status_code, status.HTTP_200_OK)
        
        # Verify invitation email was sent
        mock_email_service.send_invitation_email.assert_called_once()
        
        # Step 2: List users to verify invitation
        list_response = self.client.get('/api/companies/users/')
        self.assertEqual(list_response.status_code, status.HTTP_200_OK)
        
        # Handle pagination
        if 'results' in list_response.data:
            data = list_response.data['results']
        else:
            data = list_response.data
            
        self.assertEqual(len(data), 1)
        
        # Verify invited user appears in list
        invited_user_data = data[0]
        self.assertEqual(invited_user_data['user']['email'], self.invitee_user.email)
        self.assertEqual(invited_user_data['role'], 'manager')
        
        # Step 3: Remove user
        remove_response = self.client.delete(f'/api/companies/users/{self.invitee_user.id}/remove/')
        self.assertEqual(remove_response.status_code, status.HTTP_204_NO_CONTENT)
        
        # Step 4: Verify user is removed
        final_list_response = self.client.get('/api/companies/users/')
        self.assertEqual(final_list_response.status_code, status.HTTP_200_OK)
        
        # Handle pagination
        if 'results' in final_list_response.data:
            final_data = final_list_response.data['results']
        else:
            final_data = final_list_response.data
            
        self.assertEqual(len(final_data), 0)
    
    @patch('apps.companies.views.EmailService')
    def test_user_management_with_subscription_limits(self, mock_email_service):
        """Test user management respecting subscription limits"""
        # Create multiple users to test limit
        users = []
        for i in range(6):  # More than max_users (5)
            user = User.objects.create_user(
                username=f'limituser{i}',
                email=f'user{i}@example.com',
                password='testpass123',
                first_name=f'User', 
                last_name=f'{i}'
            )
            users.append(user)
        
        # Invite users up to limit
        for i in range(4):  # 4 users + owner = 5 (at limit)
            invitation_data = {
                'email': users[i].email,
                'role': 'viewer'
            }
            
            response = self.client.post('/api/companies/users/invite/', invitation_data, format='json')
            self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Try to invite one more user (should fail)
        invitation_data = {
            'email': users[4].email,
            'role': 'viewer'
        }
        
        response = self.client.post('/api/companies/users/invite/', invitation_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn('User limit reached', response.data['error'])
        
        # Verify we have exactly 4 company users
        list_response = self.client.get('/api/companies/users/')
        
        # Handle pagination
        if 'results' in list_response.data:
            data = list_response.data['results']
        else:
            data = list_response.data
            
        self.assertEqual(len(data), 4)
        
        # Remove one user
        remove_response = self.client.delete(f'/api/companies/users/{users[0].id}/remove/')
        self.assertEqual(remove_response.status_code, status.HTTP_204_NO_CONTENT)
        
        # Now we should be able to invite the 5th user
        response = self.client.post('/api/companies/users/invite/', invitation_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_user_management_role_consistency(self):
        """Test that user roles remain consistent across operations"""
        # Create and invite user as manager
        manager_user = User.objects.create_user(
            username='roleconsistencyuser', email='roleconsistency@example.com',
            password='testpass123',
            first_name='Manager', last_name='User'
        )
        
        with patch('apps.companies.views.EmailService'):
            invitation_data = {
                'email': manager_user.email,
                'role': 'manager',
                'permissions': {'can_manage_team': True}
            }
            
            self.client.post('/api/companies/users/invite/', invitation_data, format='json')
        
        # Verify role in listing
        list_response = self.client.get('/api/companies/users/')
        
        # Handle pagination
        if 'results' in list_response.data:
            data = list_response.data['results']
        else:
            data = list_response.data
            
        manager_data = data[0]
        self.assertEqual(manager_data['role'], 'manager')
        self.assertEqual(manager_data['permissions']['can_manage_team'], True)
        
        # Verify role persists in database
        company_user = CompanyUser.objects.get(
            company=self.company,
            user=manager_user
        )
        self.assertEqual(company_user.role, 'manager')
        self.assertEqual(company_user.permissions['can_manage_team'], True)