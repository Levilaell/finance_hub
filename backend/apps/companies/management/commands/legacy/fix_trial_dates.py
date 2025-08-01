"""
Fix trial dates for recently created companies
"""
from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.companies.models import Company


class Command(BaseCommand):
    help = 'Fix trial dates for companies'

    def handle(self, *args, **options):
        # Fix companies with expired status that were created recently
        recent_cutoff = timezone.now() - timedelta(days=1)  # Companies created in last 24 hours
        
        companies = Company.objects.filter(
            created_at__gte=recent_cutoff,
            subscription_status='expired'
        )
        
        self.stdout.write(f"Found {companies.count()} companies to fix")
        
        for company in companies:
            # Reset to trial with 14 days
            company.subscription_status = 'trial'
            company.trial_ends_at = timezone.now() + timedelta(days=14)
            company.save()
            
            self.stdout.write(
                self.style.SUCCESS(
                    f"Fixed company {company.id} - {company.name}: "
                    f"Status: {company.subscription_status}, "
                    f"Trial ends: {company.trial_ends_at}"
                )
            )
        
        # Also check companies in trial with wrong dates
        trial_companies = Company.objects.filter(
            subscription_status='trial',
            trial_ends_at__lt=timezone.now()
        )
        
        self.stdout.write(f"\nFound {trial_companies.count()} trial companies with past dates")
        
        for company in trial_companies:
            # If created recently, fix the date
            if company.created_at >= recent_cutoff:
                company.trial_ends_at = company.created_at + timedelta(days=14)
                company.save()
                
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Fixed trial date for company {company.id} - {company.name}: "
                        f"Trial ends: {company.trial_ends_at}"
                    )
                )