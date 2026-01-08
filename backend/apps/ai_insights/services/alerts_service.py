"""
Alerts Service - Rule-based financial alerts for SMBs
Generates actionable alerts without LLM costs
"""
import logging
from dataclasses import dataclass
from datetime import timedelta
from decimal import Decimal
from enum import Enum
from typing import Dict, Any, List, Optional
from django.db.models import Sum, Count, Avg, Q
from django.utils import timezone

from apps.banking.models import Transaction, BankAccount, Bill

logger = logging.getLogger(__name__)


class AlertSeverity(Enum):
    CRITICAL = "critical"  # Needs immediate action
    HIGH = "high"          # Needs attention this week
    MEDIUM = "medium"      # Worth knowing
    LOW = "low"            # Nice to know


class AlertCategory(Enum):
    CASH_FLOW = "cash_flow"
    BILLS = "bills"
    SPENDING = "spending"
    INCOME = "income"
    SAVINGS = "savings"
    ANOMALY = "anomaly"


@dataclass
class Alert:
    """Represents a single alert."""
    category: AlertCategory
    severity: AlertSeverity
    title: str
    description: str
    action: str
    value: Optional[float] = None
    metadata: Optional[Dict] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "category": self.category.value,
            "severity": self.severity.value,
            "title": self.title,
            "description": self.description,
            "action": self.action,
            "value": self.value,
            "metadata": self.metadata or {}
        }


class AlertsService:
    """
    Generates rule-based financial alerts.
    More useful and cheaper than LLM-generated insights.
    """

    # Thresholds (can be customized per company type later)
    OVERDUE_CRITICAL_DAYS = 30
    LOW_BALANCE_THRESHOLD = 0.2  # 20% of average monthly expenses
    HIGH_EXPENSE_CATEGORY_THRESHOLD = 0.4  # 40% of total
    EXPENSE_SPIKE_THRESHOLD = 1.5  # 50% increase
    INCOME_DROP_THRESHOLD = 0.7  # 30% decrease
    SAVINGS_RATE_TARGET = 0.1  # 10% savings rate
    CREDIT_CARD_UTILIZATION_WARNING = 0.7  # 70%
    CREDIT_CARD_UTILIZATION_CRITICAL = 0.9  # 90%

    def __init__(self, user):
        self.user = user
        self.today = timezone.now().date()
        self.alerts: List[Alert] = []

    def generate_alerts(self) -> List[Dict[str, Any]]:
        """Generate all alerts for the user."""
        try:
            # Run all alert checks
            self._check_overdue_bills()
            self._check_upcoming_bills()
            self._check_low_balance()
            self._check_negative_cash_flow()
            self._check_expense_concentration()
            self._check_expense_spikes()
            self._check_income_drops()
            self._check_savings_rate()
            self._check_credit_card_utilization()
            self._check_large_pending_receivables()
            self._check_recurring_expense_increases()
            self._check_unusual_transactions()

            # Sort by severity
            severity_order = {
                AlertSeverity.CRITICAL: 0,
                AlertSeverity.HIGH: 1,
                AlertSeverity.MEDIUM: 2,
                AlertSeverity.LOW: 3
            }
            self.alerts.sort(key=lambda a: severity_order[a.severity])

            return [alert.to_dict() for alert in self.alerts]

        except Exception as e:
            logger.error(f"Error generating alerts for user {self.user.id}: {e}")
            return []

    def _add_alert(self, alert: Alert):
        """Add an alert to the list."""
        self.alerts.append(alert)

    # ==================== BILL ALERTS ====================

    def _check_overdue_bills(self):
        """Check for overdue bills - CRITICAL priority."""
        overdue_bills = Bill.objects.filter(
            user=self.user,
            type='payable',
            status__in=['pending', 'partially_paid'],
            due_date__lt=self.today
        )

        if not overdue_bills.exists():
            return

        total_overdue = overdue_bills.aggregate(total=Sum('amount'))['total'] or 0
        count = overdue_bills.count()

        # Check for very old bills (30+ days)
        very_old = overdue_bills.filter(
            due_date__lt=self.today - timedelta(days=self.OVERDUE_CRITICAL_DAYS)
        )

        if very_old.exists():
            very_old_total = very_old.aggregate(total=Sum('amount'))['total'] or 0
            self._add_alert(Alert(
                category=AlertCategory.BILLS,
                severity=AlertSeverity.CRITICAL,
                title=f"Contas vencidas há mais de 30 dias",
                description=f"Você tem R$ {float(very_old_total):,.2f} em {very_old.count()} conta(s) vencida(s) há mais de 30 dias. Isso pode gerar juros, multas e negativação.",
                action="Priorize o pagamento ou negocie com os credores imediatamente.",
                value=float(very_old_total),
                metadata={"count": very_old.count(), "days_overdue": 30}
            ))
        elif count > 0:
            self._add_alert(Alert(
                category=AlertCategory.BILLS,
                severity=AlertSeverity.HIGH,
                title=f"{count} conta(s) em atraso",
                description=f"Você tem R$ {float(total_overdue):,.2f} em contas vencidas.",
                action="Pague ou negocie essas contas para evitar juros e multas.",
                value=float(total_overdue),
                metadata={"count": count}
            ))

    def _check_upcoming_bills(self):
        """Check for bills due in the next 7 days."""
        next_week = self.today + timedelta(days=7)

        upcoming = Bill.objects.filter(
            user=self.user,
            type='payable',
            status__in=['pending', 'partially_paid'],
            due_date__gte=self.today,
            due_date__lte=next_week
        )

        if not upcoming.exists():
            return

        total = upcoming.aggregate(total=Sum('amount'))['total'] or 0
        count = upcoming.count()

        # Check if user has enough balance
        total_balance = self._get_total_balance()

        if total_balance < float(total):
            self._add_alert(Alert(
                category=AlertCategory.BILLS,
                severity=AlertSeverity.CRITICAL,
                title="Saldo insuficiente para contas da semana",
                description=f"Você tem R$ {float(total):,.2f} em contas vencendo nos próximos 7 dias, mas seu saldo é de apenas R$ {total_balance:,.2f}.",
                action=f"Você precisa de mais R$ {float(total) - total_balance:,.2f}. Cobre recebíveis ou renegocie prazos.",
                value=float(total) - total_balance,
                metadata={"bills_total": float(total), "current_balance": total_balance}
            ))
        elif count >= 3:
            self._add_alert(Alert(
                category=AlertCategory.BILLS,
                severity=AlertSeverity.MEDIUM,
                title=f"{count} contas vencem esta semana",
                description=f"Total de R$ {float(total):,.2f} em contas nos próximos 7 dias.",
                action="Organize os pagamentos para evitar atrasos.",
                value=float(total),
                metadata={"count": count}
            ))

    # ==================== CASH FLOW ALERTS ====================

    def _check_low_balance(self):
        """Check if balance is too low compared to expenses."""
        total_balance = self._get_total_balance()
        avg_monthly_expenses = self._get_average_monthly_expenses()

        if avg_monthly_expenses == 0:
            return

        # Balance should cover at least 20% of monthly expenses
        min_recommended = avg_monthly_expenses * self.LOW_BALANCE_THRESHOLD

        if total_balance < 0:
            self._add_alert(Alert(
                category=AlertCategory.CASH_FLOW,
                severity=AlertSeverity.CRITICAL,
                title="Saldo negativo",
                description=f"Seu saldo total está negativo: R$ {total_balance:,.2f}",
                action="Reduza gastos imediatamente e busque receitas extras.",
                value=total_balance
            ))
        elif total_balance < min_recommended:
            days_of_expenses = (total_balance / avg_monthly_expenses) * 30 if avg_monthly_expenses > 0 else 0
            self._add_alert(Alert(
                category=AlertCategory.CASH_FLOW,
                severity=AlertSeverity.HIGH,
                title="Saldo muito baixo",
                description=f"Seu saldo de R$ {total_balance:,.2f} cobre apenas {days_of_expenses:.0f} dias de despesas.",
                action=f"O ideal é ter pelo menos R$ {min_recommended:,.2f} (20% das despesas mensais) como reserva.",
                value=total_balance,
                metadata={"days_coverage": days_of_expenses, "recommended": min_recommended}
            ))

    def _check_negative_cash_flow(self):
        """Check if expenses exceed income for the last 2 months."""
        two_months_ago = self.today - timedelta(days=60)

        transactions = Transaction.objects.filter(
            account__connection__user=self.user,
            date__gte=two_months_ago
        )

        income = transactions.filter(type='CREDIT').aggregate(
            total=Sum('amount'))['total'] or Decimal('0')
        expenses = abs(transactions.filter(type='DEBIT').aggregate(
            total=Sum('amount'))['total'] or Decimal('0'))

        if expenses > income and income > 0:
            deficit = float(expenses - income)
            deficit_pct = (deficit / float(income)) * 100

            if deficit_pct > 20:
                self._add_alert(Alert(
                    category=AlertCategory.CASH_FLOW,
                    severity=AlertSeverity.HIGH,
                    title="Gastando mais do que ganha",
                    description=f"Nos últimos 2 meses, suas despesas (R$ {float(expenses):,.2f}) superaram suas receitas (R$ {float(income):,.2f}) em {deficit_pct:.0f}%.",
                    action="Revise seus gastos e identifique onde cortar. Esse ritmo não é sustentável.",
                    value=deficit,
                    metadata={"income": float(income), "expenses": float(expenses), "deficit_pct": deficit_pct}
                ))

    # ==================== SPENDING ALERTS ====================

    def _check_expense_concentration(self):
        """Check if one category dominates expenses."""
        thirty_days_ago = self.today - timedelta(days=30)

        expenses = Transaction.objects.filter(
            account__connection__user=self.user,
            type='DEBIT',
            date__gte=thirty_days_ago
        )

        total_expenses = abs(expenses.aggregate(total=Sum('amount'))['total'] or Decimal('0'))

        if total_expenses == 0:
            return

        # Group by category
        categories = {}
        for txn in expenses:
            cat = txn.user_category.name if txn.user_category else (txn.pluggy_category or 'Outros')
            categories[cat] = categories.get(cat, Decimal('0')) + abs(txn.amount)

        # Check for concentration
        for cat, amount in categories.items():
            pct = float(amount) / float(total_expenses)
            if pct > self.HIGH_EXPENSE_CATEGORY_THRESHOLD:
                self._add_alert(Alert(
                    category=AlertCategory.SPENDING,
                    severity=AlertSeverity.MEDIUM,
                    title=f"Alta concentração em '{cat}'",
                    description=f"A categoria '{cat}' representa {pct*100:.0f}% dos seus gastos (R$ {float(amount):,.2f} de R$ {float(total_expenses):,.2f}).",
                    action=f"Avalie se esses gastos são essenciais ou se há margem para redução.",
                    value=float(amount),
                    metadata={"category": cat, "percentage": pct * 100, "total_expenses": float(total_expenses)}
                ))

    def _check_expense_spikes(self):
        """Check for unusual expense increases in categories."""
        # Current month
        current_month_start = self.today.replace(day=1)
        last_month_start = (current_month_start - timedelta(days=1)).replace(day=1)
        last_month_end = current_month_start - timedelta(days=1)

        # Get expenses by category for both periods
        current_expenses = self._get_expenses_by_category(current_month_start, self.today)
        last_expenses = self._get_expenses_by_category(last_month_start, last_month_end)

        # Days ratio for fair comparison
        days_current = (self.today - current_month_start).days + 1
        days_last = (last_month_end - last_month_start).days + 1
        day_ratio = days_last / days_current if days_current > 0 else 1

        for cat, current_amount in current_expenses.items():
            last_amount = last_expenses.get(cat, Decimal('0'))

            # Project current month based on days elapsed
            projected = float(current_amount) * day_ratio

            if last_amount > 100 and projected > float(last_amount) * self.EXPENSE_SPIKE_THRESHOLD:
                increase_pct = ((projected - float(last_amount)) / float(last_amount)) * 100
                self._add_alert(Alert(
                    category=AlertCategory.SPENDING,
                    severity=AlertSeverity.MEDIUM,
                    title=f"Aumento em '{cat}'",
                    description=f"Gastos com '{cat}' estão {increase_pct:.0f}% maiores que o mês passado (projeção: R$ {projected:,.2f} vs R$ {float(last_amount):,.2f}).",
                    action="Verifique se esse aumento era esperado ou se há gastos desnecessários.",
                    value=projected - float(last_amount),
                    metadata={"category": cat, "projected": projected, "last_month": float(last_amount)}
                ))

    # ==================== INCOME ALERTS ====================

    def _check_income_drops(self):
        """Check for significant income drops."""
        # Compare last 30 days with previous 30 days
        thirty_days_ago = self.today - timedelta(days=30)
        sixty_days_ago = self.today - timedelta(days=60)

        recent_income = Transaction.objects.filter(
            account__connection__user=self.user,
            type='CREDIT',
            date__gte=thirty_days_ago
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')

        previous_income = Transaction.objects.filter(
            account__connection__user=self.user,
            type='CREDIT',
            date__gte=sixty_days_ago,
            date__lt=thirty_days_ago
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')

        if previous_income > 1000 and recent_income < previous_income * Decimal(str(self.INCOME_DROP_THRESHOLD)):
            drop_pct = ((float(previous_income) - float(recent_income)) / float(previous_income)) * 100
            self._add_alert(Alert(
                category=AlertCategory.INCOME,
                severity=AlertSeverity.HIGH,
                title=f"Queda de {drop_pct:.0f}% na receita",
                description=f"Sua receita caiu de R$ {float(previous_income):,.2f} para R$ {float(recent_income):,.2f} nos últimos 30 dias.",
                action="Identifique a causa (cliente perdido? sazonalidade?) e tome ações para recuperar.",
                value=float(previous_income) - float(recent_income),
                metadata={"recent": float(recent_income), "previous": float(previous_income)}
            ))

    def _check_large_pending_receivables(self):
        """Check for large amounts pending to receive."""
        receivables = Bill.objects.filter(
            user=self.user,
            type='receivable',
            status__in=['pending', 'partially_paid']
        )

        total = receivables.aggregate(total=Sum('amount'))['total'] or 0

        if total > 0:
            # Check overdue receivables
            overdue = receivables.filter(due_date__lt=self.today)
            overdue_total = overdue.aggregate(total=Sum('amount'))['total'] or 0

            if overdue_total > 1000:
                oldest = overdue.order_by('due_date').first()
                days_overdue = (self.today - oldest.due_date).days if oldest else 0

                self._add_alert(Alert(
                    category=AlertCategory.INCOME,
                    severity=AlertSeverity.HIGH if days_overdue > 15 else AlertSeverity.MEDIUM,
                    title=f"R$ {float(overdue_total):,.2f} a receber em atraso",
                    description=f"Você tem valores a receber vencidos há até {days_overdue} dias.",
                    action="Entre em contato com os devedores para cobrar ou renegociar.",
                    value=float(overdue_total),
                    metadata={"count": overdue.count(), "days_overdue": days_overdue}
                ))

    # ==================== SAVINGS ALERTS ====================

    def _check_savings_rate(self):
        """Check if user is saving enough."""
        thirty_days_ago = self.today - timedelta(days=30)

        transactions = Transaction.objects.filter(
            account__connection__user=self.user,
            date__gte=thirty_days_ago
        )

        income = transactions.filter(type='CREDIT').aggregate(
            total=Sum('amount'))['total'] or Decimal('0')
        expenses = abs(transactions.filter(type='DEBIT').aggregate(
            total=Sum('amount'))['total'] or Decimal('0'))

        if income < 1000:
            return  # Not enough data

        savings = float(income) - float(expenses)
        savings_rate = savings / float(income) if income > 0 else 0

        if savings_rate < 0:
            # Already covered by negative cash flow alert
            return
        elif savings_rate < self.SAVINGS_RATE_TARGET:
            target_savings = float(income) * self.SAVINGS_RATE_TARGET
            self._add_alert(Alert(
                category=AlertCategory.SAVINGS,
                severity=AlertSeverity.LOW,
                title=f"Taxa de poupança de {savings_rate*100:.1f}%",
                description=f"Você está guardando R$ {savings:,.2f} por mês ({savings_rate*100:.1f}% da receita). O ideal é pelo menos 10%.",
                action=f"Tente economizar mais R$ {target_savings - savings:,.2f} por mês para atingir a meta de 10%.",
                value=savings,
                metadata={"savings_rate": savings_rate * 100, "target": 10}
            ))

    # ==================== CREDIT CARD ALERTS ====================

    def _check_credit_card_utilization(self):
        """Check credit card utilization."""
        credit_cards = BankAccount.objects.filter(
            connection__user=self.user,
            type='CREDIT_CARD',
            is_active=True
        )

        for card in credit_cards:
            if not card.credit_limit or card.credit_limit <= 0:
                continue

            used = abs(float(card.balance)) if card.balance < 0 else 0
            utilization = used / float(card.credit_limit)

            if utilization >= self.CREDIT_CARD_UTILIZATION_CRITICAL:
                self._add_alert(Alert(
                    category=AlertCategory.SPENDING,
                    severity=AlertSeverity.CRITICAL,
                    title=f"Cartão quase no limite ({utilization*100:.0f}%)",
                    description=f"O cartão '{card.name}' está com {utilization*100:.0f}% do limite usado (R$ {used:,.2f} de R$ {float(card.credit_limit):,.2f}).",
                    action="Evite novos gastos neste cartão e priorize o pagamento da fatura.",
                    value=used,
                    metadata={"card": card.name, "utilization": utilization * 100, "limit": float(card.credit_limit)}
                ))
            elif utilization >= self.CREDIT_CARD_UTILIZATION_WARNING:
                self._add_alert(Alert(
                    category=AlertCategory.SPENDING,
                    severity=AlertSeverity.MEDIUM,
                    title=f"Cartão com {utilization*100:.0f}% do limite",
                    description=f"O cartão '{card.name}' está com uso elevado.",
                    action="Monitore os gastos para não estourar o limite.",
                    value=used,
                    metadata={"card": card.name, "utilization": utilization * 100}
                ))

    # ==================== ANOMALY ALERTS ====================

    def _check_recurring_expense_increases(self):
        """Check for recurring expenses that increased."""
        # This would require tracking recurring transactions
        # Simplified version: check for same descriptions with different amounts
        pass  # TODO: Implement when recurring transaction tracking is available

    def _check_unusual_transactions(self):
        """Check for unusually large transactions."""
        thirty_days_ago = self.today - timedelta(days=30)
        ninety_days_ago = self.today - timedelta(days=90)

        # Get average transaction size
        historical = Transaction.objects.filter(
            account__connection__user=self.user,
            type='DEBIT',
            date__gte=ninety_days_ago,
            date__lt=thirty_days_ago
        )

        avg_expense = historical.aggregate(avg=Avg('amount'))['avg']
        if not avg_expense:
            return

        avg_expense = abs(float(avg_expense))

        # Find recent transactions that are 5x the average
        threshold = avg_expense * 5
        if threshold < 500:
            threshold = 500  # Minimum threshold

        unusual = Transaction.objects.filter(
            account__connection__user=self.user,
            type='DEBIT',
            date__gte=thirty_days_ago,
            amount__lt=-threshold  # DEBIT amounts are negative
        )

        for txn in unusual[:3]:  # Limit to top 3
            self._add_alert(Alert(
                category=AlertCategory.ANOMALY,
                severity=AlertSeverity.LOW,
                title=f"Gasto atípico: R$ {abs(float(txn.amount)):,.2f}",
                description=f"'{txn.description}' em {txn.date.strftime('%d/%m')} é significativamente maior que seus gastos normais (média: R$ {avg_expense:,.2f}).",
                action="Verifique se esse gasto era esperado e está correto.",
                value=abs(float(txn.amount)),
                metadata={"description": txn.description, "date": txn.date.isoformat(), "average": avg_expense}
            ))

    # ==================== HELPER METHODS ====================

    def _get_total_balance(self) -> float:
        """Get total balance across all accounts (excluding credit cards)."""
        accounts = BankAccount.objects.filter(
            connection__user=self.user,
            is_active=True
        ).exclude(type='CREDIT_CARD')

        return sum(float(acc.balance) for acc in accounts)

    def _get_average_monthly_expenses(self) -> float:
        """Get average monthly expenses over last 3 months."""
        ninety_days_ago = self.today - timedelta(days=90)

        total = Transaction.objects.filter(
            account__connection__user=self.user,
            type='DEBIT',
            date__gte=ninety_days_ago
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')

        return abs(float(total)) / 3

    def _get_expenses_by_category(self, start_date, end_date) -> Dict[str, Decimal]:
        """Get expenses grouped by category for a period."""
        expenses = Transaction.objects.filter(
            account__connection__user=self.user,
            type='DEBIT',
            date__gte=start_date,
            date__lte=end_date
        )

        categories = {}
        for txn in expenses:
            cat = txn.user_category.name if txn.user_category else (txn.pluggy_category or 'Outros')
            categories[cat] = categories.get(cat, Decimal('0')) + abs(txn.amount)

        return categories


def generate_alerts_for_user(user) -> List[Dict[str, Any]]:
    """Convenience function to generate alerts for a user."""
    service = AlertsService(user)
    return service.generate_alerts()
