"""
Management command to fix payment company mismatches

This handles cases where:
1. A Stripe session has company_id X but company X no longer exists
2. A user's company changed between checkout and return
3. Payment was successful but validation fails due to company mismatch

Usage:
    python manage.py fix_payment_company_mismatch --session-id cs_test_...
    python manage.py fix_payment_company_mismatch --user-email user@example.com --session-id cs_test_...
    python manage.py fix_payment_company_mismatch --list-mismatches
"""

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
import stripe
from apps.authentication.models import User
from apps.companies.models import Company, SubscriptionPlan
from apps.payments.models import Subscription, Payment, PaymentMethod
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Fix payment company mismatches from successful Stripe sessions'

    def add_arguments(self, parser):
        parser.add_argument(
            '--session-id',
            type=str,
            help='Stripe session ID to investigate/fix'
        )
        parser.add_argument(
            '--user-email',
            type=str,
            help='Email of the user who made the payment'
        )
        parser.add_argument(
            '--list-mismatches',
            action='store_true',
            help='List all potential company mismatches in recent sessions'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be done without making changes'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force creation of subscription even if one exists'
        )

    def handle(self, *args, **options):
        # Setup Stripe
        stripe.api_key = settings.STRIPE_SECRET_KEY
        
        if options['list_mismatches']:
            self.list_recent_mismatches()
        elif options['session_id']:
            self.fix_session_mismatch(
                session_id=options['session_id'],
                user_email=options.get('user_email'),
                dry_run=options.get('dry_run', False),
                force=options.get('force', False)
            )
        else:
            raise CommandError(
                'Please provide either --session-id or --list-mismatches'
            )

    def list_recent_mismatches(self):
        """List recent checkout sessions that might have company mismatches"""
        self.stdout.write("\n🔍 Scanning for potential company mismatches...")
        
        try:
            # Get recent checkout sessions from Stripe
            sessions = stripe.checkout.Session.list(
                limit=50,
                expand=['data.subscription']
            )
            
            potential_issues = []
            
            for session in sessions.data:
                if session.payment_status == 'paid':
                    metadata = session.get('metadata', {})
                    company_id = metadata.get('company_id')
                    
                    if company_id:
                        # Check if company exists
                        try:
                            company = Company.objects.get(id=company_id)
                            # Company exists, check if user has subscription
                            has_subscription = hasattr(company, 'subscription')
                            if not has_subscription:
                                potential_issues.append({
                                    'session_id': session.id,
                                    'company_id': company_id,
                                    'company_name': company.name,
                                    'owner_email': company.owner.email,
                                    'issue': 'No subscription created'
                                })
                        except Company.DoesNotExist:
                            potential_issues.append({
                                'session_id': session.id,
                                'company_id': company_id,
                                'company_name': None,
                                'owner_email': None,
                                'issue': 'Company not found'
                            })
            
            if potential_issues:
                self.stdout.write(
                    f"\n⚠️  Found {len(potential_issues)} potential issues:\n"
                )
                for issue in potential_issues:
                    self.stdout.write(
                        f"  Session: {issue['session_id']}\n"
                        f"  Company ID: {issue['company_id']}\n"
                        f"  Issue: {issue['issue']}\n"
                        f"  Owner: {issue['owner_email'] or 'N/A'}\n"
                        f"  ---"
                    )
            else:
                self.stdout.write("✅ No obvious mismatches found in recent sessions.")
                
        except Exception as e:
            self.stderr.write(f"❌ Error scanning sessions: {e}")

    def fix_session_mismatch(self, session_id, user_email=None, dry_run=False, force=False):
        """Fix a specific session company mismatch"""
        self.stdout.write(f"\n🔧 Investigating session: {session_id}")
        
        try:
            # 1. Get session from Stripe
            session = stripe.checkout.Session.retrieve(
                session_id,
                expand=['subscription', 'customer']
            )
            
            if session.payment_status != 'paid':
                raise CommandError(f"Session payment status is '{session.payment_status}', not 'paid'")
            
            # 2. Extract metadata
            metadata = session.get('metadata', {})
            subscription_metadata = session.get('subscription_data', {}).get('metadata', {})
            if not metadata.get('company_id') and subscription_metadata:
                metadata = subscription_metadata
                
            metadata_company_id = metadata.get('company_id')
            plan_id = metadata.get('plan_id')
            billing_period = metadata.get('billing_period', 'monthly')
            
            self.stdout.write(f"  💰 Payment Status: {session.payment_status}")
            self.stdout.write(f"  🏢 Metadata Company ID: {metadata_company_id}")
            self.stdout.write(f"  📋 Plan ID: {plan_id}")
            self.stdout.write(f"  📅 Billing Period: {billing_period}")
            self.stdout.write(f"  👤 Customer ID: {session.customer}")
            
            # 3. Find the correct company/user
            target_company = None
            target_user = None
            
            if user_email:
                # Use provided user email
                try:
                    target_user = User.objects.get(email=user_email)
                    target_company = Company.objects.get(owner=target_user)
                    self.stdout.write(f"  ✅ Using provided user: {user_email}")
                except (User.DoesNotExist, Company.DoesNotExist) as e:
                    raise CommandError(f"User/Company not found for email {user_email}: {e}")
            else:
                # Try to find company from metadata first
                if metadata_company_id:
                    try:
                        target_company = Company.objects.get(id=metadata_company_id)
                        target_user = target_company.owner
                        self.stdout.write(f"  ✅ Found original company: {target_company.name}")
                    except Company.DoesNotExist:
                        self.stdout.write(f"  ⚠️  Original company {metadata_company_id} not found")
                
                # If no company found, try to match by customer email
                if not target_company and session.customer_details:
                    customer_email = session.customer_details.get('email')
                    if customer_email:
                        try:
                            target_user = User.objects.get(email=customer_email)
                            target_company = Company.objects.get(owner=target_user)
                            self.stdout.write(f"  ✅ Matched by customer email: {customer_email}")
                        except (User.DoesNotExist, Company.DoesNotExist):
                            self.stdout.write(f"  ⚠️  No user/company found for customer email: {customer_email}")
            
            if not target_company or not target_user:
                raise CommandError("Could not determine target company/user. Use --user-email to specify.")
            
            # 4. Get plan
            try:
                plan = SubscriptionPlan.objects.get(id=plan_id)
                self.stdout.write(f"  📦 Plan: {plan.name}")
            except SubscriptionPlan.DoesNotExist:
                raise CommandError(f"Plan {plan_id} not found")
            
            # 5. Check current subscription status
            existing_subscription = None
            try:
                existing_subscription = target_company.subscription
                self.stdout.write(f"  📊 Existing subscription: {existing_subscription.status}")
                if existing_subscription.is_active and not force:
                    self.stdout.write("  ✅ Company already has active subscription. Use --force to override.")
                    return
            except:
                self.stdout.write("  📊 No existing subscription found")
            
            # 6. Create or update subscription
            if dry_run:
                self.stdout.write(f"\n🎯 DRY RUN - Would create subscription:")
                self.stdout.write(f"  Company: {target_company.name} (ID: {target_company.id})")
                self.stdout.write(f"  Plan: {plan.name}")
                self.stdout.write(f"  Billing: {billing_period}")
                self.stdout.write(f"  Stripe Customer: {session.customer}")
                if session.subscription:
                    self.stdout.write(f"  Stripe Subscription: {session.subscription}")
            else:
                # Create subscription record
                # Extract just the customer ID if it's an object
                customer_id = session.customer
                if hasattr(session.customer, 'id'):
                    customer_id = session.customer.id
                elif isinstance(session.customer, dict):
                    customer_id = session.customer.get('id')
                
                subscription_data = {
                    'company': target_company,
                    'plan': plan,
                    'status': 'active',
                    'billing_period': billing_period,
                    'stripe_customer_id': customer_id,
                    'stripe_subscription_id': session.subscription.id if session.subscription else None,
                }
                
                if existing_subscription:
                    # Update existing
                    for key, value in subscription_data.items():
                        if key != 'company':  # Don't change company
                            setattr(existing_subscription, key, value)
                    existing_subscription.save()
                    self.stdout.write(f"  ✅ Updated existing subscription {existing_subscription.id}")
                else:
                    # Create new
                    subscription = Subscription.objects.create(**subscription_data)
                    self.stdout.write(f"  ✅ Created new subscription {subscription.id}")
                
                # Update company status
                target_company.subscription_status = 'active'
                target_company.save()
                
                self.stdout.write(f"  🎉 Successfully fixed payment for {target_user.email}")
            
        except stripe.error.StripeError as e:
            raise CommandError(f"Stripe error: {e}")
        except Exception as e:
            logger.exception("Error fixing payment mismatch")
            raise CommandError(f"Unexpected error: {e}")