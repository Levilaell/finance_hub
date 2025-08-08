"""
Check trial status for a specific user
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.authentication.models import User
from apps.companies.models import Company, UserCompany


class Command(BaseCommand):
    help = 'Check trial status for a user'

    def add_arguments(self, parser):
        parser.add_argument('email', type=str, help='User email to check')
        parser.add_argument('--fix', action='store_true', help='Fix the trial if needed')

    def handle(self, *args, **options):
        email = options['email']
        
        try:
            user = User.objects.get(email=email)
            self.stdout.write(f"User found: {user.email} (ID: {user.id})")
            self.stdout.write(f"Created at: {user.date_joined}")
            
            # Check company ownership
            try:
                company = user.company
                self.stdout.write(f"\nCompany (owned): {company.name} (ID: {company.id})")
            except:
                # Check if user is a team member
                user_companies = UserCompany.objects.filter(user=user)
                if user_companies.exists():
                    for uc in user_companies:
                        company = uc.company
                        self.stdout.write(f"\nCompany (member): {company.name} (ID: {company.id})")
                else:
                    self.stdout.write(self.style.ERROR("No company found for user"))
                    return
            
            # Display company details
            self.stdout.write(f"Created at: {company.created_at}")
            self.stdout.write(f"Subscription status: {company.subscription_status}")
            self.stdout.write(f"Trial ends at: {company.trial_ends_at}")
            self.stdout.write(f"Current time: {timezone.now()}")
            
            if company.trial_ends_at:
                time_left = company.trial_ends_at - timezone.now()
                self.stdout.write(f"Time left in trial: {time_left}")
                
                if time_left.total_seconds() < 0:
                    self.stdout.write(self.style.WARNING("Trial has expired!"))
                    
                    if options['fix']:
                        # Fix the trial
                        from datetime import timedelta
                        company.subscription_status = 'trial'
                        company.trial_ends_at = timezone.now() + timedelta(days=14)
                        company.save()
                        
                        self.stdout.write(
                            self.style.SUCCESS(
                                f"Fixed! New trial ends at: {company.trial_ends_at}"
                            )
                        )
            
            # Check subscription plan
            if company.subscription_plan:
                self.stdout.write(f"\nSubscription plan: {company.subscription_plan.name}")
                self.stdout.write(f"Plan type: {company.subscription_plan.plan_type}")
                self.stdout.write(f"Price: R$ {company.subscription_plan.price_monthly}/month")
            else:
                self.stdout.write(self.style.WARNING("No subscription plan assigned"))
            
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"User with email '{email}' not found"))