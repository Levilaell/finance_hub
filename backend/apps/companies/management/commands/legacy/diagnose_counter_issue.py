from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db import connection
from apps.companies.models import Company, ResourceUsage
from apps.banking.models import BankAccount, Transaction
import json
from datetime import datetime

User = get_user_model()


class Command(BaseCommand):
    help = 'Diagnose transaction counter issue in detail'

    def add_arguments(self, parser):
        parser.add_argument(
            '--email',
            type=str,
            required=True,
            help='User email to diagnose'
        )

    def handle(self, *args, **options):
        email = options.get('email')
        
        try:
            user = User.objects.get(email=email)
            company = user.company
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"User not found: {email}"))
            return
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error: {e}"))
            return
        
        self.stdout.write(self.style.SUCCESS(f"\n=== Diagnosing Counter Issue for: {email} ==="))
        self.stdout.write(f"User ID: {user.id}")
        self.stdout.write(f"Company: {company.name} (ID: {company.id})")
        
        # 1. Check timezone settings
        self.stdout.write(f"\n1. Timezone Info:")
        self.stdout.write(f"   - Django timezone.now(): {timezone.now()}")
        self.stdout.write(f"   - Python datetime.now(): {datetime.now()}")
        self.stdout.write(f"   - Timezone aware: {timezone.is_aware(timezone.now())}")
        
        # 2. Get month boundaries
        now = timezone.now()
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        self.stdout.write(f"\n2. Month Boundaries:")
        self.stdout.write(f"   - Current time: {now}")
        self.stdout.write(f"   - Month start: {month_start}")
        self.stdout.write(f"   - Month start (date only): {month_start.date()}")
        
        # 3. Check ResourceUsage
        self.stdout.write(f"\n3. ResourceUsage Records:")
        all_usage = ResourceUsage.objects.filter(company=company).order_by('-month')
        for usage in all_usage[:3]:  # Show last 3 months
            self.stdout.write(f"   - {usage.month}: transactions_count={usage.transactions_count}")
        
        # Get current month usage
        current_usage = ResourceUsage.get_or_create_current_month(company)
        self.stdout.write(f"\n   Current month ResourceUsage:")
        self.stdout.write(f"   - ID: {current_usage.id}")
        self.stdout.write(f"   - Month: {current_usage.month}")
        self.stdout.write(f"   - transactions_count: {current_usage.transactions_count}")
        self.stdout.write(f"   - created_at: {current_usage.created_at}")
        self.stdout.write(f"   - updated_at: {current_usage.updated_at}")
        
        # 4. Company fields
        self.stdout.write(f"\n4. Company Fields:")
        self.stdout.write(f"   - current_month_transactions: {company.current_month_transactions}")
        self.stdout.write(f"   - last_usage_reset: {company.last_usage_reset}")
        
        # 5. Count transactions different ways
        self.stdout.write(f"\n5. Transaction Counts:")
        
        # Total transactions
        total_tx = Transaction.objects.filter(bank_account__company=company).count()
        self.stdout.write(f"   - Total transactions (all time): {total_tx}")
        
        # By created_at
        tx_created_month = Transaction.objects.filter(
            bank_account__company=company,
            created_at__gte=month_start
        ).count()
        self.stdout.write(f"   - Created this month: {tx_created_month}")
        
        # By transaction_date (datetime field)
        tx_date_month = Transaction.objects.filter(
            bank_account__company=company,
            transaction_date__gte=month_start
        ).count()
        self.stdout.write(f"   - Transaction date >= month_start: {tx_date_month}")
        
        # By transaction_date with date comparison
        tx_date_only = Transaction.objects.filter(
            bank_account__company=company,
            transaction_date__date__gte=month_start.date()
        ).count()
        self.stdout.write(f"   - Transaction date (date only) >= month_start: {tx_date_only}")
        
        # 6. Sample transactions
        self.stdout.write(f"\n6. Sample Transactions (last 5):")
        recent_tx = Transaction.objects.filter(
            bank_account__company=company
        ).order_by('-created_at')[:5]
        
        for tx in recent_tx:
            self.stdout.write(f"   - Created: {tx.created_at} | Date: {tx.transaction_date} | {tx.description[:30]}")
        
        # 7. Raw SQL query
        self.stdout.write(f"\n7. Raw SQL Query:")
        with connection.cursor() as cursor:
            # Count by transaction_date
            cursor.execute("""
                SELECT COUNT(*) 
                FROM banking_transaction t
                JOIN banking_bankaccount ba ON t.bank_account_id = ba.id
                WHERE ba.company_id = %s 
                AND t.transaction_date >= %s
            """, [company.id, month_start])
            raw_count = cursor.fetchone()[0]
            self.stdout.write(f"   - Raw SQL count (transaction_date): {raw_count}")
            
            # Show some dates
            cursor.execute("""
                SELECT t.transaction_date, COUNT(*)
                FROM banking_transaction t
                JOIN banking_bankaccount ba ON t.bank_account_id = ba.id
                WHERE ba.company_id = %s
                GROUP BY DATE(t.transaction_date)
                ORDER BY t.transaction_date DESC
                LIMIT 10
            """, [company.id])
            
            self.stdout.write(f"\n   Transaction counts by date:")
            for row in cursor.fetchall():
                self.stdout.write(f"   - {row[0]}: {row[1]} transactions")
        
        # 8. Bank accounts
        self.stdout.write(f"\n8. Bank Accounts:")
        accounts = BankAccount.objects.filter(company=company)
        for acc in accounts:
            tx_count = Transaction.objects.filter(
                bank_account=acc,
                transaction_date__gte=month_start
            ).count()
            self.stdout.write(f"   - {acc.id}: active={acc.is_active}, status={acc.status}, "
                            f"transactions this month={tx_count}")
        
        # 9. What the API would return
        self.stdout.write(f"\n9. API Response Simulation:")
        plan = company.subscription_plan
        if plan:
            api_response = {
                'transactions': {
                    'limit': plan.max_transactions,
                    'used': current_usage.transactions_count,
                    'percentage': round((current_usage.transactions_count / plan.max_transactions * 100), 1) if plan.max_transactions != 999999 else 0
                }
            }
            self.stdout.write(json.dumps(api_response, indent=2))
        
        # 10. Recommendations
        self.stdout.write(f"\n10. Diagnosis:")
        if current_usage.transactions_count != tx_date_month:
            self.stdout.write(self.style.WARNING(f"   ⚠️  ResourceUsage mismatch!"))
            self.stdout.write(f"   ResourceUsage shows: {current_usage.transactions_count}")
            self.stdout.write(f"   Actual count is: {tx_date_month}")
            self.stdout.write(f"   Run: python manage.py fix_all_counters")
        
        if company.current_month_transactions != tx_date_month:
            self.stdout.write(self.style.WARNING(f"   ⚠️  Company counter mismatch!"))
            self.stdout.write(f"   Company shows: {company.current_month_transactions}")
            self.stdout.write(f"   Actual count is: {tx_date_month}")
        
        self.stdout.write(self.style.SUCCESS("\n=== Diagnosis complete ==="))