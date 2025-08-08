"""
Base report generator class
"""
import io
import logging
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Any, Optional, Tuple
from abc import ABC, abstractmethod

from django.db.models import QuerySet, Sum, Count, Avg, Q
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.units import inch
import xlsxwriter

from apps.banking.models import Transaction, BankAccount
from apps.reports.constants import TransactionType

logger = logging.getLogger(__name__)


class BaseReportGenerator(ABC):
    """Base class for all report generators"""
    
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
    
    @abstractmethod
    def generate(
        self,
        start_date: date,
        end_date: date,
        format: str = 'pdf',
        filters: Optional[Dict] = None
    ) -> io.BytesIO:
        """Generate the report - must be implemented by subclasses"""
        pass
    
    def _get_filtered_transactions(
        self, 
        start_date: date, 
        end_date: date, 
        filters: Optional[Dict] = None
    ) -> QuerySet:
        """Get filtered transactions with optimized queries"""
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
    
    def _calculate_summary_stats(self, transactions: QuerySet) -> Dict[str, Any]:
        """Calculate summary statistics for transactions"""
        income = transactions.filter(
            transaction_type__in=TransactionType.income_types()
        ).aggregate(
            total=Sum('amount'), count=Count('id')
        )
        expenses = transactions.filter(
            transaction_type__in=TransactionType.expense_types()
        ).aggregate(
            total=Sum('amount'), count=Count('id')
        )
        
        total_income = income['total'] or Decimal('0')
        total_expenses = expenses['total'] or Decimal('0')
        
        return {
            'total_count': transactions.count(),
            'total_income': total_income,
            'total_expenses': abs(total_expenses),  # Convert to positive for display
            'net_balance': total_income - abs(total_expenses),
            'income_count': income['count'] or 0,
            'expense_count': expenses['count'] or 0
        }
    
    def _get_account_display_name(self, account: BankAccount) -> str:
        """Get display name for bank account"""
        if hasattr(account, 'name') and account.name:
            return account.name
        elif hasattr(account, 'alias') and account.alias:
            return account.alias
        else:
            # Construct name based on bank and type
            bank_name = account.bank_provider.name if hasattr(account, 'bank_provider') else 'Banco'
            account_type = account.get_account_type_display() if hasattr(account, 'get_account_type_display') else account.account_type
            return f"{bank_name} - {account_type}"
    
    def _create_pdf_document(self, buffer: io.BytesIO) -> SimpleDocTemplate:
        """Create a PDF document with standard settings"""
        return SimpleDocTemplate(buffer, pagesize=A4)
    
    def _create_excel_workbook(self, buffer: io.BytesIO) -> xlsxwriter.Workbook:
        """Create an Excel workbook with standard settings"""
        return xlsxwriter.Workbook(buffer, {'in_memory': True})
    
    def _get_standard_excel_formats(self, workbook: xlsxwriter.Workbook) -> Dict[str, Any]:
        """Get standard Excel formats"""
        return {
            'header': workbook.add_format({
                'bold': True,
                'font_color': 'white',
                'bg_color': '#4F46E5',
                'align': 'center'
            }),
            'money': workbook.add_format({'num_format': 'R$ #,##0.00'}),
            'percent': workbook.add_format({'num_format': '0.0%'}),
            'date': workbook.add_format({'num_format': 'dd/mm/yyyy'}),
            'title': workbook.add_format({
                'bold': True,
                'font_size': 16,
                'align': 'center'
            }),
            'subtitle': workbook.add_format({
                'bold': True,
                'font_size': 12,
                'bg_color': '#E5E7EB'
            }),
        }
    
    def _add_pdf_footer(self, story: List) -> None:
        """Add standard footer to PDF"""
        story.append(Spacer(1, 0.5*inch))
        footer = Paragraph(
            f"Relatório gerado em {datetime.now().strftime('%d/%m/%Y às %H:%M')}",
            self.styles['Footer']
        )
        story.append(footer)