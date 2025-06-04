"""
Create companies for users that don't have them
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.companies.models import Company, SubscriptionPlan

User = get_user_model()


class Command(BaseCommand):
    help = 'Create companies for users that do not have them'

    def handle(self, *args, **options):
        # Get or create a default subscription plan
        starter_plan, plan_created = SubscriptionPlan.objects.get_or_create(
            slug='starter',
            defaults={
                'name': 'Starter',
                'plan_type': 'starter',
                'price_monthly': 29.90,
                'price_yearly': 299.00,
                'max_transactions': 500,
                'max_bank_accounts': 1,
                'max_users': 1,
                'has_ai_categorization': True,
                'has_advanced_reports': False,
                'has_api_access': False,
                'has_accountant_access': False,
            }
        )
        
        if plan_created:
            self.stdout.write(
                self.style.SUCCESS(f'Created default subscription plan: {starter_plan.name}')
            )

        # Find users without companies
        users_without_company = []
        for user in User.objects.all():
            try:
                _ = user.company
                self.stdout.write(f'User {user.email} already has company')
            except User.company.RelatedObjectDoesNotExist:
                users_without_company.append(user)
                self.stdout.write(
                    self.style.WARNING(f'User {user.email} needs a company')
                )

        # Create companies for users without them
        companies_created = 0
        for user in users_without_company:
            company_name = f'Empresa de {user.first_name or user.username}'
            
            company = Company.objects.create(
                owner=user,
                name=company_name,
                company_type='mei',
                business_sector='other',
                subscription_plan=starter_plan
            )
            
            companies_created += 1
            self.stdout.write(
                self.style.SUCCESS(
                    f'Created company "{company.name}" for user {user.email}'
                )
            )

        if companies_created == 0:
            self.stdout.write(
                self.style.SUCCESS('All users already have companies')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully created {companies_created} companies'
                )
            )