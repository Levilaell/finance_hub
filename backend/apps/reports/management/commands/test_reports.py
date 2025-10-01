"""
Management command to test reports functionality.
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import datetime, timedelta
import json

from apps.reports.services import ReportsService

User = get_user_model()


class Command(BaseCommand):
    help = 'Test reports generation with sample data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--user-email',
            type=str,
            default='test@example.com',
            help='Email of the user to generate reports for'
        )
        parser.add_argument(
            '--report-type',
            type=str,
            choices=['all', 'cash_flow', 'category', 'balances', 'monthly', 'trend', 'comparison'],
            default='all',
            help='Type of report to generate'
        )

    def handle(self, *args, **options):
        email = options['user_email']
        report_type = options['report_type']

        # Get user
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'User with email {email} not found')
            )
            return

        service = ReportsService()
        now = timezone.now()

        self.stdout.write(self.style.SUCCESS(f'\nGenerating reports for user: {user.email}'))
        self.stdout.write(self.style.SUCCESS('=' * 60))

        # Test Cash Flow Report
        if report_type in ['all', 'cash_flow']:
            self.stdout.write('\n📊 Cash Flow Report (Last 30 days, daily)')
            cash_flow = service.get_cash_flow_report(
                user=user,
                start_date=now - timedelta(days=30),
                end_date=now,
                granularity='daily'
            )
            self.stdout.write(f"  Total Income: ${cash_flow['summary']['total_income']:.2f}")
            self.stdout.write(f"  Total Expenses: ${cash_flow['summary']['total_expenses']:.2f}")
            self.stdout.write(f"  Net Cash Flow: ${cash_flow['summary']['net_cash_flow']:.2f}")
            self.stdout.write(f"  Data Points: {len(cash_flow['labels'])}")

        # Test Category Breakdown
        if report_type in ['all', 'category']:
            self.stdout.write('\n🥧 Category Breakdown (Last 30 days)')
            category = service.get_category_breakdown(
                user=user,
                start_date=now - timedelta(days=30),
                end_date=now,
                transaction_type='DEBIT'
            )
            self.stdout.write(f"  Total Amount: ${category['summary']['total_amount']:.2f}")
            self.stdout.write(f"  Categories: {category['summary']['categories_count']}")
            if category['labels']:
                self.stdout.write("  Top Categories:")
                for label, amount in zip(category['labels'][:5], category['datasets'][0]['data'][:5]):
                    self.stdout.write(f"    - {label}: ${amount:.2f}")

        # Test Account Balances Evolution
        if report_type in ['all', 'balances']:
            self.stdout.write('\n💳 Account Balances Evolution (Last 30 days)')
            balances = service.get_account_balances_evolution(
                user=user,
                start_date=now - timedelta(days=30),
                end_date=now
            )
            self.stdout.write(f"  Accounts Tracked: {balances['summary']['accounts_count']}")
            self.stdout.write(f"  Data Points: {len(balances['labels'])}")
            for dataset in balances['datasets']:
                if dataset['data']:
                    current_balance = dataset['data'][-1]
                    self.stdout.write(f"  {dataset['label']}: ${current_balance:.2f}")

        # Test Monthly Summary
        if report_type in ['all', 'monthly']:
            self.stdout.write(f'\n📅 Monthly Summary ({now.strftime("%B %Y")})')
            monthly = service.get_monthly_summary(
                user=user,
                month=now.month,
                year=now.year
            )
            self.stdout.write(f"  Income: ${monthly['income']['total']:.2f} ({monthly['income']['count']} transactions)")
            self.stdout.write(f"  Expenses: ${monthly['expenses']['total']:.2f} ({monthly['expenses']['count']} transactions)")
            self.stdout.write(f"  Net Savings: ${monthly['net_savings']:.2f}")
            self.stdout.write(f"  Daily Avg Income: ${monthly['income']['daily_avg']:.2f}")
            self.stdout.write(f"  Daily Avg Expenses: ${monthly['expenses']['daily_avg']:.2f}")

        # Test Trend Analysis
        if report_type in ['all', 'trend']:
            self.stdout.write('\n📈 Trend Analysis (Last 6 months)')
            trend = service.get_trend_analysis(
                user=user,
                months=6,
                end_date=now
            )
            analysis = trend['analysis']
            self.stdout.write(f"  Income Trend: {analysis['income_direction'].upper()} ({analysis['income_trend_percentage']:.1f}%)")
            self.stdout.write(f"  Expense Trend: {analysis['expense_direction'].upper()} ({analysis['expense_trend_percentage']:.1f}%)")
            self.stdout.write(f"  Avg Monthly Income: ${analysis['avg_monthly_income']:.2f}")
            self.stdout.write(f"  Avg Monthly Expenses: ${analysis['avg_monthly_expenses']:.2f}")
            self.stdout.write(f"  Months Analyzed: {analysis['months_analyzed']}")

        # Test Comparison Report
        if report_type in ['all', 'comparison']:
            self.stdout.write('\n🔄 Period Comparison (This month vs Last month)')
            # This month
            month_start = datetime(now.year, now.month, 1, tzinfo=timezone.utc)
            # Last month
            if now.month == 1:
                last_month_start = datetime(now.year - 1, 12, 1, tzinfo=timezone.utc)
                last_month_end = datetime(now.year, 1, 1, tzinfo=timezone.utc) - timedelta(days=1)
            else:
                last_month_start = datetime(now.year, now.month - 1, 1, tzinfo=timezone.utc)
                last_month_end = month_start - timedelta(days=1)

            comparison = service.get_comparison_report(
                user=user,
                period1_start=last_month_start,
                period1_end=last_month_end,
                period2_start=month_start,
                period2_end=now
            )

            self.stdout.write("  Last Month:")
            self.stdout.write(f"    Income: ${comparison['period1']['income']:.2f}")
            self.stdout.write(f"    Expenses: ${comparison['period1']['expenses']:.2f}")
            self.stdout.write("  This Month:")
            self.stdout.write(f"    Income: ${comparison['period2']['income']:.2f}")
            self.stdout.write(f"    Expenses: ${comparison['period2']['expenses']:.2f}")
            self.stdout.write("  Changes:")
            self.stdout.write(f"    Income: ${comparison['changes']['income']['absolute']:.2f} ({comparison['changes']['income']['percentage']:.1f}%)")
            self.stdout.write(f"    Expenses: ${comparison['changes']['expenses']['absolute']:.2f} ({comparison['changes']['expenses']['percentage']:.1f}%)")

        self.stdout.write(self.style.SUCCESS('\n✅ Reports generated successfully!'))