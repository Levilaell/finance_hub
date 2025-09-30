"""
Reports service for data aggregation and analysis.
"""

from django.db.models import Sum, Count, Avg, Q, F
from django.db.models.functions import TruncDate, TruncWeek, TruncMonth, TruncYear
from django.utils import timezone
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Any, Optional, Tuple
from collections import defaultdict

from apps.banking.models import Transaction, BankAccount, BankConnection


class ReportsService:
    """Service for generating financial reports and analytics."""

    @staticmethod
    def get_cash_flow_report(
        user,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        granularity: str = 'daily'
    ) -> Dict[str, Any]:
        """
        Generate cash flow report showing income vs expenses over time.

        Args:
            user: User instance
            start_date: Start date for the report
            end_date: End date for the report
            granularity: 'daily', 'weekly', 'monthly', or 'yearly'

        Returns:
            Dictionary with cash flow data suitable for charts
        """
        if not end_date:
            end_date = timezone.now()
        if not start_date:
            start_date = end_date - timedelta(days=30)

        # Get user transactions
        transactions = Transaction.objects.filter(
            account__connection__user=user,
            date__gte=start_date,
            date__lte=end_date
        )

        # Determine truncation function based on granularity
        trunc_func = {
            'daily': TruncDate,
            'weekly': TruncWeek,
            'monthly': TruncMonth,
            'yearly': TruncYear
        }.get(granularity, TruncDate)

        # Aggregate by period
        income_data = transactions.filter(type='CREDIT').annotate(
            period=trunc_func('date')
        ).values('period').annotate(
            total=Sum('amount')
        ).order_by('period')

        expense_data = transactions.filter(type='DEBIT').annotate(
            period=trunc_func('date')
        ).values('period').annotate(
            total=Sum('amount')
        ).order_by('period')

        # Format for charts
        periods = set()
        income_dict = {}
        expense_dict = {}

        for item in income_data:
            periods.add(item['period'])
            income_dict[item['period']] = float(item['total'] or 0)

        for item in expense_data:
            periods.add(item['period'])
            expense_dict[item['period']] = float(item['total'] or 0)

        # Create ordered lists
        sorted_periods = sorted(periods) if periods else []

        cash_flow_data = {
            'labels': [period.strftime('%Y-%m-%d') for period in sorted_periods],
            'datasets': [
                {
                    'label': 'Income',
                    'data': [income_dict.get(period, 0) for period in sorted_periods],
                    'borderColor': 'rgb(75, 192, 192)',
                    'backgroundColor': 'rgba(75, 192, 192, 0.2)',
                },
                {
                    'label': 'Expenses',
                    'data': [expense_dict.get(period, 0) for period in sorted_periods],
                    'borderColor': 'rgb(255, 99, 132)',
                    'backgroundColor': 'rgba(255, 99, 132, 0.2)',
                }
            ],
            'summary': {
                'total_income': sum(income_dict.values()),
                'total_expenses': sum(expense_dict.values()),
                'net_cash_flow': sum(income_dict.values()) - sum(expense_dict.values()),
                'period': f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}",
                'granularity': granularity
            }
        }

        return cash_flow_data

    @staticmethod
    def get_category_breakdown(
        user,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        transaction_type: str = 'DEBIT'
    ) -> Dict[str, Any]:
        """
        Generate category breakdown for expenses or income.

        Args:
            user: User instance
            start_date: Start date for the report
            end_date: End date for the report
            transaction_type: 'DEBIT' for expenses, 'CREDIT' for income

        Returns:
            Dictionary with category breakdown data for pie/donut charts
        """
        if not end_date:
            end_date = timezone.now()
        if not start_date:
            start_date = end_date - timedelta(days=30)

        # Get categorized transactions
        transactions = Transaction.objects.filter(
            account__connection__user=user,
            type=transaction_type,
            date__gte=start_date,
            date__lte=end_date
        ).values('category').annotate(
            total=Sum('amount'),
            count=Count('id')
        ).order_by('-total')

        # Format for charts
        categories = []
        amounts = []
        percentages = []
        total_amount = sum(item['total'] for item in transactions if item['total'])

        for item in transactions:
            if item['total']:
                category = item['category'] or 'Uncategorized'
                amount = float(item['total'])
                percentage = (amount / total_amount * 100) if total_amount > 0 else 0

                categories.append(category)
                amounts.append(amount)
                percentages.append(round(percentage, 2))

        category_data = {
            'labels': categories,
            'datasets': [{
                'data': amounts,
                'backgroundColor': [
                    'rgba(255, 99, 132, 0.8)',
                    'rgba(54, 162, 235, 0.8)',
                    'rgba(255, 206, 86, 0.8)',
                    'rgba(75, 192, 192, 0.8)',
                    'rgba(153, 102, 255, 0.8)',
                    'rgba(255, 159, 64, 0.8)',
                    'rgba(199, 199, 199, 0.8)',
                    'rgba(83, 102, 255, 0.8)',
                    'rgba(255, 99, 255, 0.8)',
                    'rgba(99, 255, 132, 0.8)',
                ][:len(categories)],
                'borderColor': [
                    'rgba(255, 99, 132, 1)',
                    'rgba(54, 162, 235, 1)',
                    'rgba(255, 206, 86, 1)',
                    'rgba(75, 192, 192, 1)',
                    'rgba(153, 102, 255, 1)',
                    'rgba(255, 159, 64, 1)',
                    'rgba(199, 199, 199, 1)',
                    'rgba(83, 102, 255, 1)',
                    'rgba(255, 99, 255, 1)',
                    'rgba(99, 255, 132, 1)',
                ][:len(categories)],
                'borderWidth': 1
            }],
            'percentages': percentages,
            'summary': {
                'total_amount': total_amount,
                'categories_count': len(categories),
                'transaction_type': 'Expenses' if transaction_type == 'DEBIT' else 'Income',
                'period': f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}"
            }
        }

        return category_data

    @staticmethod
    def get_account_balances_evolution(
        user,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        account_ids: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Generate account balance evolution over time.

        Args:
            user: User instance
            start_date: Start date for the report
            end_date: End date for the report
            account_ids: Optional list of account IDs to filter

        Returns:
            Dictionary with balance evolution data for line charts
        """
        if not end_date:
            end_date = timezone.now()
        if not start_date:
            start_date = end_date - timedelta(days=30)

        # Get accounts
        accounts_query = BankAccount.objects.filter(
            connection__user=user,
            is_active=True
        )

        if account_ids:
            accounts_query = accounts_query.filter(id__in=account_ids)

        accounts = list(accounts_query)

        # Calculate daily balances
        balance_data = {
            'labels': [],
            'datasets': [],
            'summary': {
                'accounts_count': len(accounts),
                'period': f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}"
            }
        }

        if not accounts:
            return balance_data

        # Generate date range
        current_date = start_date
        dates = []
        while current_date <= end_date:
            dates.append(current_date)
            current_date += timedelta(days=1)

        balance_data['labels'] = [d.strftime('%Y-%m-%d') for d in dates]

        # Colors for different accounts
        colors = [
            'rgb(255, 99, 132)',
            'rgb(54, 162, 235)',
            'rgb(255, 206, 86)',
            'rgb(75, 192, 192)',
            'rgb(153, 102, 255)',
            'rgb(255, 159, 64)',
        ]

        # Calculate balance evolution for each account
        for idx, account in enumerate(accounts):
            account_balances = []

            for date in dates:
                # Get transactions up to this date
                transactions_sum = Transaction.objects.filter(
                    account=account,
                    date__lte=date
                ).aggregate(
                    credits=Sum('amount', filter=Q(type='CREDIT')),
                    debits=Sum('amount', filter=Q(type='DEBIT'))
                )

                credits = float(transactions_sum['credits'] or 0)
                debits = float(transactions_sum['debits'] or 0)
                balance = float(account.balance) + credits - debits
                account_balances.append(balance)

            color = colors[idx % len(colors)]
            balance_data['datasets'].append({
                'label': f"{account.name} ({account.get_type_display()})",
                'data': account_balances,
                'borderColor': color,
                'backgroundColor': color.replace('rgb', 'rgba').replace(')', ', 0.2)'),
                'tension': 0.1,
                'fill': False
            })

        return balance_data

    @staticmethod
    def get_monthly_summary(user, month: int, year: int) -> Dict[str, Any]:
        """
        Generate monthly financial summary.

        Args:
            user: User instance
            month: Month number (1-12)
            year: Year (e.g., 2024)

        Returns:
            Dictionary with monthly summary data
        """
        start_date = datetime(year, month, 1, tzinfo=timezone.utc)
        if month == 12:
            end_date = datetime(year + 1, 1, 1, tzinfo=timezone.utc) - timedelta(days=1)
        else:
            end_date = datetime(year, month + 1, 1, tzinfo=timezone.utc) - timedelta(days=1)

        # Get transactions for the month
        transactions = Transaction.objects.filter(
            account__connection__user=user,
            date__gte=start_date,
            date__lte=end_date
        )

        # Calculate summaries
        income = transactions.filter(type='CREDIT').aggregate(
            total=Sum('amount'),
            count=Count('id')
        )

        expenses = transactions.filter(type='DEBIT').aggregate(
            total=Sum('amount'),
            count=Count('id')
        )

        # Get top expenses
        top_expenses = transactions.filter(type='DEBIT').order_by('-amount')[:10].values(
            'description', 'amount', 'category', 'date', 'merchant_name'
        )

        # Get top income
        top_income = transactions.filter(type='CREDIT').order_by('-amount')[:10].values(
            'description', 'amount', 'category', 'date', 'merchant_name'
        )

        # Daily breakdown
        daily_breakdown = transactions.annotate(
            day=TruncDate('date')
        ).values('day', 'type').annotate(
            total=Sum('amount')
        ).order_by('day')

        # Format daily data
        daily_income = {}
        daily_expenses = {}

        for item in daily_breakdown:
            day_str = item['day'].strftime('%d')
            if item['type'] == 'CREDIT':
                daily_income[day_str] = float(item['total'])
            else:
                daily_expenses[day_str] = float(item['total'])

        # Create day labels for the month
        days_in_month = (end_date - start_date).days + 1
        day_labels = [str(i) for i in range(1, days_in_month + 1)]

        summary_data = {
            'month': f"{year}-{month:02d}",
            'income': {
                'total': float(income['total'] or 0),
                'count': income['count'],
                'daily_avg': float(income['total'] or 0) / days_in_month
            },
            'expenses': {
                'total': float(expenses['total'] or 0),
                'count': expenses['count'],
                'daily_avg': float(expenses['total'] or 0) / days_in_month
            },
            'net_savings': float(income['total'] or 0) - float(expenses['total'] or 0),
            'top_expenses': [
                {
                    'description': t['description'],
                    'amount': float(t['amount']),
                    'category': t['category'],
                    'date': t['date'].strftime('%Y-%m-%d'),
                    'merchant': t['merchant_name']
                }
                for t in top_expenses
            ],
            'top_income': [
                {
                    'description': t['description'],
                    'amount': float(t['amount']),
                    'category': t['category'],
                    'date': t['date'].strftime('%Y-%m-%d'),
                    'merchant': t['merchant_name']
                }
                for t in top_income
            ],
            'daily_chart': {
                'labels': day_labels,
                'datasets': [
                    {
                        'label': 'Income',
                        'data': [daily_income.get(day, 0) for day in day_labels],
                        'backgroundColor': 'rgba(75, 192, 192, 0.6)',
                    },
                    {
                        'label': 'Expenses',
                        'data': [daily_expenses.get(day, 0) for day in day_labels],
                        'backgroundColor': 'rgba(255, 99, 132, 0.6)',
                    }
                ]
            }
        }

        return summary_data

    @staticmethod
    def get_trend_analysis(
        user,
        months: int = 6,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Generate trend analysis for the last N months.

        Args:
            user: User instance
            months: Number of months to analyze
            end_date: End date for analysis

        Returns:
            Dictionary with trend analysis data
        """
        if not end_date:
            end_date = timezone.now()

        start_date = end_date - timedelta(days=30 * months)

        # Get monthly aggregates
        transactions = Transaction.objects.filter(
            account__connection__user=user,
            date__gte=start_date,
            date__lte=end_date
        )

        monthly_data = transactions.annotate(
            month=TruncMonth('date')
        ).values('month', 'type').annotate(
            total=Sum('amount'),
            count=Count('id'),
            avg=Avg('amount')
        ).order_by('month')

        # Organize by month
        months_dict = defaultdict(lambda: {'income': 0, 'expenses': 0, 'transactions': 0})

        for item in monthly_data:
            month_key = item['month'].strftime('%Y-%m')
            if item['type'] == 'CREDIT':
                months_dict[month_key]['income'] = float(item['total'])
            else:
                months_dict[month_key]['expenses'] = float(item['total'])
            months_dict[month_key]['transactions'] += item['count']

        # Sort months and prepare data
        sorted_months = sorted(months_dict.keys())

        # Calculate trends
        income_values = [months_dict[m]['income'] for m in sorted_months]
        expense_values = [months_dict[m]['expenses'] for m in sorted_months]

        # Simple trend calculation (percentage change)
        income_trend = 0
        expense_trend = 0

        if len(income_values) >= 2 and income_values[0] > 0:
            income_trend = ((income_values[-1] - income_values[0]) / income_values[0]) * 100

        if len(expense_values) >= 2 and expense_values[0] > 0:
            expense_trend = ((expense_values[-1] - expense_values[0]) / expense_values[0]) * 100

        trend_data = {
            'labels': sorted_months,
            'datasets': [
                {
                    'label': 'Income Trend',
                    'data': income_values,
                    'borderColor': 'rgb(75, 192, 192)',
                    'backgroundColor': 'rgba(75, 192, 192, 0.2)',
                    'tension': 0.3,
                },
                {
                    'label': 'Expense Trend',
                    'data': expense_values,
                    'borderColor': 'rgb(255, 99, 132)',
                    'backgroundColor': 'rgba(255, 99, 132, 0.2)',
                    'tension': 0.3,
                }
            ],
            'analysis': {
                'income_trend_percentage': round(income_trend, 2),
                'expense_trend_percentage': round(expense_trend, 2),
                'income_direction': 'up' if income_trend > 0 else 'down' if income_trend < 0 else 'stable',
                'expense_direction': 'up' if expense_trend > 0 else 'down' if expense_trend < 0 else 'stable',
                'avg_monthly_income': sum(income_values) / len(income_values) if income_values else 0,
                'avg_monthly_expenses': sum(expense_values) / len(expense_values) if expense_values else 0,
                'months_analyzed': len(sorted_months)
            }
        }

        return trend_data

    @staticmethod
    def get_comparison_report(
        user,
        period1_start: datetime,
        period1_end: datetime,
        period2_start: datetime,
        period2_end: datetime
    ) -> Dict[str, Any]:
        """
        Compare two time periods.

        Args:
            user: User instance
            period1_start: Start of first period
            period1_end: End of first period
            period2_start: Start of second period
            period2_end: End of second period

        Returns:
            Dictionary with comparison data
        """
        # Get transactions for both periods
        period1_transactions = Transaction.objects.filter(
            account__connection__user=user,
            date__gte=period1_start,
            date__lte=period1_end
        )

        period2_transactions = Transaction.objects.filter(
            account__connection__user=user,
            date__gte=period2_start,
            date__lte=period2_end
        )

        # Calculate summaries for each period
        def get_period_summary(transactions, start, end):
            income = transactions.filter(type='CREDIT').aggregate(Sum('amount'))['amount__sum'] or 0
            expenses = transactions.filter(type='DEBIT').aggregate(Sum('amount'))['amount__sum'] or 0

            categories = transactions.filter(type='DEBIT').values('category').annotate(
                total=Sum('amount')
            ).order_by('-total')[:5]

            return {
                'income': float(income),
                'expenses': float(expenses),
                'net': float(income - expenses),
                'transactions_count': transactions.count(),
                'top_categories': [
                    {'name': c['category'] or 'Uncategorized', 'amount': float(c['total'])}
                    for c in categories
                ],
                'period': f"{start.strftime('%Y-%m-%d')} to {end.strftime('%Y-%m-%d')}"
            }

        period1_summary = get_period_summary(period1_transactions, period1_start, period1_end)
        period2_summary = get_period_summary(period2_transactions, period2_start, period2_end)

        # Calculate changes
        income_change = ((period2_summary['income'] - period1_summary['income']) / period1_summary['income'] * 100) if period1_summary['income'] > 0 else 0
        expense_change = ((period2_summary['expenses'] - period1_summary['expenses']) / period1_summary['expenses'] * 100) if period1_summary['expenses'] > 0 else 0

        comparison_data = {
            'period1': period1_summary,
            'period2': period2_summary,
            'changes': {
                'income': {
                    'absolute': period2_summary['income'] - period1_summary['income'],
                    'percentage': round(income_change, 2)
                },
                'expenses': {
                    'absolute': period2_summary['expenses'] - period1_summary['expenses'],
                    'percentage': round(expense_change, 2)
                },
                'net': {
                    'absolute': period2_summary['net'] - period1_summary['net'],
                    'percentage': round(((period2_summary['net'] - period1_summary['net']) / abs(period1_summary['net']) * 100) if period1_summary['net'] != 0 else 0, 2)
                }
            },
            'comparison_chart': {
                'labels': ['Income', 'Expenses', 'Net Savings'],
                'datasets': [
                    {
                        'label': 'Period 1',
                        'data': [period1_summary['income'], period1_summary['expenses'], period1_summary['net']],
                        'backgroundColor': 'rgba(54, 162, 235, 0.6)',
                    },
                    {
                        'label': 'Period 2',
                        'data': [period2_summary['income'], period2_summary['expenses'], period2_summary['net']],
                        'backgroundColor': 'rgba(255, 206, 86, 0.6)',
                    }
                ]
            }
        }

        return comparison_data