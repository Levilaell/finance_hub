"""
Management command to synchronize subscription status between Company and Subscription models

This fixes inconsistencies where Company.subscription_status and Subscription.status
get out of sync, ensuring single source of truth.

Usage:
    python manage.py sync_subscription_status --dry-run
    python manage.py sync_subscription_status --fix-all
    python manage.py sync_subscription_status --company-id 123
"""

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from apps.companies.models import Company, SubscriptionPlan
from apps.payments.models import Subscription
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Synchronize subscription status between Company and Subscription models'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be changed without making modifications'
        )
        parser.add_argument(
            '--fix-all',
            action='store_true',
            help='Fix all subscription status inconsistencies'
        )
        parser.add_argument(
            '--company-id',
            type=int,
            help='Fix specific company by ID'
        )
        parser.add_argument(
            '--source',
            choices=['company', 'subscription'],
            default='subscription',
            help='Which model to use as source of truth (default: subscription)'
        )

    def handle(self, *args, **options):
        if options['company_id']:
            self.fix_company_subscription(
                company_id=options['company_id'],
                dry_run=options.get('dry_run', False),
                source=options.get('source', 'subscription')
            )
        elif options['fix_all']:
            self.fix_all_subscriptions(
                dry_run=options.get('dry_run', False),
                source=options.get('source', 'subscription')
            )
        else:
            self.audit_subscription_inconsistencies()

    def audit_subscription_inconsistencies(self):
        """Audit subscription status inconsistencies"""
        self.stdout.write("\n🔍 Auditing subscription status inconsistencies...")
        
        inconsistencies = []
        
        # Find companies with subscriptions
        companies_with_subs = Company.objects.filter(subscription__isnull=False).select_related('subscription')
        
        for company in companies_with_subs:
            subscription = company.subscription
            
            company_status = company.subscription_status
            subscription_status = subscription.status
            
            if company_status != subscription_status:
                # Handle special cases
                if (company_status == 'early_access' and subscription_status in ['active', 'trial']) or \
                   (subscription_status == 'past_due' and company_status in ['active', 'cancelled']):
                    # These might be valid differences
                    inconsistencies.append({
                        'company_id': company.id,
                        'company_name': company.name,
                        'company_status': company_status,
                        'subscription_status': subscription_status,
                        'type': 'special_case',
                        'subscription_id': subscription.id
                    })
                else:
                    # Clear inconsistency
                    inconsistencies.append({
                        'company_id': company.id,
                        'company_name': company.name,
                        'company_status': company_status,
                        'subscription_status': subscription_status,
                        'type': 'mismatch',
                        'subscription_id': subscription.id
                    })
        
        # Find companies without subscriptions but active status
        companies_without_subs = Company.objects.filter(
            subscription__isnull=True,
            subscription_status__in=['active', 'past_due']
        )
        
        for company in companies_without_subs:
            inconsistencies.append({
                'company_id': company.id,
                'company_name': company.name,
                'company_status': company.subscription_status,
                'subscription_status': None,
                'type': 'missing_subscription',
                'subscription_id': None
            })
        
        # Report findings
        if inconsistencies:
            self.stdout.write(f"\n⚠️  Found {len(inconsistencies)} inconsistencies:\n")
            
            for issue in inconsistencies:
                if issue['type'] == 'missing_subscription':
                    self.stdout.write(
                        f"  🚨 Company {issue['company_id']} ({issue['company_name']}):\n"
                        f"     Status: {issue['company_status']} but NO subscription exists\n"
                        f"     ---"
                    )
                else:
                    self.stdout.write(
                        f"  ⚠️  Company {issue['company_id']} ({issue['company_name']}):\n"
                        f"     Company status: {issue['company_status']}\n"
                        f"     Subscription status: {issue['subscription_status']}\n"
                        f"     Subscription ID: {issue['subscription_id']}\n"
                        f"     Type: {issue['type']}\n"
                        f"     ---"
                    )
            
            self.stdout.write(f"\n💡 Run with --fix-all to fix these inconsistencies")
        else:
            self.stdout.write("✅ No subscription status inconsistencies found!")

    def fix_all_subscriptions(self, dry_run=False, source='subscription'):
        """Fix all subscription status inconsistencies"""
        self.stdout.write(f"\n🔧 {'DRY RUN: ' if dry_run else ''}Fixing all subscription status inconsistencies...")
        self.stdout.write(f"   Using {source} model as source of truth")
        
        fixed_count = 0
        error_count = 0
        
        if source == 'subscription':
            # Use Subscription model as source of truth
            companies_with_subs = Company.objects.filter(subscription__isnull=False).select_related('subscription')
            
            for company in companies_with_subs:
                subscription = company.subscription
                
                if company.subscription_status != subscription.status:
                    try:
                        if not dry_run:
                            with transaction.atomic():
                                # Map subscription status to company status
                                company_status = subscription.status
                                if subscription.status == 'past_due':
                                    # Map past_due to cancelled in company model
                                    company_status = 'cancelled'
                                
                                company.subscription_status = company_status
                                company.save(update_fields=['subscription_status'])
                        
                        self.stdout.write(
                            f"  ✅ Company {company.id}: {company.subscription_status} → {subscription.status}"
                        )
                        fixed_count += 1
                        
                    except Exception as e:
                        self.stderr.write(
                            f"  ❌ Error fixing Company {company.id}: {e}"
                        )
                        error_count += 1
            
            # Handle companies without subscriptions but active status
            companies_without_subs = Company.objects.filter(
                subscription__isnull=True,
                subscription_status__in=['active', 'past_due']
            )
            
            for company in companies_without_subs:
                try:
                    if not dry_run:
                        company.subscription_status = 'trial'  # Default to trial
                        company.save(update_fields=['subscription_status'])
                    
                    self.stdout.write(
                        f"  ✅ Company {company.id} (no subscription): {company.subscription_status} → trial"
                    )
                    fixed_count += 1
                    
                except Exception as e:
                    self.stderr.write(
                        f"  ❌ Error fixing Company {company.id}: {e}"
                    )
                    error_count += 1
        
        else:  # source == 'company'
            # Use Company model as source of truth
            subscriptions = Subscription.objects.select_related('company')
            
            for subscription in subscriptions:
                company = subscription.company
                
                if company.subscription_status != subscription.status:
                    try:
                        if not dry_run:
                            with transaction.atomic():
                                # Map company status to subscription status
                                subscription_status = company.subscription_status
                                if company.subscription_status == 'early_access':
                                    # Map early_access to active in subscription model
                                    subscription_status = 'active'
                                
                                subscription.status = subscription_status
                                subscription.save(update_fields=['status'])
                        
                        self.stdout.write(
                            f"  ✅ Subscription {subscription.id}: {subscription.status} → {company.subscription_status}"
                        )
                        fixed_count += 1
                        
                    except Exception as e:
                        self.stderr.write(
                            f"  ❌ Error fixing Subscription {subscription.id}: {e}"
                        )
                        error_count += 1
        
        # Summary
        self.stdout.write(f"\n📊 Summary:")
        self.stdout.write(f"   Fixed: {fixed_count}")
        if error_count > 0:
            self.stdout.write(f"   Errors: {error_count}")
        
        if dry_run:
            self.stdout.write(f"\n🎯 This was a dry run. Use --fix-all without --dry-run to apply changes.")

    def fix_company_subscription(self, company_id, dry_run=False, source='subscription'):
        """Fix specific company subscription status"""
        self.stdout.write(f"\n🔧 {'DRY RUN: ' if dry_run else ''}Fixing subscription for company {company_id}...")
        
        try:
            company = Company.objects.get(id=company_id)
            
            try:
                subscription = company.subscription
                
                self.stdout.write(f"   Company status: {company.subscription_status}")
                self.stdout.write(f"   Subscription status: {subscription.status}")
                
                if company.subscription_status != subscription.status:
                    if source == 'subscription':
                        # Use subscription as source of truth
                        if not dry_run:
                            with transaction.atomic():
                                company.subscription_status = subscription.status
                                company.save(update_fields=['subscription_status'])
                        
                        self.stdout.write(f"   ✅ Updated company status to: {subscription.status}")
                    else:
                        # Use company as source of truth
                        if not dry_run:
                            with transaction.atomic():
                                subscription.status = company.subscription_status
                                subscription.save(update_fields=['status'])
                        
                        self.stdout.write(f"   ✅ Updated subscription status to: {company.subscription_status}")
                else:
                    self.stdout.write("   ✅ Status already synchronized")
                    
            except Subscription.DoesNotExist:
                self.stdout.write("   ⚠️  No subscription found for company")
                if company.subscription_status in ['active', 'past_due']:
                    if not dry_run:
                        company.subscription_status = 'trial'
                        company.save(update_fields=['subscription_status'])
                    self.stdout.write("   ✅ Reset company status to trial")
                
        except Company.DoesNotExist:
            raise CommandError(f"Company {company_id} not found")