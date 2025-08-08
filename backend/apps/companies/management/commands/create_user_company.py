"""
Create company for users who don't have one
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.companies.models import Company, SubscriptionPlan

User = get_user_model()


class Command(BaseCommand):
    help = 'Create company for users who dont have one'

    def add_arguments(self, parser):
        parser.add_argument(
            '--email',
            type=str,
            help='User email (optional, creates for all users if not specified)'
        )

    def handle(self, *args, **options):
        email = options.get('email')
        
        if email:
            users = User.objects.filter(email=email)
        else:
            # Get all users without a company
            users = User.objects.filter(company__isnull=True)
        
        if not users.exists():
            self.stdout.write(self.style.WARNING('No users found without companies'))
            return
        
        # Get or create a basic plan for trial
        basic_plan, _ = SubscriptionPlan.objects.get_or_create(
            slug='basic',
            defaults={
                'name': 'Basic',
                'price_monthly': 0,
                'price_yearly': 0,
                'max_transactions': 500,
                'max_bank_accounts': 2,
                'max_ai_requests_per_month': 50,
                'trial_days': 14,
                'has_ai_categorization': True,
                'enable_ai_insights': False,
                'enable_ai_reports': False,
                'has_advanced_reports': False,
                'has_api_access': False,
                'has_accountant_access': False,
                'has_priority_support': False,
                'display_order': 1,
            }
        )
        
        created_count = 0
        
        for user in users:
            try:
                company = Company.objects.create(
                    owner=user,
                    name=f"{user.first_name}'s Company" if user.first_name else f"Company for {user.email}",
                    trade_name=f"{user.first_name}'s Company" if user.first_name else f"Company for {user.email}",
                    email=user.email,
                    subscription_plan=basic_plan,
                    subscription_status='trial',
                )
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Created company "{company.name}" for user {user.email}'
                    )
                )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(
                        f'Failed to create company for user {user.email}: {str(e)}'
                    )
                )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully created {created_count} companies'
            )
        )