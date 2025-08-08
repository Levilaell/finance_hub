# backend/apps/reports/report_generator.py

"""
Report generation service for creating PDF and Excel reports
"""
import io
import logging
from datetime import datetime, timedelta, date
from decimal import Decimal
from typing import Dict, List, Any, Optional, Tuple
from collections import defaultdict

from django.conf import settings
from django.db.models import Sum, Count, Avg, Q, F
from django.utils import timezone

# PDF generation
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak, Image, KeepTogether
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.charts.piecharts import Pie
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics.charts.linecharts import HorizontalLineChart
from reportlab.graphics.widgets.markers import makeMarker

# Excel generation
import xlsxwriter

from apps.banking.models import Transaction, BankAccount, TransactionCategory

logger = logging.getLogger(__name__)


class ReportGenerator:
    """Service for generating financial reports"""
    
    def __init__(self, company):
        self.company = company
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
    
    def _setup_custom_styles(self):
        """Setup custom styles for PDF"""
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1a202c'),
            spaceAfter=30,
        ))
        
        self.styles.add(ParagraphStyle(
            name='CustomHeading',
            parent=self.styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#2d3748'),
            spaceAfter=12,
        ))
        
        self.styles.add(ParagraphStyle(
            name='SectionHeading',
            parent=self.styles['Heading3'],
            fontSize=12,
            textColor=colors.HexColor('#4a5568'),
            spaceAfter=8,
        ))
        
        self.styles.add(ParagraphStyle(
            name='Footer',
            parent=self.styles['Normal'],
            fontSize=8,
            textColor=colors.HexColor('#718096'),
            alignment=1,  # Center alignment
        ))
    
    def generate_report(
        self, 
        report_type: str,
        start_date: date,
        end_date: date,
        format: str = 'pdf',
        filters: Optional[Dict] = None
    ) -> io.BytesIO:
        """Generate report based on type"""
        
        # Route to appropriate generator method
        if report_type == 'profit_loss':
            return self.generate_profit_loss_report(start_date, end_date, format, filters)
        elif report_type == 'cash_flow':
            return self.generate_cash_flow_report(start_date, end_date, format, filters)
        elif report_type == 'monthly_summary':
            return self.generate_monthly_summary_report(start_date, end_date, format, filters)
        elif report_type == 'category_analysis':
            return self.generate_category_analysis_report(start_date, end_date, format, filters)
        else:
            # Default to transaction report for backward compatibility
            return self.generate_transaction_report(start_date, end_date, format, filters)
    
    def generate_profit_loss_report(
        self,
        start_date: date,
        end_date: date,
        format: str = 'pdf',
        filters: Optional[Dict] = None
    ) -> io.BytesIO:
        """Generate Profit & Loss (DRE) report"""
        
        # Get all transactions in period
        transactions = self._get_filtered_transactions(start_date, end_date, filters)
        
        # Calculate revenue by category
        revenue_by_category = transactions.filter(
            transaction_type__in=['credit', 'transfer_in', 'pix_in', 'interest']
        ).values(
            'category__name'
        ).annotate(
            total=Sum('amount'),
            count=Count('id')
        ).order_by('-total')
        
        # Calculate expenses by category
        expenses_by_category = transactions.filter(
            transaction_type__in=['debit', 'transfer_out', 'pix_out', 'fee']
        ).values(
            'category__name'
        ).annotate(
            total=Sum('amount'),
            count=Count('id')
        ).order_by('-total')
        
        # Calculate totals
        total_revenue = sum(item['total'] or 0 for item in revenue_by_category)
        total_expenses = sum(item['total'] or 0 for item in expenses_by_category)
        gross_profit = total_revenue + total_expenses  # expenses are negative in DB, so add
        
        # Calculate monthly breakdown
        monthly_data = self._calculate_monthly_breakdown(transactions, start_date, end_date)
        
        if format == 'pdf':
            return self._generate_profit_loss_pdf(
                revenue_by_category, expenses_by_category,
                total_revenue, total_expenses, gross_profit,
                monthly_data, start_date, end_date
            )
        else:
            return self._generate_profit_loss_excel(
                revenue_by_category, expenses_by_category,
                total_revenue, total_expenses, gross_profit,
                monthly_data, start_date, end_date
            )
    
    def generate_cash_flow_report(
        self,
        start_date: date,
        end_date: date,
        format: str = 'pdf',
        filters: Optional[Dict] = None
    ) -> io.BytesIO:
        """Generate Cash Flow report"""
        
        # Get all accounts
        accounts = BankAccount.objects.filter(
            company=self.company,
            is_active=True
        )
        
        # Calculate opening and closing balances
        account_balances = []
        total_opening = Decimal('0')
        total_closing = Decimal('0')
        
        for account in accounts:
            opening_balance = self._get_balance_at_date(account, start_date)
            closing_balance = self._get_balance_at_date(account, end_date + timedelta(days=1))
            
            account_balances.append({
                'account': account,
                'opening': opening_balance,
                'closing': closing_balance,
                'change': closing_balance - opening_balance
            })
            
            total_opening += opening_balance
            total_closing += closing_balance
        
        # Get cash flow transactions
        transactions = self._get_filtered_transactions(start_date, end_date, filters)
        
        # Daily cash flow
        daily_flow = self._calculate_daily_cash_flow(transactions, start_date, end_date)
        
        # Cash flow by category
        inflows = transactions.filter(
            transaction_type__in=['credit', 'transfer_in', 'pix_in', 'interest']
        ).values(
            'category__name'
        ).annotate(
            total=Sum('amount')
        ).order_by('-total')
        
        outflows = transactions.filter(
            transaction_type__in=['debit', 'transfer_out', 'pix_out', 'fee']
        ).values(
            'category__name'
        ).annotate(
            total=Sum('amount')
        ).order_by('-total')
        
        if format == 'pdf':
            return self._generate_cash_flow_pdf(
                account_balances, total_opening, total_closing,
                daily_flow, inflows, outflows,
                start_date, end_date
            )
        else:
            return self._generate_cash_flow_excel(
                account_balances, total_opening, total_closing,
                daily_flow, inflows, outflows,
                start_date, end_date
            )
    
    def generate_monthly_summary_report(
        self,
        start_date: date,
        end_date: date,
        format: str = 'pdf',
        filters: Optional[Dict] = None
    ) -> io.BytesIO:
        """Generate Monthly Summary report"""
        
        # Get transactions
        transactions = self._get_filtered_transactions(start_date, end_date, filters)
        
        # Summary statistics
        summary_stats = self._calculate_summary_stats(transactions)
        
        # Top expenses
        top_expenses = transactions.filter(
            transaction_type__in=['debit', 'transfer_out', 'pix_out', 'fee']
        ).order_by('-amount')[:10]
        
        # Top income
        top_income = transactions.filter(
            transaction_type__in=['credit', 'transfer_in', 'pix_in', 'interest']
        ).order_by('-amount')[:10]
        
        # Daily averages
        days_in_period = (end_date - start_date).days + 1
        avg_daily_expense = summary_stats['total_expenses'] / days_in_period if days_in_period > 0 else 0
        avg_daily_income = summary_stats['total_income'] / days_in_period if days_in_period > 0 else 0
        
        # Category breakdown
        category_breakdown = self._calculate_category_breakdown(transactions)
        
        # Account activity
        account_activity = transactions.values(
            'bank_account__id',
            'bank_account__nickname'
        ).annotate(
            transaction_count=Count('id'),
            total_credits=Sum('amount', filter=Q(transaction_type__in=['credit', 'transfer_in', 'pix_in', 'interest'])),
            total_debits=Sum('amount', filter=Q(transaction_type__in=['debit', 'transfer_out', 'pix_out', 'fee']))
        )
        
        if format == 'pdf':
            return self._generate_monthly_summary_pdf(
                summary_stats, top_expenses, top_income,
                avg_daily_expense, avg_daily_income,
                category_breakdown, account_activity,
                start_date, end_date
            )
        else:
            return self._generate_monthly_summary_excel(
                summary_stats, top_expenses, top_income,
                avg_daily_expense, avg_daily_income,
                category_breakdown, account_activity,
                start_date, end_date
            )
    
    def generate_category_analysis_report(
        self,
        start_date: date,
        end_date: date,
        format: str = 'pdf',
        filters: Optional[Dict] = None
    ) -> io.BytesIO:
        """Generate Category Analysis report"""
        
        # Get transactions
        transactions = self._get_filtered_transactions(start_date, end_date, filters)
        
        # Get all categories
        categories = TransactionCategory.objects.filter(
            is_active=True
        ).annotate(
            total_amount=Sum(
                'transactions__amount',
                filter=Q(
                    transactions__transaction_date__gte=start_date,
                    transactions__transaction_date__lte=end_date,
                    transactions__bank_account__company=self.company
                )
            ),
            transaction_count=Count(
                'transactions',
                filter=Q(
                    transactions__transaction_date__gte=start_date,
                    transactions__transaction_date__lte=end_date,
                    transactions__bank_account__company=self.company
                )
            ),
            avg_transaction=Avg(
                'transactions__amount',
                filter=Q(
                    transactions__transaction_date__gte=start_date,
                    transactions__transaction_date__lte=end_date,
                    transactions__bank_account__company=self.company
                )
            )
        ).order_by('-total_amount')
        
        # Category trends (monthly)
        category_trends = self._calculate_category_trends(transactions, start_date, end_date)
        
        # Category comparison
        # Calculate total from all categories to ensure consistency
        category_data = []
        total_all_transactions = Decimal('0')
        
        for category in categories:
            if category.total_amount:
                category_data.append({
                    'category': category,
                    'total': category.total_amount,
                    'count': category.transaction_count,
                    'average': category.avg_transaction or 0,
                    'percentage': 0  # Will be calculated after we have the total
                })
                total_all_transactions += abs(category.total_amount)
        
        # Now calculate percentages based on the actual total
        for item in category_data:
            item['percentage'] = (abs(item['total']) / total_all_transactions * 100) if total_all_transactions > 0 else 0
        
        # Use the calculated total for the report
        total_expenses = total_all_transactions
        
        if format == 'pdf':
            return self._generate_category_analysis_pdf(
                category_data, category_trends,
                total_expenses, start_date, end_date
            )
        else:
            return self._generate_category_analysis_excel(
                category_data, category_trends,
                total_expenses, start_date, end_date
            )
    
    def generate_transaction_report(
        self, 
        start_date: date,
        end_date: date,
        format: str = 'pdf',
        filters: Optional[Dict] = None
    ) -> io.BytesIO:
        """Generate transaction report in PDF or Excel format"""
        
        # Get transactions
        transactions = self._get_filtered_transactions(start_date, end_date, filters)
        
        if format == 'pdf':
            return self._generate_transaction_pdf(transactions, start_date, end_date)
        else:
            return self._generate_transaction_excel(transactions, start_date, end_date)
    
    # Helper methods
    def _get_filtered_transactions(self, start_date: date, end_date: date, filters: Optional[Dict] = None):
        """Get filtered transactions"""
        transactions = Transaction.objects.filter(
            bank_account__company=self.company,
            transaction_date__gte=start_date,
            transaction_date__lte=end_date
        )
        
        # Apply filters
        if filters:
            if filters.get('category_ids'):
                transactions = transactions.filter(category_id__in=filters['category_ids'])
            if filters.get('account_ids'):
                transactions = transactions.filter(bank_account_id__in=filters['account_ids'])
            if filters.get('transaction_type'):
                transactions = transactions.filter(transaction_type=filters['transaction_type'])
        
        return transactions.select_related('category', 'bank_account').order_by('-transaction_date')
    
    def _get_account_display_name(self, account):
        """Get display name for bank account"""
        if hasattr(account, 'name') and account.name:
            return account.name
        elif hasattr(account, 'alias') and account.alias:
            return account.alias
        else:
            # Construir nome baseado no banco e tipo
            bank_name = account.bank_provider.name if hasattr(account, 'bank_provider') else 'Banco'
            account_type = account.get_account_type_display() if hasattr(account, 'get_account_type_display') else account.account_type
            return f"{bank_name} - {account_type}"
    
    def _calculate_summary_stats(self, transactions) -> Dict[str, Any]:
        """Calculate summary statistics for transactions"""
        income = transactions.filter(
            transaction_type__in=['credit', 'transfer_in', 'pix_in', 'interest']
        ).aggregate(
            total=Sum('amount'), count=Count('id')
        )
        expenses = transactions.filter(
            transaction_type__in=['debit', 'transfer_out', 'pix_out', 'fee']
        ).aggregate(
            total=Sum('amount'), count=Count('id')
        )
        
        total_income = income['total'] or Decimal('0')
        total_expenses = expenses['total'] or Decimal('0')
        
        return {
            'total_count': transactions.count(),
            'total_income': total_income,
            'total_expenses': abs(total_expenses),  # Convert to positive for display
            'net_balance': total_income - abs(total_expenses),  # subtract absolute value of expenses
            'income_count': income['count'] or 0,
            'expense_count': expenses['count'] or 0
        }
    
    def _calculate_category_breakdown(self, transactions) -> List[Dict[str, Any]]:
        """Calculate expense breakdown by category"""
        expenses = transactions.filter(
            transaction_type__in=['debit', 'transfer_out', 'pix_out', 'fee']
        )
        
        category_data = expenses.values('category__name').annotate(
            total=Sum('amount'),
            count=Count('id')
        ).order_by('-total')
        
        return [
            {
                'name': item['category__name'] or 'Sem categoria',
                'total': item['total'],
                'count': item['count']
            }
            for item in category_data
        ]
    
    def _calculate_monthly_breakdown(self, transactions, start_date: date, end_date: date):
        """Calculate monthly breakdown of income and expenses"""
        monthly_data = defaultdict(lambda: {'income': Decimal('0'), 'expenses': Decimal('0')})
        
        for trans in transactions:
            month_key = trans.transaction_date.strftime('%Y-%m')
            if trans.transaction_type in ['credit', 'transfer_in', 'pix_in', 'interest']:
                monthly_data[month_key]['income'] += trans.amount
            elif trans.transaction_type in ['debit', 'transfer_out', 'pix_out', 'fee']:
                monthly_data[month_key]['expenses'] += trans.amount
        
        # Convert to sorted list
        result = []
        current = start_date
        while current <= end_date:
            month_key = current.strftime('%Y-%m')
            data = monthly_data.get(month_key, {'income': Decimal('0'), 'expenses': Decimal('0')})
            result.append({
                'month': current.strftime('%B %Y'),
                'month_date': current,
                'income': data['income'],
                'expenses': data['expenses'],
                'profit': data['income'] + data['expenses']  # expenses are negative, so add them
            })
            # Move to next month
            if current.month == 12:
                current = current.replace(year=current.year + 1, month=1)
            else:
                current = current.replace(month=current.month + 1)
        
        return result
    
    def _calculate_daily_cash_flow(self, transactions, start_date: date, end_date: date):
        """Calculate daily cash flow"""
        daily_data = defaultdict(lambda: {'inflow': Decimal('0'), 'outflow': Decimal('0')})
        
        for trans in transactions:
            # Convert datetime to date for consistent key comparison
            day_key = trans.transaction_date.date() if hasattr(trans.transaction_date, 'date') else trans.transaction_date
            if trans.transaction_type in ['credit', 'transfer_in', 'pix_in', 'interest']:
                daily_data[day_key]['inflow'] += trans.amount
            elif trans.transaction_type in ['debit', 'transfer_out', 'pix_out', 'fee']:
                daily_data[day_key]['outflow'] += abs(trans.amount)
        
        # Create complete daily series
        result = []
        current = start_date
        cumulative_balance = Decimal('0')
        
        while current <= end_date:
            data = daily_data.get(current, {'inflow': Decimal('0'), 'outflow': Decimal('0')})
            daily_balance = data['inflow'] - data['outflow']  # outflow is positive value, so subtract
            cumulative_balance += daily_balance
            
            result.append({
                'date': current,
                'inflow': data['inflow'],
                'outflow': data['outflow'],
                'net': daily_balance,
                'cumulative': cumulative_balance
            })
            current += timedelta(days=1)
        
        return result
    
    def _calculate_category_trends(self, transactions, start_date: date, end_date: date):
        """Calculate category trends over time"""
        trends = defaultdict(lambda: defaultdict(Decimal))
        
        for trans in transactions:
            if trans.transaction_type in ['debit', 'transfer_out', 'pix_out', 'fee']:  # Only expenses for category analysis
                month_key = trans.transaction_date.strftime('%Y-%m')
                category_name = trans.category.name if trans.category else 'Sem categoria'
                trends[category_name][month_key] += abs(trans.amount)
        
        return dict(trends)
    
    def _get_balance_at_date(self, account, date):
        """Calculate account balance at a specific date"""
        # Get all transactions up to (not including) the date
        transactions = Transaction.objects.filter(
            bank_account=account,
            transaction_date__lt=date
        )
        
        credits = transactions.filter(
            transaction_type__in=['credit', 'transfer_in', 'pix_in', 'interest']
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
        
        debits = transactions.filter(
            transaction_type__in=['debit', 'transfer_out', 'pix_out', 'fee']
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
        
        # Calculate balance as credits + debits (debits are negative in DB)
        # This gives us the net change from all transactions
        return credits + debits
    
    # PDF Generation Methods
    def _generate_profit_loss_pdf(self, revenue_by_category, expenses_by_category,
                                  total_revenue, total_expenses, gross_profit,
                                  monthly_data, start_date, end_date):
        """Generate PDF for Profit & Loss report"""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        story = []
        
        # Title
        title = Paragraph(
            f"Demonstração de Resultados (DRE) - {self.company.name}",
            self.styles['CustomTitle']
        )
        story.append(title)
        
        # Period
        period = Paragraph(
            f"Período: {start_date.strftime('%d/%m/%Y')} a {end_date.strftime('%d/%m/%Y')}",
            self.styles['Normal']
        )
        story.append(period)
        story.append(Spacer(1, 0.5*inch))
        
        # Summary
        story.append(Paragraph("Resumo Executivo", self.styles['CustomHeading']))
        
        summary_data = [
            ['', 'Valor (R$)', '% do Total'],
            ['RECEITAS', f'{total_revenue:,.2f}', '100%'],
            ['DESPESAS', f'-{abs(total_expenses):,.2f}', 
             f'{(abs(total_expenses)/total_revenue*100):.1f}%' if total_revenue > 0 else '0%'],
            ['', '', ''],
            ['LUCRO/PREJUÍZO', 
             f'{gross_profit:,.2f}',
             f'{(gross_profit/total_revenue*100):.1f}%' if total_revenue > 0 else '0%'],
        ]
        
        summary_table = Table(summary_data, colWidths=[3*inch, 2*inch, 1.5*inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTNAME', (0, 4), (-1, 4), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('LINEBELOW', (0, 2), (-1, 2), 2, colors.black),
            ('BACKGROUND', (0, 4), (-1, 4), colors.lightgrey),
        ]))
        story.append(summary_table)
        story.append(Spacer(1, 0.5*inch))
        
        # Revenue breakdown
        if revenue_by_category:
            story.append(Paragraph("Detalhamento de Receitas", self.styles['SectionHeading']))
            revenue_data = [['Categoria', 'Valor (R$)', 'Qtd', '%']]
            
            for item in revenue_by_category:
                percentage = (item['total'] / total_revenue * 100) if total_revenue > 0 else 0
                revenue_data.append([
                    item['category__name'] or 'Sem categoria',
                    f"{item['total']:,.2f}",
                    str(item['count']),
                    f"{percentage:.1f}%"
                ])
            
            revenue_table = Table(revenue_data, colWidths=[3*inch, 1.5*inch, 0.8*inch, 0.8*inch])
            revenue_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.green),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
            ]))
            story.append(revenue_table)
            story.append(Spacer(1, 0.3*inch))
        
        # Expense breakdown
        if expenses_by_category:
            story.append(Paragraph("Detalhamento de Despesas", self.styles['SectionHeading']))
            expense_data = [['Categoria', 'Valor (R$)', 'Qtd', '%']]
            
            for item in expenses_by_category:
                percentage = (abs(item['total']) / abs(total_expenses) * 100) if total_expenses != 0 else 0
                expense_data.append([
                    item['category__name'] or 'Sem categoria',
                    f"{item['total']:,.2f}",
                    str(item['count']),
                    f"{percentage:.1f}%"
                ])
            
            expense_table = Table(expense_data, colWidths=[3*inch, 1.5*inch, 0.8*inch, 0.8*inch])
            expense_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.red),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
            ]))
            story.append(expense_table)
        
        # Monthly breakdown
        if monthly_data:
            story.append(PageBreak())
            story.append(Paragraph("Evolução Mensal", self.styles['CustomHeading']))
            
            monthly_table_data = [['Mês', 'Receitas (R$)', 'Despesas (R$)', 'Resultado (R$)']]
            
            for month in monthly_data:
                monthly_table_data.append([
                    month['month'],
                    f"{month['income']:,.2f}",
                    f"-{abs(month['expenses']):,.2f}",
                    f"{month['profit']:,.2f}"
                ])
            
            # Add totals
            monthly_table_data.append([
                'TOTAL',
                f"{total_revenue:,.2f}",
                f"-{abs(total_expenses):,.2f}",
                f"{gross_profit:,.2f}"
            ])
            
            monthly_table = Table(monthly_table_data, colWidths=[2*inch, 1.5*inch, 1.5*inch, 1.5*inch])
            monthly_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('LINEABOVE', (0, -1), (-1, -1), 2, colors.black),
                ('BACKGROUND', (0, -1), (-1, -1), colors.lightgrey),
            ]))
            story.append(monthly_table)
        
        # Footer
        story.append(Spacer(1, 0.5*inch))
        footer = Paragraph(
            f"Relatório gerado em {datetime.now().strftime('%d/%m/%Y às %H:%M')}",
            self.styles['Footer']
        )
        story.append(footer)
        
        # Build PDF
        doc.build(story)
        buffer.seek(0)
        return buffer
    
    def _generate_cash_flow_pdf(self, account_balances, total_opening, total_closing,
                                daily_flow, inflows, outflows, start_date, end_date):
        """Generate PDF for Cash Flow report"""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        story = []
        
        # Title
        title = Paragraph(
            f"Relatório de Fluxo de Caixa - {self.company.name}",
            self.styles['CustomTitle']
        )
        story.append(title)
        
        # Period
        period = Paragraph(
            f"Período: {start_date.strftime('%d/%m/%Y')} a {end_date.strftime('%d/%m/%Y')}",
            self.styles['Normal']
        )
        story.append(period)
        story.append(Spacer(1, 0.5*inch))
        
        # Account Summary
        story.append(Paragraph("Resumo por Conta", self.styles['CustomHeading']))
        
        account_data = [['Conta', 'Saldo Inicial', 'Saldo Final', 'Variação']]
        for item in account_balances:
            account_data.append([
                self._get_account_display_name(item['account']),
                f"R$ {item['opening']:,.2f}",
                f"R$ {item['closing']:,.2f}",
                f"R$ {item['change']:,.2f}"
            ])
        
        # Add totals
        account_data.append([
            'TOTAL',
            f"R$ {total_opening:,.2f}",
            f"R$ {total_closing:,.2f}",
            f"R$ {total_closing - total_opening:,.2f}"
        ])
        
        account_table = Table(account_data, colWidths=[2.5*inch, 1.5*inch, 1.5*inch, 1.5*inch])
        account_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('LINEABOVE', (0, -1), (-1, -1), 2, colors.black),
            ('BACKGROUND', (0, -1), (-1, -1), colors.lightgrey),
        ]))
        story.append(account_table)
        story.append(Spacer(1, 0.5*inch))
        
        # Cash Flow Summary
        total_inflows = sum(item['total'] for item in inflows)
        total_outflows = sum(abs(item['total']) for item in outflows)  # Use absolute values
        net_flow = total_inflows - total_outflows
        
        story.append(Paragraph("Resumo do Fluxo", self.styles['CustomHeading']))
        
        flow_summary = [
            ['Entradas', f'R$ {total_inflows:,.2f}'],
            ['Saídas', f'R$ {total_outflows:,.2f}'],
            ['Fluxo Líquido', f'R$ {net_flow:,.2f}'],
        ]
        
        flow_table = Table(flow_summary, colWidths=[3*inch, 2*inch])
        flow_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 12),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('LINEBELOW', (0, 1), (-1, 1), 1, colors.black),
            ('LINEBELOW', (0, 2), (-1, 2), 2, colors.black),
        ]))
        story.append(flow_table)
        story.append(Spacer(1, 0.5*inch))
        
        # Inflows by category
        if inflows:
            story.append(Paragraph("Entradas por Categoria", self.styles['SectionHeading']))
            inflow_data = [['Categoria', 'Valor (R$)', '%']]
            
            for item in inflows[:10]:  # Top 10
                percentage = (item['total'] / total_inflows * 100) if total_inflows > 0 else 0
                inflow_data.append([
                    item['category__name'] or 'Sem categoria',
                    f"{item['total']:,.2f}",
                    f"{percentage:.1f}%"
                ])
            
            inflow_table = Table(inflow_data, colWidths=[3.5*inch, 1.5*inch, 1*inch])
            inflow_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.green),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ]))
            story.append(inflow_table)
            story.append(Spacer(1, 0.3*inch))
        
        # Outflows by category
        if outflows:
            story.append(Paragraph("Saídas por Categoria", self.styles['SectionHeading']))
            outflow_data = [['Categoria', 'Valor (R$)', '%']]
            
            for item in outflows[:10]:  # Top 10
                percentage = (abs(item['total']) / abs(total_outflows) * 100) if total_outflows != 0 else 0
                outflow_data.append([
                    item['category__name'] or 'Sem categoria',
                    f"{abs(item['total']):,.2f}",
                    f"{percentage:.1f}%"
                ])
            
            outflow_table = Table(outflow_data, colWidths=[3.5*inch, 1.5*inch, 1*inch])
            outflow_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.red),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ]))
            story.append(outflow_table)
        
        # Daily flow chart (simplified table version)
        if len(daily_flow) <= 31:  # Show daily detail for up to 31 days
            story.append(PageBreak())
            story.append(Paragraph("Fluxo Diário", self.styles['CustomHeading']))
            
            daily_data = [['Data', 'Entradas', 'Saídas', 'Saldo do Dia', 'Saldo Acumulado']]
            
            for day in daily_flow:
                daily_data.append([
                    day['date'].strftime('%d/%m'),
                    f"{day['inflow']:,.2f}" if day['inflow'] > 0 else '-',
                    f"{day['outflow']:,.2f}" if day['outflow'] > 0 else '-',
                    f"{day['net']:,.2f}",
                    f"{day['cumulative']:,.2f}"
                ])
            
            daily_table = Table(daily_data, colWidths=[1*inch, 1.3*inch, 1.3*inch, 1.3*inch, 1.5*inch])
            daily_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
            ]))
            story.append(daily_table)
        
        # Footer
        story.append(Spacer(1, 0.5*inch))
        footer = Paragraph(
            f"Relatório gerado em {datetime.now().strftime('%d/%m/%Y às %H:%M')}",
            self.styles['Footer']
        )
        story.append(footer)
        
        # Build PDF
        doc.build(story)
        buffer.seek(0)
        return buffer
    
    def _generate_monthly_summary_pdf(self, summary_stats, top_expenses, top_income,
                                     avg_daily_expense, avg_daily_income,
                                     category_breakdown, account_activity,
                                     start_date, end_date):
        """Generate PDF for Monthly Summary report"""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        story = []
        
        # Title
        title = Paragraph(
            f"Resumo Mensal - {self.company.name}",
            self.styles['CustomTitle']
        )
        story.append(title)
        
        # Period
        period = Paragraph(
            f"Período: {start_date.strftime('%d/%m/%Y')} a {end_date.strftime('%d/%m/%Y')}",
            self.styles['Normal']
        )
        story.append(period)
        story.append(Spacer(1, 0.5*inch))
        
        # Key Metrics
        story.append(Paragraph("Métricas Principais", self.styles['CustomHeading']))
        
        metrics_data = [
            ['Métrica', 'Valor'],
            ['Total de Transações', f"{summary_stats['total_count']}"],
            ['Receitas', f"R$ {summary_stats['total_income']:,.2f} ({summary_stats['income_count']} transações)"],
            ['Despesas', f"R$ {abs(summary_stats['total_expenses']):,.2f} ({summary_stats['expense_count']} transações)"],
            ['Resultado Líquido', f"R$ {summary_stats['net_balance']:,.2f}"],
            ['Média Diária de Receitas', f"R$ {avg_daily_income:,.2f}"],
            ['Média Diária de Despesas', f"R$ {abs(avg_daily_expense):,.2f}"],
        ]
        
        metrics_table = Table(metrics_data, colWidths=[3.5*inch, 3*inch])
        metrics_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
        ]))
        story.append(metrics_table)
        story.append(Spacer(1, 0.5*inch))
        
        # Top Expenses
        if top_expenses:
            story.append(Paragraph("10 Maiores Despesas", self.styles['SectionHeading']))
            expense_data = [['Data', 'Descrição', 'Categoria', 'Valor']]
            
            for trans in top_expenses:
                expense_data.append([
                    trans.transaction_date.strftime('%d/%m'),
                    trans.description[:40] + '...' if len(trans.description) > 40 else trans.description,
                    trans.category.name if trans.category else 'Sem categoria',
                    f"R$ {abs(trans.amount):,.2f}"
                ])
            
            expense_table = Table(expense_data, colWidths=[0.8*inch, 3*inch, 1.5*inch, 1.2*inch])
            expense_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.red),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('ALIGN', (-1, 0), (-1, -1), 'RIGHT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ]))
            story.append(expense_table)
            story.append(Spacer(1, 0.3*inch))
        
        # Top Income
        if top_income:
            story.append(Paragraph("10 Maiores Receitas", self.styles['SectionHeading']))
            income_data = [['Data', 'Descrição', 'Categoria', 'Valor']]
            
            for trans in top_income:
                income_data.append([
                    trans.transaction_date.strftime('%d/%m'),
                    trans.description[:40] + '...' if len(trans.description) > 40 else trans.description,
                    trans.category.name if trans.category else 'Sem categoria',
                    f"R$ {trans.amount:,.2f}"
                ])
            
            income_table = Table(income_data, colWidths=[0.8*inch, 3*inch, 1.5*inch, 1.2*inch])
            income_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.green),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('ALIGN', (-1, 0), (-1, -1), 'RIGHT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ]))
            story.append(income_table)
        
        # Category Breakdown
        if category_breakdown:
            story.append(PageBreak())
            story.append(Paragraph("Despesas por Categoria", self.styles['CustomHeading']))
            
            # Create pie chart
            drawing = Drawing(400, 200)
            pie = Pie()
            pie.x = 150
            pie.y = 50
            pie.width = 100
            pie.height = 100
            pie.data = [float(item['total']) for item in category_breakdown[:8]]  # Top 8
            pie.labels = [item['name'] for item in category_breakdown[:8]]
            pie.slices.strokeWidth = 0.5
            
            # Add colors
            pie_colors = [
                colors.HexColor('#FF6B6B'),
                colors.HexColor('#4ECDC4'),
                colors.HexColor('#45B7D1'),
                colors.HexColor('#96CEB4'),
                colors.HexColor('#FECA57'),
                colors.HexColor('#DDA0DD'),
                colors.HexColor('#98D8C8'),
                colors.HexColor('#FFD93D'),
            ]
            for i, color in enumerate(pie_colors[:len(pie.data)]):
                pie.slices[i].fillColor = color
            
            drawing.add(pie)
            story.append(drawing)
            
            # Category table
            cat_data = [['Categoria', 'Valor (R$)', 'Transações', '% do Total']]
            total_cat_expenses = sum(abs(item['total']) for item in category_breakdown)
            
            for item in category_breakdown[:10]:  # Top 10
                percentage = (abs(item['total']) / total_cat_expenses * 100) if total_cat_expenses > 0 else 0
                cat_data.append([
                    item['name'],
                    f"{abs(item['total']):,.2f}",
                    str(item['count']),
                    f"{percentage:.1f}%"
                ])
            
            cat_table = Table(cat_data, colWidths=[3*inch, 1.5*inch, 1*inch, 1*inch])
            cat_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ]))
            story.append(cat_table)
        
        # Account Activity
        if account_activity:
            story.append(Spacer(1, 0.5*inch))
            story.append(Paragraph("Atividade por Conta", self.styles['SectionHeading']))
            
            account_data = [['Conta', 'Transações', 'Créditos (R$)', 'Débitos (R$)']]
            
            for item in account_activity:
                account_name = item['bank_account__nickname'] or f"Conta {item['bank_account__id']}"
                account_data.append([
                    account_name,
                    str(item['transaction_count']),
                    f"{item['total_credits'] or 0:,.2f}",
                    f"{abs(item['total_debits']) if item['total_debits'] else 0:,.2f}"
                ])
            
            acc_table = Table(account_data, colWidths=[2.5*inch, 1*inch, 1.5*inch, 1.5*inch])
            acc_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ]))
            story.append(acc_table)
        
        # Footer
        story.append(Spacer(1, 0.5*inch))
        footer = Paragraph(
            f"Relatório gerado em {datetime.now().strftime('%d/%m/%Y às %H:%M')}",
            self.styles['Footer']
        )
        story.append(footer)
        
        # Build PDF
        doc.build(story)
        buffer.seek(0)
        return buffer
    
    def _generate_category_analysis_pdf(self, category_data, category_trends,
                                       total_expenses, start_date, end_date):
        """Generate PDF for Category Analysis report"""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        story = []
        
        # Title
        title = Paragraph(
            f"Análise por Categoria - {self.company.name}",
            self.styles['CustomTitle']
        )
        story.append(title)
        
        # Period
        period = Paragraph(
            f"Período: {start_date.strftime('%d/%m/%Y')} a {end_date.strftime('%d/%m/%Y')}",
            self.styles['Normal']
        )
        story.append(period)
        story.append(Spacer(1, 0.5*inch))
        
        # Summary
        story.append(Paragraph("Resumo Geral", self.styles['CustomHeading']))
        
        summary_data = [
            ['Total de Despesas', f'R$ {total_expenses:,.2f}'],
            ['Categorias Analisadas', str(len(category_data))],
            ['Média por Categoria', f'R$ {(total_expenses / len(category_data)):,.2f}' if category_data else 'R$ 0,00'],
        ]
        
        summary_table = Table(summary_data, colWidths=[3*inch, 2*inch])
        summary_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        story.append(summary_table)
        story.append(Spacer(1, 0.5*inch))
        
        # Category Details
        if category_data:
            story.append(Paragraph("Detalhamento por Categoria", self.styles['CustomHeading']))
            
            # Create pie chart
            drawing = Drawing(400, 200)
            pie = Pie()
            pie.x = 150
            pie.y = 50
            pie.width = 100
            pie.height = 100
            
            # Use top 8 categories for pie chart
            top_categories = category_data[:8]
            pie.data = [float(abs(item['total'])) for item in top_categories]
            pie.labels = [f"{item['category'].name} ({item['percentage']:.1f}%)" 
                         for item in top_categories]
            pie.slices.strokeWidth = 0.5
            
            # Add colors
            pie_colors = [
                colors.HexColor('#FF6B6B'),
                colors.HexColor('#4ECDC4'),
                colors.HexColor('#45B7D1'),
                colors.HexColor('#96CEB4'),
                colors.HexColor('#FECA57'),
                colors.HexColor('#DDA0DD'),
                colors.HexColor('#98D8C8'),
                colors.HexColor('#FFD93D'),
            ]
            for i, color in enumerate(pie_colors[:len(pie.data)]):
                pie.slices[i].fillColor = color
            
            drawing.add(pie)
            story.append(drawing)
            story.append(Spacer(1, 0.3*inch))
            
            # Detailed table
            detail_data = [['Categoria', 'Total (R$)', 'Qtd', 'Média (R$)', '% do Total']]
            
            for item in category_data:
                detail_data.append([
                    item['category'].name,
                    f"{abs(item['total']):,.2f}",
                    str(item['count']),
                    f"{abs(item['average']):,.2f}",
                    f"{item['percentage']:.1f}%"
                ])
            
            detail_table = Table(detail_data, colWidths=[2.5*inch, 1.3*inch, 0.7*inch, 1.2*inch, 0.8*inch])
            detail_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
            ]))
            story.append(detail_table)
        
        # Category Trends
        if category_trends and len(category_trends) > 0:
            story.append(PageBreak())
            story.append(Paragraph("Evolução Temporal por Categoria", self.styles['CustomHeading']))
            
            # Show trends for top 5 categories
            top_category_names = [item['category'].name for item in category_data[:5]]
            
            for cat_name in top_category_names:
                if cat_name in category_trends:
                    story.append(Paragraph(f"{cat_name}", self.styles['SectionHeading']))
                    
                    trend_data = [['Mês', 'Valor (R$)']]
                    months = sorted(category_trends[cat_name].keys())
                    
                    for month in months:
                        month_date = datetime.strptime(month, '%Y-%m')
                        trend_data.append([
                            month_date.strftime('%B %Y'),
                            f"{abs(category_trends[cat_name][month]):,.2f}"
                        ])
                    
                    trend_table = Table(trend_data, colWidths=[2*inch, 1.5*inch])
                    trend_table.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                        ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
                        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                        ('FONTSIZE', (0, 0), (-1, -1), 9),
                        ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ]))
                    story.append(trend_table)
                    story.append(Spacer(1, 0.2*inch))
        
        # Footer
        story.append(Spacer(1, 0.5*inch))
        footer = Paragraph(
            f"Relatório gerado em {datetime.now().strftime('%d/%m/%Y às %H:%M')}",
            self.styles['Footer']
        )
        story.append(footer)
        
        # Build PDF
        doc.build(story)
        buffer.seek(0)
        return buffer
    
    def _generate_transaction_pdf(self, transactions, start_date, end_date) -> io.BytesIO:
        """Generate PDF transaction report"""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        story = []
        
        # Title
        title = Paragraph(
            f"Relatório de Transações - {self.company.name}",
            self.styles['CustomTitle']
        )
        story.append(title)
        
        # Period
        period = Paragraph(
            f"Período: {start_date.strftime('%d/%m/%Y')} a {end_date.strftime('%d/%m/%Y')}",
            self.styles['Normal']
        )
        story.append(period)
        story.append(Spacer(1, 0.5*inch))
        
        # Summary statistics
        summary_data = self._calculate_summary_stats(transactions)
        story.append(Paragraph("Resumo", self.styles['CustomHeading']))
        
        summary_table_data = [
            ['Total de Transações', str(summary_data['total_count'])],
            ['Total de Receitas', f"R$ {summary_data['total_income']:,.2f}"],
            ['Total de Despesas', f"R$ {summary_data['total_expenses']:,.2f}"],
            ['Saldo Líquido', f"R$ {summary_data['net_balance']:,.2f}"],
        ]
        
        summary_table = Table(summary_table_data, colWidths=[3*inch, 2*inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(summary_table)
        story.append(Spacer(1, 0.5*inch))
        
        # Category breakdown
        category_data = self._calculate_category_breakdown(transactions)
        if category_data:
            story.append(Paragraph("Despesas por Categoria", self.styles['CustomHeading']))
            
            # Create pie chart
            drawing = Drawing(400, 200)
            pie = Pie()
            pie.x = 150
            pie.y = 50
            pie.width = 100
            pie.height = 100
            pie.data = [float(item['total']) for item in category_data[:8]]  # Top 8
            pie.labels = [item['name'] for item in category_data[:8]]
            pie.slices.strokeWidth = 0.5
            drawing.add(pie)
            story.append(drawing)
            story.append(Spacer(1, 0.3*inch))
        
        # Transaction list
        story.append(PageBreak())
        story.append(Paragraph("Detalhes das Transações", self.styles['CustomHeading']))
        
        # Table header
        table_data = [['Data', 'Descrição', 'Categoria', 'Conta', 'Tipo', 'Valor']]
        
        # Add transactions
        for trans in transactions[:100]:  # Limit to 100 for PDF
            table_data.append([
                trans.transaction_date.strftime('%d/%m/%Y'),
                trans.description[:40] + '...' if len(trans.description) > 40 else trans.description,
                trans.category.name if trans.category else 'Sem categoria',
                self._get_account_display_name(trans.bank_account),
                'Receita' if trans.transaction_type == 'credit' else 'Despesa',
                f"R$ {trans.amount:,.2f}"
            ])
        
        # Create table
        trans_table = Table(table_data, colWidths=[1.2*inch, 2.5*inch, 1.2*inch, 1.2*inch, 0.8*inch, 1.1*inch])
        trans_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (-1, 0), (-1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
        ]))
        story.append(trans_table)
        
        if transactions.count() > 100:
            story.append(Spacer(1, 0.2*inch))
            story.append(Paragraph(
                f"* Mostrando apenas as primeiras 100 transações de um total de {transactions.count()}",
                self.styles['Normal']
            ))
        
        # Footer
        story.append(Spacer(1, 0.5*inch))
        footer = Paragraph(
            f"Relatório gerado em {datetime.now().strftime('%d/%m/%Y às %H:%M')}",
            self.styles['Footer']
        )
        story.append(footer)
        
        # Build PDF
        doc.build(story)
        buffer.seek(0)
        return buffer
    
    # Excel Generation Methods
    def _generate_profit_loss_excel(self, revenue_by_category, expenses_by_category,
                                   total_revenue, total_expenses, gross_profit,
                                   monthly_data, start_date, end_date):
        """Generate Excel for Profit & Loss report"""
        buffer = io.BytesIO()
        workbook = xlsxwriter.Workbook(buffer, {'in_memory': True})
        
        # Formats
        header_format = workbook.add_format({
            'bold': True,
            'font_color': 'white',
            'bg_color': '#4F46E5',
            'align': 'center'
        })
        money_format = workbook.add_format({'num_format': 'R$ #,##0.00'})
        percent_format = workbook.add_format({'num_format': '0.0%'})
        date_format = workbook.add_format({'num_format': 'dd/mm/yyyy'})
        title_format = workbook.add_format({
            'bold': True,
            'font_size': 16,
            'align': 'center'
        })
        subtitle_format = workbook.add_format({
            'bold': True,
            'font_size': 12,
            'bg_color': '#E5E7EB'
        })
        
        # Summary Sheet
        sheet = workbook.add_worksheet('Resumo DRE')
        
        # Title
        sheet.merge_range('A1:D1', f'Demonstração de Resultados - {self.company.name}', title_format)
        sheet.merge_range('A2:D2', f'Período: {start_date.strftime("%d/%m/%Y")} a {end_date.strftime("%d/%m/%Y")}', workbook.add_format({'align': 'center'}))
        
        # Summary
        sheet.write('A4', 'RESUMO EXECUTIVO', subtitle_format)
        sheet.write('A5', 'Descrição')
        sheet.write('B5', 'Valor (R$)', header_format)
        sheet.write('C5', '% do Total', header_format)
        
        sheet.write('A6', 'RECEITAS')
        sheet.write('B6', total_revenue, money_format)
        sheet.write('C6', 1.0, percent_format)
        
        sheet.write('A7', 'DESPESAS')
        sheet.write('B7', -total_expenses, money_format)
        sheet.write('C7', (total_expenses / total_revenue) if total_revenue > 0 else 0, percent_format)
        
        sheet.write('A9', 'LUCRO/PREJUÍZO', workbook.add_format({'bold': True}))
        sheet.write('B9', gross_profit, workbook.add_format({'num_format': 'R$ #,##0.00', 'bold': True}))
        sheet.write('C9', gross_profit / total_revenue if total_revenue > 0 else 0, percent_format)
        
        # Revenue Details
        if revenue_by_category:
            row = 11
            sheet.write(f'A{row}', 'DETALHAMENTO DE RECEITAS', subtitle_format)
            row += 1
            sheet.write(f'A{row}', 'Categoria')
            sheet.write(f'B{row}', 'Valor (R$)', header_format)
            sheet.write(f'C{row}', 'Qtd', header_format)
            sheet.write(f'D{row}', '%', header_format)
            
            row += 1
            for item in revenue_by_category:
                sheet.write(f'A{row}', item['category__name'] or 'Sem categoria')
                sheet.write(f'B{row}', float(item['total']), money_format)
                sheet.write(f'C{row}', item['count'])
                sheet.write(f'D{row}', float(item['total']) / float(total_revenue) if total_revenue > 0 else 0, percent_format)
                row += 1
        
        # Expense Details
        if expenses_by_category:
            row += 2
            sheet.write(f'A{row}', 'DETALHAMENTO DE DESPESAS', subtitle_format)
            row += 1
            sheet.write(f'A{row}', 'Categoria')
            sheet.write(f'B{row}', 'Valor (R$)', header_format)
            sheet.write(f'C{row}', 'Qtd', header_format)
            sheet.write(f'D{row}', '%', header_format)
            
            row += 1
            for item in expenses_by_category:
                sheet.write(f'A{row}', item['category__name'] or 'Sem categoria')
                sheet.write(f'B{row}', float(item['total']), money_format)
                sheet.write(f'C{row}', item['count'])
                sheet.write(f'D{row}', float(item['total']) / float(total_expenses) if total_expenses > 0 else 0, percent_format)
                row += 1
        
        # Monthly Sheet
        if monthly_data:
            monthly_sheet = workbook.add_worksheet('Evolução Mensal')
            
            monthly_sheet.write('A1', 'EVOLUÇÃO MENSAL', subtitle_format)
            monthly_sheet.write('A2', 'Mês')
            monthly_sheet.write('B2', 'Receitas (R$)', header_format)
            monthly_sheet.write('C2', 'Despesas (R$)', header_format)
            monthly_sheet.write('D2', 'Resultado (R$)', header_format)
            
            row = 3
            for month in monthly_data:
                monthly_sheet.write(f'A{row}', month['month'])
                monthly_sheet.write(f'B{row}', float(month['income']), money_format)
                monthly_sheet.write(f'C{row}', float(month['expenses']), money_format)
                monthly_sheet.write(f'D{row}', float(month['profit']), money_format)
                row += 1
            
            # Totals
            monthly_sheet.write(f'A{row}', 'TOTAL', workbook.add_format({'bold': True}))
            monthly_sheet.write(f'B{row}', float(total_revenue), workbook.add_format({'num_format': 'R$ #,##0.00', 'bold': True}))
            monthly_sheet.write(f'C{row}', float(total_expenses), workbook.add_format({'num_format': 'R$ #,##0.00', 'bold': True}))
            monthly_sheet.write(f'D{row}', float(gross_profit), workbook.add_format({'num_format': 'R$ #,##0.00', 'bold': True}))
            
            # Auto-fit columns
            monthly_sheet.set_column('A:A', 15)
            monthly_sheet.set_column('B:D', 18)
        
        # Auto-fit columns
        sheet.set_column('A:A', 25)
        sheet.set_column('B:D', 15)
        
        workbook.close()
        buffer.seek(0)
        return buffer
    
    def _generate_cash_flow_excel(self, account_balances, total_opening, total_closing,
                                 daily_flow, inflows, outflows, start_date, end_date):
        """Generate Excel for Cash Flow report"""
        buffer = io.BytesIO()
        workbook = xlsxwriter.Workbook(buffer, {'in_memory': True})
        
        # Formats
        header_format = workbook.add_format({
            'bold': True,
            'font_color': 'white',
            'bg_color': '#4F46E5',
            'align': 'center'
        })
        money_format = workbook.add_format({'num_format': 'R$ #,##0.00'})
        date_format = workbook.add_format({'num_format': 'dd/mm/yyyy'})
        percent_format = workbook.add_format({'num_format': '0.0%'})
        
        # Account Summary Sheet
        sheet = workbook.add_worksheet('Resumo por Conta')
        
        sheet.write('A1', 'FLUXO DE CAIXA - RESUMO POR CONTA')
        sheet.write('A3', 'Conta')
        sheet.write('B3', 'Saldo Inicial', header_format)
        sheet.write('C3', 'Saldo Final', header_format)
        sheet.write('D3', 'Variação', header_format)
        
        row = 4
        for item in account_balances:
            sheet.write(f'A{row}', self._get_account_display_name(item['account']))
            sheet.write(f'B{row}', float(item['opening']), money_format)
            sheet.write(f'C{row}', float(item['closing']), money_format)
            sheet.write(f'D{row}', float(item['change']), money_format)
            row += 1
        
        # Totals
        sheet.write(f'A{row}', 'TOTAL', workbook.add_format({'bold': True}))
        sheet.write(f'B{row}', float(total_opening), workbook.add_format({'num_format': 'R$ #,##0.00', 'bold': True}))
        sheet.write(f'C{row}', float(total_closing), workbook.add_format({'num_format': 'R$ #,##0.00', 'bold': True}))
        sheet.write(f'D{row}', float(total_closing - total_opening), workbook.add_format({'num_format': 'R$ #,##0.00', 'bold': True}))
        
        # Flow Summary
        total_inflows = sum(item['total'] for item in inflows)
        total_outflows = sum(item['total'] for item in outflows)
        
        row += 3
        sheet.write(f'A{row}', 'RESUMO DO FLUXO')
        row += 1
        sheet.write(f'A{row}', 'Entradas')
        sheet.write(f'B{row}', float(total_inflows), money_format)
        row += 1
        sheet.write(f'A{row}', 'Saídas')
        sheet.write(f'B{row}', float(total_outflows), money_format)
        row += 1
        sheet.write(f'A{row}', 'Fluxo Líquido', workbook.add_format({'bold': True}))
        sheet.write(f'B{row}', float(total_inflows - total_outflows), workbook.add_format({'num_format': 'R$ #,##0.00', 'bold': True}))
        
        # Daily Flow Sheet
        if len(daily_flow) <= 31:
            daily_sheet = workbook.add_worksheet('Fluxo Diário')
            
            daily_sheet.write('A1', 'Data')
            daily_sheet.write('B1', 'Entradas', header_format)
            daily_sheet.write('C1', 'Saídas', header_format)
            daily_sheet.write('D1', 'Saldo do Dia', header_format)
            daily_sheet.write('E1', 'Saldo Acumulado', header_format)
            
            row = 2
            for day in daily_flow:
                daily_sheet.write(f'A{row}', day['date'], date_format)
                daily_sheet.write(f'B{row}', float(day['inflow']), money_format)
                daily_sheet.write(f'C{row}', float(day['outflow']), money_format)
                daily_sheet.write(f'D{row}', float(day['net']), money_format)
                daily_sheet.write(f'E{row}', float(day['cumulative']), money_format)
                row += 1
            
            daily_sheet.set_column('A:A', 12)
            daily_sheet.set_column('B:E', 18)
        
        # Categories Sheet
        cat_sheet = workbook.add_worksheet('Por Categoria')
        
        # Inflows
        cat_sheet.write('A1', 'ENTRADAS POR CATEGORIA')
        cat_sheet.write('A2', 'Categoria')
        cat_sheet.write('B2', 'Valor (R$)', header_format)
        cat_sheet.write('C2', '%', header_format)
        
        row = 3
        for item in inflows:
            cat_sheet.write(f'A{row}', item['category__name'] or 'Sem categoria')
            cat_sheet.write(f'B{row}', float(item['total']), money_format)
            cat_sheet.write(f'C{row}', float(item['total']) / float(total_inflows) if total_inflows > 0 else 0, percent_format)
            row += 1
        
        # Outflows
        row += 2
        cat_sheet.write(f'A{row}', 'SAÍDAS POR CATEGORIA')
        row += 1
        cat_sheet.write(f'A{row}', 'Categoria')
        cat_sheet.write(f'B{row}', 'Valor (R$)', header_format)
        cat_sheet.write(f'C{row}', '%', header_format)
        
        row += 1
        for item in outflows:
            cat_sheet.write(f'A{row}', item['category__name'] or 'Sem categoria')
            cat_sheet.write(f'B{row}', float(item['total']), money_format)
            cat_sheet.write(f'C{row}', float(item['total']) / float(total_outflows) if total_outflows > 0 else 0, percent_format)
            row += 1
        
        # Auto-fit columns
        sheet.set_column('A:A', 25)
        sheet.set_column('B:D', 18)
        cat_sheet.set_column('A:A', 25)
        cat_sheet.set_column('B:C', 18)
        
        workbook.close()
        buffer.seek(0)
        return buffer
    
    def _generate_monthly_summary_excel(self, summary_stats, top_expenses, top_income,
                                       avg_daily_expense, avg_daily_income,
                                       category_breakdown, account_activity,
                                       start_date, end_date):
        """Generate Excel for Monthly Summary report"""
        buffer = io.BytesIO()
        workbook = xlsxwriter.Workbook(buffer, {'in_memory': True})
        
        # Formats
        header_format = workbook.add_format({
            'bold': True,
            'font_color': 'white',
            'bg_color': '#4F46E5',
            'align': 'center'
        })
        money_format = workbook.add_format({'num_format': 'R$ #,##0.00'})
        date_format = workbook.add_format({'num_format': 'dd/mm/yyyy'})
        
        # Summary Sheet
        sheet = workbook.add_worksheet('Resumo')
        
        sheet.write('A1', 'RESUMO MENSAL')
        sheet.write('A3', 'Métrica')
        sheet.write('B3', 'Valor')
        
        metrics = [
            ('Total de Transações', summary_stats['total_count']),
            ('Receitas', f"R$ {summary_stats['total_income']:,.2f} ({summary_stats['income_count']} transações)"),
            ('Despesas', f"R$ {abs(summary_stats['total_expenses']):,.2f} ({summary_stats['expense_count']} transações)"),
            ('Resultado Líquido', f"R$ {summary_stats['net_balance']:,.2f}"),
            ('Média Diária de Receitas', f"R$ {avg_daily_income:,.2f}"),
            ('Média Diária de Despesas', f"R$ {abs(avg_daily_expense):,.2f}"),
        ]
        
        row = 4
        for metric, value in metrics:
            sheet.write(f'A{row}', metric)
            sheet.write(f'B{row}', value)
            row += 1
        
        # Top Transactions Sheet
        trans_sheet = workbook.add_worksheet('Top Transações')
        
        # Top Expenses
        trans_sheet.write('A1', 'TOP 10 MAIORES DESPESAS')
        trans_sheet.write('A2', 'Data')
        trans_sheet.write('B2', 'Descrição')
        trans_sheet.write('C2', 'Categoria')
        trans_sheet.write('D2', 'Valor', header_format)
        
        row = 3
        for trans in top_expenses:
            trans_sheet.write(f'A{row}', trans.transaction_date, date_format)
            trans_sheet.write(f'B{row}', trans.description)
            trans_sheet.write(f'C{row}', trans.category.name if trans.category else 'Sem categoria')
            trans_sheet.write(f'D{row}', float(trans.amount), money_format)
            row += 1
        
        # Top Income
        row += 2
        trans_sheet.write(f'A{row}', 'TOP 10 MAIORES RECEITAS')
        row += 1
        trans_sheet.write(f'A{row}', 'Data')
        trans_sheet.write(f'B{row}', 'Descrição')
        trans_sheet.write(f'C{row}', 'Categoria')
        trans_sheet.write(f'D{row}', 'Valor', header_format)
        
        row += 1
        for trans in top_income:
            trans_sheet.write(f'A{row}', trans.transaction_date, date_format)
            trans_sheet.write(f'B{row}', trans.description)
            trans_sheet.write(f'C{row}', trans.category.name if trans.category else 'Sem categoria')
            trans_sheet.write(f'D{row}', float(trans.amount), money_format)
            row += 1
        
        # Categories Sheet
        if category_breakdown:
            cat_sheet = workbook.add_worksheet('Por Categoria')
            
            cat_sheet.write('A1', 'DESPESAS POR CATEGORIA')
            cat_sheet.write('A2', 'Categoria')
            cat_sheet.write('B2', 'Valor (R$)', header_format)
            cat_sheet.write('C2', 'Transações', header_format)
            cat_sheet.write('D2', '% do Total', header_format)
            
            total_cat_expenses = sum(abs(item['total']) for item in category_breakdown)
            row = 3
            
            for item in category_breakdown:
                percentage = (abs(item['total']) / total_cat_expenses * 100) if total_cat_expenses > 0 else 0
                cat_sheet.write(f'A{row}', item['name'])
                cat_sheet.write(f'B{row}', float(abs(item['total'])), money_format)
                cat_sheet.write(f'C{row}', item['count'])
                cat_sheet.write(f'D{row}', f"{percentage:.1f}%")
                row += 1
            
            cat_sheet.set_column('A:A', 25)
            cat_sheet.set_column('B:D', 15)
        
        # Auto-fit columns
        sheet.set_column('A:A', 30)
        sheet.set_column('B:B', 40)
        trans_sheet.set_column('A:A', 12)
        trans_sheet.set_column('B:B', 50)
        trans_sheet.set_column('C:C', 20)
        trans_sheet.set_column('D:D', 15)
        
        workbook.close()
        buffer.seek(0)
        return buffer
    
    def _generate_category_analysis_excel(self, category_data, category_trends,
                                         total_expenses, start_date, end_date):
        """Generate Excel for Category Analysis report"""
        buffer = io.BytesIO()
        workbook = xlsxwriter.Workbook(buffer, {'in_memory': True})
        
        # Formats
        header_format = workbook.add_format({
            'bold': True,
            'font_color': 'white',
            'bg_color': '#4F46E5',
            'align': 'center'
        })
        money_format = workbook.add_format({'num_format': 'R$ #,##0.00'})
        percent_format = workbook.add_format({'num_format': '0.0%'})
        
        # Summary Sheet
        sheet = workbook.add_worksheet('Análise de Categorias')
        
        sheet.write('A1', 'ANÁLISE POR CATEGORIA')
        sheet.write('A3', 'Total de Despesas')
        sheet.write('B3', float(total_expenses), money_format)
        sheet.write('A4', 'Categorias Analisadas')
        sheet.write('B4', len(category_data))
        sheet.write('A5', 'Média por Categoria')
        sheet.write('B5', float(total_expenses / len(category_data)) if category_data else 0, money_format)
        
        # Category Details
        sheet.write('A7', 'DETALHAMENTO')
        sheet.write('A8', 'Categoria')
        sheet.write('B8', 'Total (R$)', header_format)
        sheet.write('C8', 'Qtd', header_format)
        sheet.write('D8', 'Média (R$)', header_format)
        sheet.write('E8', '% do Total', header_format)
        
        row = 9
        for item in category_data:
            sheet.write(f'A{row}', item['category'].name)
            sheet.write(f'B{row}', float(item['total']), money_format)
            sheet.write(f'C{row}', item['count'])
            sheet.write(f'D{row}', float(item['average']), money_format)
            sheet.write(f'E{row}', item['percentage'] / 100, percent_format)
            row += 1
        
        # Trends Sheet
        if category_trends:
            trends_sheet = workbook.add_worksheet('Tendências')
            
            # Get all months
            all_months = set()
            for cat_months in category_trends.values():
                all_months.update(cat_months.keys())
            months = sorted(all_months)
            
            # Header
            trends_sheet.write('A1', 'Categoria')
            col = 1
            for month in months:
                month_date = datetime.strptime(month, '%Y-%m')
                trends_sheet.write(0, col, month_date.strftime('%b %Y'), header_format)
                col += 1
            
            # Data
            row = 1
            for cat_name, monthly_data in category_trends.items():
                trends_sheet.write(row, 0, cat_name)
                col = 1
                for month in months:
                    if month in monthly_data:
                        trends_sheet.write(row, col, float(monthly_data[month]), money_format)
                    else:
                        trends_sheet.write(row, col, 0, money_format)
                    col += 1
                row += 1
            
            trends_sheet.set_column('A:A', 25)
            trends_sheet.set_column('B:Z', 15)
        
        # Auto-fit columns
        sheet.set_column('A:A', 25)
        sheet.set_column('B:E', 15)
        
        workbook.close()
        buffer.seek(0)
        return buffer
    
    def _generate_transaction_excel(self, transactions, start_date, end_date) -> io.BytesIO:
        """Generate Excel transaction report"""
        buffer = io.BytesIO()
        workbook = xlsxwriter.Workbook(buffer, {'in_memory': True})
        
        # Formats
        header_format = workbook.add_format({
            'bold': True,
            'font_color': 'white',
            'bg_color': '#4F46E5',
            'align': 'center'
        })
        money_format = workbook.add_format({'num_format': 'R$ #,##0.00'})
        date_format = workbook.add_format({'num_format': 'dd/mm/yyyy'})
        
        # Summary Sheet
        summary_sheet = workbook.add_worksheet('Resumo')
        
        # Title
        summary_sheet.write('A1', f'Relatório de Transações - {self.company.name}')
        summary_sheet.write('A2', f'Período: {start_date.strftime("%d/%m/%Y")} a {end_date.strftime("%d/%m/%Y")}')
        
        # Summary
        summary_data = self._calculate_summary_stats(transactions)
        
        summary_sheet.write('A4', 'Total de Transações:')
        summary_sheet.write('B4', summary_data['total_count'])
        summary_sheet.write('A5', 'Total de Receitas:')
        summary_sheet.write('B5', float(summary_data['total_income']), money_format)
        summary_sheet.write('A6', 'Total de Despesas:')
        summary_sheet.write('B6', float(summary_data['total_expenses']), money_format)
        summary_sheet.write('A7', 'Saldo Líquido:')
        summary_sheet.write('B7', float(summary_data['net_balance']), money_format)
        
        # Transactions Sheet
        trans_sheet = workbook.add_worksheet('Transações')
        
        # Headers
        headers = ['Data', 'Descrição', 'Categoria', 'Conta', 'Tipo', 'Valor']
        for col, header in enumerate(headers):
            trans_sheet.write(0, col, header, header_format)
        
        # Data
        row = 1
        for trans in transactions:
            trans_sheet.write(row, 0, trans.transaction_date, date_format)
            trans_sheet.write(row, 1, trans.description)
            trans_sheet.write(row, 2, trans.category.name if trans.category else 'Sem categoria')
            trans_sheet.write(row, 3, self._get_account_display_name(trans.bank_account))
            trans_sheet.write(row, 4, 'Receita' if trans.transaction_type == 'credit' else 'Despesa')
            trans_sheet.write(row, 5, float(trans.amount), money_format)
            row += 1
        
        # Auto-fit columns
        trans_sheet.set_column('A:A', 12)
        trans_sheet.set_column('B:B', 50)
        trans_sheet.set_column('C:C', 20)
        trans_sheet.set_column('D:D', 20)
        trans_sheet.set_column('E:E', 10)
        trans_sheet.set_column('F:F', 15)
        
        summary_sheet.set_column('A:A', 20)
        summary_sheet.set_column('B:B', 20)
        
        workbook.close()
        buffer.seek(0)
        return buffer