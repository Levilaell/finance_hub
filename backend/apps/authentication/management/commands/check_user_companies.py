"""
Check user-company relationships
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.companies.models import Company, CompanyUser

User = get_user_model()


class Command(BaseCommand):
    help = 'Check user-company relationships in the database'

    def add_arguments(self, parser):
        parser.add_argument(
            '--email',
            type=str,
            help='Check specific user by email',
        )

    def handle(self, *args, **options):
        email = options.get('email')
        
        if email:
            try:
                user = User.objects.get(email=email)
                self.check_user(user)
            except User.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'User with email {email} not found'))
        else:
            # Check all users
            users = User.objects.all().order_by('-created_at')[:10]  # Last 10 users
            self.stdout.write(self.style.SUCCESS(f'\nChecking last 10 users:\n'))
            
            for user in users:
                self.check_user(user)
                self.stdout.write('-' * 50)

    def check_user(self, user):
        self.stdout.write(f'User: {user.email} (ID: {user.id})')
        self.stdout.write(f'  Name: {user.get_full_name()}')
        self.stdout.write(f'  Created: {user.created_at}')
        
        # Check if user owns a company
        if hasattr(user, 'company'):
            company = user.company
            self.stdout.write(self.style.SUCCESS(f'  ✓ Owns company: {company.name} (ID: {company.id})'))
            self.stdout.write(f'    - CNPJ: {company.cnpj}')
            self.stdout.write(f'    - Type: {company.company_type}')
            self.stdout.write(f'    - Sector: {company.business_sector}')
            self.stdout.write(f'    - Status: {company.subscription_status}')
            self.stdout.write(f'    - Plan: {company.subscription_plan.name if company.subscription_plan else "None"}')
        else:
            self.stdout.write(self.style.WARNING('  ✗ Does not own a company'))
        
        # Check if user is member of any companies
        memberships = CompanyUser.objects.filter(user=user, is_active=True).select_related('company')
        if memberships.exists():
            self.stdout.write(f'  Member of {memberships.count()} companies:')
            for membership in memberships:
                self.stdout.write(f'    - {membership.company.name} (Role: {membership.role})')
        else:
            self.stdout.write('  Not a member of any company')