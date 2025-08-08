from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import models
from apps.companies.models import Company, ResourceUsage
from apps.banking.models import Transaction
from apps.banking.models import BankAccount
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Debug usage counter issues'

    def add_arguments(self, parser):
        parser.add_argument(
            '--email',
            type=str,
            help='User email to debug'
        )
        parser.add_argument(
            '--fix',
            action='store_true',
            help='Fix the counter if discrepancies are found'
        )

    def handle(self, *args, **options):
        email = options.get('email')
        fix = options.get('fix', False)
        
        # Get company
        if email:
            try:
                from django.contrib.auth import get_user_model
                User = get_user_model()
                user = User.objects.get(email=email)
                company = user.company
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error finding user/company: {e}"))
                return
        else:
            # Get first company with bank accounts
            company = Company.objects.filter(
                bank_accounts__isnull=False
            ).distinct().first()
            
            if not company:
                self.stdout.write(self.style.ERROR("No companies with transactions found"))
                return
        
        self.stdout.write(self.style.SUCCESS(f"\n=== Debugging Usage Counter for: {company.name} ==="))
        
        # Get current month dates
        now = timezone.now()
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        # 1. Check company fields
        self.stdout.write(f"\n1. Company fields:")
        self.stdout.write(f"   - current_month_transactions: {company.current_month_transactions}")
        
        # 2. Check ResourceUsage
        self.stdout.write(f"\n2. ResourceUsage record:")
        try:
            usage = ResourceUsage.get_or_create_current_month(company)
            self.stdout.write(f"   - Month: {usage.month}")
            self.stdout.write(f"   - transactions_count: {usage.transactions_count}")
            self.stdout.write(f"   - ai_requests_count: {usage.ai_requests_count}")
            self.stdout.write(f"   - reports_generated: {usage.reports_generated}")
            self.stdout.write(f"   - Created: {usage.created_at}")
            self.stdout.write(f"   - Updated: {usage.updated_at}")
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"   - Error getting ResourceUsage: {e}"))
            usage = None
        
        # 3. Count actual transactions for current month
        self.stdout.write(f"\n3. Actual transaction count:")
        
        # Get all bank accounts
        bank_accounts = BankAccount.objects.filter(company=company, is_active=True)
        self.stdout.write(f"   - Active bank accounts: {bank_accounts.count()}")
        
        # Count transactions
        actual_count = Transaction.objects.filter(
            bank_account__company=company,
            created_at__gte=month_start
        ).count()
        
        self.stdout.write(f"   - Transactions created this month: {actual_count}")
        
        # Count by transaction date instead of created_at
        tx_by_date = Transaction.objects.filter(
            bank_account__company=company,
            transaction_date__gte=month_start.date()
        ).count()
        
        self.stdout.write(f"   - Transactions by transaction_date: {tx_by_date}")
        
        # 4. Check recent transactions
        self.stdout.write(f"\n4. Recent transactions (last 5):")
        recent_txs = Transaction.objects.filter(
            bank_account__company=company
        ).order_by('-created_at')[:5]
        
        for tx in recent_txs:
            self.stdout.write(f"   - {tx.created_at.strftime('%Y-%m-%d %H:%M')} | "
                            f"{tx.transaction_date} | "
                            f"{tx.description[:30]} | "
                            f"R$ {tx.amount}")
        
        # 5. Check bank account sync status
        self.stdout.write(f"\n5. Bank account sync status:")
        for account in bank_accounts:
            bank_name = account.bank_provider.name if account.bank_provider else 'N/A'
            self.stdout.write(f"   - {bank_name} ({account.account_type}):")
            self.stdout.write(f"     * Status: {account.status}")
            self.stdout.write(f"     * Last sync: {account.last_sync_at}")
            self.stdout.write(f"     * External ID: {'Yes' if account.external_id else 'No'}")
            
            # Count transactions for this account
            account_txs = Transaction.objects.filter(
                bank_account=account,
                created_at__gte=month_start
            ).count()
            self.stdout.write(f"     * Transactions this month: {account_txs}")
        
        # 6. Check for discrepancies
        self.stdout.write(f"\n6. Discrepancy analysis:")
        
        discrepancy = False
        
        if company.current_month_transactions != actual_count:
            self.stdout.write(self.style.WARNING(
                f"   - Company counter ({company.current_month_transactions}) "
                f"differs from actual count ({actual_count})"
            ))
            discrepancy = True
        
        if usage and usage.transactions_count != actual_count:
            self.stdout.write(self.style.WARNING(
                f"   - ResourceUsage counter ({usage.transactions_count}) "
                f"differs from actual count ({actual_count})"
            ))
            discrepancy = True
        
        if not discrepancy:
            self.stdout.write(self.style.SUCCESS("   - No discrepancies found"))
        
        # 7. Fix if requested
        if fix and discrepancy:
            self.stdout.write(f"\n7. Fixing counters...")
            
            # Update company
            company.current_month_transactions = actual_count
            company.save(update_fields=['current_month_transactions'])
            self.stdout.write(self.style.SUCCESS(f"   - Updated company counter to {actual_count}"))
            
            # Update ResourceUsage
            if usage:
                usage.transactions_count = actual_count
                usage.save(update_fields=['transactions_count'])
                self.stdout.write(self.style.SUCCESS(f"   - Updated ResourceUsage counter to {actual_count}"))
        
        # 8. Check API endpoint
        self.stdout.write(f"\n8. API endpoint check:")
        try:
            from apps.companies.views import UsageLimitsView
            # Simulate the view logic
            plan = company.subscription_plan
            if plan:
                limit = plan.max_transactions
            else:
                limit = 100
            
            percentage = (actual_count / limit * 100) if limit != 999999 else 0
            
            self.stdout.write(f"   - Plan limit: {limit}")
            self.stdout.write(f"   - Usage percentage: {percentage:.1f}%")
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"   - Error checking API: {e}"))
        
        self.stdout.write(self.style.SUCCESS("\n=== Debug complete ==="))