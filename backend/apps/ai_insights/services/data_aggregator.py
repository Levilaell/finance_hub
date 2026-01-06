"""
Data Aggregator for AI Insights
Prepares financial data for AI analysis
"""
import logging
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, Any, List
from django.db.models import Sum, Count, Q
from django.utils import timezone

from apps.banking.models import Transaction, BankAccount, Bill, Category

logger = logging.getLogger(__name__)


class DataAggregator:
    """
    Aggregates financial data for AI analysis.
    """

    def __init__(self, user):
        self.user = user
        self.months_back = 3  # Analyze last 3 months

    def aggregate_data(self) -> Dict[str, Any]:
        """
        Aggregate all financial data for the user.

        Returns:
            Dict with structured financial data ready for AI analysis
        """
        try:
            # Get date ranges
            end_date = timezone.now().date()
            start_date = end_date - timedelta(days=90)  # 3 months

            # Get company info
            company = getattr(self.user, 'company', None)

            # Build aggregated data
            data = {
                'context': self._get_context(company, start_date, end_date),
                'data': {
                    'monthly_summaries': self._get_monthly_summaries(start_date, end_date),
                    'current_month_summary': self._get_current_month_summary(),
                    'top_expense_categories': self._get_top_categories('expense', start_date, end_date),
                    'top_income_categories': self._get_top_categories('income', start_date, end_date),
                    'top_transactions': self._get_top_transactions(start_date, end_date),
                    'bills_summary': self._get_bills_summary(),
                    'account_balances': self._get_account_balances(),
                    'trends': self._get_trends(start_date, end_date)
                }
            }

            return data

        except Exception as e:
            logger.error(f'Error aggregating data for user {self.user.id}: {str(e)}')
            raise

    def _get_context(self, company, start_date, end_date) -> Dict[str, str]:
        """Get context information about the company and analysis period."""
        from apps.ai_insights.models import AIInsight

        # Get previous analysis date
        previous_insight = AIInsight.objects.filter(
            user=self.user,
            has_error=False
        ).first()

        # Safe company attribute access with full null checks
        if company is not None:
            company_type = getattr(company, 'get_company_type_display', lambda: 'N/A')()
            business_sector = getattr(company, 'get_business_sector_display', lambda: 'N/A')()
        else:
            company_type = 'N/A'
            business_sector = 'N/A'

        return {
            'company_type': company_type or 'N/A',
            'business_sector': business_sector or 'N/A',
            'period': f"{start_date.strftime('%d/%m/%Y')} - {end_date.strftime('%d/%m/%Y')}",
            'previous_analysis_date': previous_insight.generated_at.strftime('%d/%m/%Y') if previous_insight else 'Primeira análise'
        }

    def _get_monthly_summaries(self, start_date, end_date) -> List[Dict[str, Any]]:
        """Get monthly income/expense summaries for the period."""
        summaries = []

        current = start_date
        while current <= end_date:
            month_start = current.replace(day=1)
            next_month = (month_start + timedelta(days=32)).replace(day=1)
            month_end = next_month - timedelta(days=1)

            transactions = Transaction.objects.filter(
                account__connection__user=self.user,
                date__gte=month_start,
                date__lte=month_end
            )

            income = transactions.filter(type='CREDIT').aggregate(
                total=Sum('amount')
            )['total'] or Decimal('0')

            expenses = transactions.filter(type='DEBIT').aggregate(
                total=Sum('amount')
            )['total'] or Decimal('0')

            summaries.append({
                'month': month_start.strftime('%b/%y'),
                'income': float(income),
                'expenses': float(abs(expenses)),
                'net': float(income - abs(expenses)),
                'transaction_count': transactions.count()
            })

            current = next_month

        return summaries

    def _get_current_month_summary(self) -> Dict[str, Any]:
        """Get summary for the current month."""
        now = timezone.now()
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        transactions = Transaction.objects.filter(
            account__connection__user=self.user,
            date__gte=month_start
        )

        income = transactions.filter(type='CREDIT').aggregate(
            total=Sum('amount')
        )['total'] or Decimal('0')

        expenses = transactions.filter(type='DEBIT').aggregate(
            total=Sum('amount')
        )['total'] or Decimal('0')

        return {
            'income': float(income),
            'expenses': float(abs(expenses)),
            'balance': float(income - abs(expenses)),
            'transactions_count': transactions.count()
        }

    def _get_top_categories(self, category_type: str, start_date, end_date, limit: int = 5) -> List[Dict[str, Any]]:
        """Get top expense or income categories."""
        transaction_type = 'DEBIT' if category_type == 'expense' else 'CREDIT'

        # Get transactions with categories
        transactions = Transaction.objects.filter(
            account__connection__user=self.user,
            type=transaction_type,
            date__gte=start_date,
            date__lte=end_date
        ).exclude(
            Q(user_category__isnull=True) & Q(pluggy_category='')
        )

        # Aggregate by category
        categories = {}
        for txn in transactions:
            cat_name = txn.user_category.name if txn.user_category else txn.pluggy_category
            if not cat_name:
                cat_name = 'Sem categoria'

            if cat_name not in categories:
                categories[cat_name] = {'total': 0, 'count': 0}

            categories[cat_name]['total'] += abs(float(txn.amount))
            categories[cat_name]['count'] += 1

        # Sort and limit
        sorted_categories = sorted(
            categories.items(),
            key=lambda x: x[1]['total'],
            reverse=True
        )[:limit]

        return [
            {
                'category': name,
                'total': round(data['total'], 2),
                'count': data['count']
            }
            for name, data in sorted_categories
        ]

    def _get_top_transactions(self, start_date, end_date, limit: int = 10) -> Dict[str, List[Dict[str, Any]]]:
        """Get top income and expense transactions."""
        top_expenses = Transaction.objects.filter(
            account__connection__user=self.user,
            type='DEBIT',
            date__gte=start_date,
            date__lte=end_date
        ).order_by('amount')[:limit]

        top_income = Transaction.objects.filter(
            account__connection__user=self.user,
            type='CREDIT',
            date__gte=start_date,
            date__lte=end_date
        ).order_by('-amount')[:limit]

        return {
            'top_expenses': [
                {
                    'description': txn.description,
                    'amount': float(abs(txn.amount)),
                    'date': txn.date.strftime('%d/%m/%Y'),
                    'category': txn.user_category.name if txn.user_category else txn.pluggy_category
                }
                for txn in top_expenses
            ],
            'top_income': [
                {
                    'description': txn.description,
                    'amount': float(txn.amount),
                    'date': txn.date.strftime('%d/%m/%Y'),
                    'category': txn.user_category.name if txn.user_category else txn.pluggy_category
                }
                for txn in top_income
            ]
        }

    def _get_bills_summary(self) -> Dict[str, Any]:
        """Get summary of bills (payable/receivable)."""
        bills = Bill.objects.filter(user=self.user)

        receivable = bills.filter(type='receivable', status__in=['pending', 'partially_paid'])
        payable = bills.filter(type='payable', status__in=['pending', 'partially_paid'])
        overdue = bills.filter(status__in=['pending', 'partially_paid'], due_date__lt=timezone.now().date())

        return {
            'total_receivable': float(receivable.aggregate(total=Sum('amount'))['total'] or 0),
            'total_payable': float(payable.aggregate(total=Sum('amount'))['total'] or 0),
            'total_overdue': float(overdue.aggregate(total=Sum('amount'))['total'] or 0),
            'receivable_count': receivable.count(),
            'payable_count': payable.count(),
            'overdue_count': overdue.count()
        }

    def _get_account_balances(self) -> Dict[str, Any]:
        """Get current account balances."""
        accounts = BankAccount.objects.filter(
            connection__user=self.user,
            is_active=True
        )

        # Total balance (excluding credit cards)
        total_balance = sum(
            float(acc.balance)
            for acc in accounts
            if acc.type not in ['CREDIT_CARD']
        )

        # Credit card debt
        credit_card_debt = sum(
            float(abs(acc.balance))
            for acc in accounts
            if acc.type == 'CREDIT_CARD' and acc.balance < 0
        )

        return {
            'total_balance': round(total_balance, 2),
            'credit_card_debt': round(credit_card_debt, 2),
            'accounts_count': accounts.count(),
            'account_types': list(accounts.values_list('type', flat=True).distinct())
        }

    def _get_trends(self, start_date, end_date) -> Dict[str, Any]:
        """Calculate trends (comparison with previous period)."""
        # Current period
        current_transactions = Transaction.objects.filter(
            account__connection__user=self.user,
            date__gte=start_date,
            date__lte=end_date
        )

        current_income = current_transactions.filter(type='CREDIT').aggregate(
            total=Sum('amount')
        )['total'] or Decimal('0')

        current_expenses = current_transactions.filter(type='DEBIT').aggregate(
            total=Sum('amount')
        )['total'] or Decimal('0')

        # Previous period (same duration before start_date)
        period_days = (end_date - start_date).days
        previous_start = start_date - timedelta(days=period_days)
        previous_end = start_date - timedelta(days=1)

        previous_transactions = Transaction.objects.filter(
            account__connection__user=self.user,
            date__gte=previous_start,
            date__lte=previous_end
        )

        previous_income = previous_transactions.filter(type='CREDIT').aggregate(
            total=Sum('amount')
        )['total'] or Decimal('0')

        previous_expenses = previous_transactions.filter(type='DEBIT').aggregate(
            total=Sum('amount')
        )['total'] or Decimal('0')

        # Calculate percentages
        income_change = self._calculate_percentage_change(previous_income, current_income)
        expense_change = self._calculate_percentage_change(abs(previous_expenses), abs(current_expenses))

        return {
            'income_vs_previous_period': f"{income_change:+.1f}%",
            'expenses_vs_previous_period': f"{expense_change:+.1f}%",
            'current_income': float(current_income),
            'previous_income': float(previous_income),
            'current_expenses': float(abs(current_expenses)),
            'previous_expenses': float(abs(previous_expenses))
        }

    def _calculate_percentage_change(self, old_value, new_value) -> float:
        """Calculate percentage change between two values."""
        if old_value == 0:
            return 0 if new_value == 0 else 100

        return ((new_value - old_value) / old_value) * 100
