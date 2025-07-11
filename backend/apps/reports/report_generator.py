"""
Report generation service for creating PDF and Excel reports
"""
import io
import logging
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Any, Optional

from django.conf import settings
from django.db.models import Sum, Count, Avg, Q
from django.utils import timezone

# PDF generation
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak, Image
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.charts.piecharts import Pie
from reportlab.graphics.charts.barcharts import VerticalBarChart

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
    
    def generate_transaction_report(
        self, 
        start_date: datetime,
        end_date: datetime,
        format: str = 'pdf',
        filters: Optional[Dict] = None
    ) -> io.BytesIO:
        """Generate transaction report in PDF or Excel format"""
        
        # Get transactions
        transactions = Transaction.objects.filter(
            bank_account__company=self.company,
            transaction_date__gte=start_date,
            transaction_date__lte=end_date
        )
        
        # Apply filters
        if filters:
            if filters.get('category_id'):
                transactions = transactions.filter(category_id=filters['category_id'])
            if filters.get('account_id'):
                transactions = transactions.filter(bank_account_id=filters['account_id'])
            if filters.get('transaction_type'):
                transactions = transactions.filter(transaction_type=filters['transaction_type'])
        
        transactions = transactions.select_related('category', 'bank_account').order_by('-transaction_date')
        
        if format == 'pdf':
            return self._generate_transaction_pdf(transactions, start_date, end_date)
        else:
            return self._generate_transaction_excel(transactions, start_date, end_date)
    
    def _generate_transaction_pdf(self, transactions, start_date, end_date) -> io.BytesIO:
        """Generate PDF transaction report"""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        story = []
        
        # Title
        title = Paragraph(
            f"Transaction Report - {self.company.name}",
            self.styles['CustomTitle']
        )
        story.append(title)
        
        # Period
        period = Paragraph(
            f"Period: {start_date.strftime('%B %d, %Y')} to {end_date.strftime('%B %d, %Y')}",
            self.styles['Normal']
        )
        story.append(period)
        story.append(Spacer(1, 0.5*inch))
        
        # Summary statistics
        summary_data = self._calculate_summary_stats(transactions)
        story.append(Paragraph("Summary", self.styles['CustomHeading']))
        
        summary_table_data = [
            ['Total Transactions', str(summary_data['total_count'])],
            ['Total Income', f"R$ {summary_data['total_income']:,.2f}"],
            ['Total Expenses', f"R$ {summary_data['total_expenses']:,.2f}"],
            ['Net Balance', f"R$ {summary_data['net_balance']:,.2f}"],
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
            story.append(Paragraph("Expenses by Category", self.styles['CustomHeading']))
            
            # Create pie chart
            drawing = Drawing(400, 200)
            pie = Pie()
            pie.x = 150
            pie.y = 50
            pie.width = 100
            pie.height = 100
            pie.data = [float(item['total']) for item in category_data]
            pie.labels = [item['name'] for item in category_data]
            pie.slices.strokeWidth = 0.5
            drawing.add(pie)
            story.append(drawing)
            story.append(Spacer(1, 0.3*inch))
        
        # Transaction list
        story.append(PageBreak())
        story.append(Paragraph("Transaction Details", self.styles['CustomHeading']))
        
        # Table header
        table_data = [['Date', 'Description', 'Category', 'Account', 'Type', 'Amount']]
        
        # Add transactions
        for trans in transactions[:100]:  # Limit to 100 for PDF
            table_data.append([
                trans.transaction_date.strftime('%Y-%m-%d'),
                trans.description[:40] + '...' if len(trans.description) > 40 else trans.description,
                trans.category.name if trans.category else 'Uncategorized',
                trans.bank_account.get_display_name(),
                trans.transaction_type.title(),
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
        ]))
        story.append(trans_table)
        
        # Build PDF
        doc.build(story)
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
            'align': 'center',
            'valign': 'vcenter'
        })
        
        money_format = workbook.add_format({'num_format': 'R$ #,##0.00'})
        date_format = workbook.add_format({'num_format': 'dd/mm/yyyy'})
        
        # Summary sheet
        summary_sheet = workbook.add_worksheet('Summary')
        summary_data = self._calculate_summary_stats(transactions)
        
        summary_sheet.write('A1', 'Transaction Report', header_format)
        summary_sheet.write('A2', f'{self.company.name}')
        summary_sheet.write('A3', f'Period: {start_date.strftime("%B %d, %Y")} to {end_date.strftime("%B %d, %Y")}')
        
        summary_sheet.write('A5', 'Summary Statistics', header_format)
        summary_sheet.write('A6', 'Total Transactions:')
        summary_sheet.write('B6', summary_data['total_count'])
        summary_sheet.write('A7', 'Total Income:')
        summary_sheet.write('B7', summary_data['total_income'], money_format)
        summary_sheet.write('A8', 'Total Expenses:')
        summary_sheet.write('B8', summary_data['total_expenses'], money_format)
        summary_sheet.write('A9', 'Net Balance:')
        summary_sheet.write('B9', summary_data['net_balance'], money_format)
        
        # Category breakdown
        category_data = self._calculate_category_breakdown(transactions)
        if category_data:
            summary_sheet.write('A11', 'Expenses by Category', header_format)
            summary_sheet.write('A12', 'Category')
            summary_sheet.write('B12', 'Amount')
            summary_sheet.write('C12', 'Count')
            
            row = 13
            for cat in category_data:
                summary_sheet.write(f'A{row}', cat['name'])
                summary_sheet.write(f'B{row}', float(cat['total']), money_format)
                summary_sheet.write(f'C{row}', cat['count'])
                row += 1
            
            # Add chart
            chart = workbook.add_chart({'type': 'pie'})
            chart.add_series({
                'categories': f'=Summary!$A$13:$A${row-1}',
                'values': f'=Summary!$B$13:$B${row-1}',
                'name': 'Expenses by Category'
            })
            chart.set_title({'name': 'Expense Distribution'})
            summary_sheet.insert_chart('E12', chart)
        
        # Transactions sheet
        trans_sheet = workbook.add_worksheet('Transactions')
        
        # Headers
        headers = ['Date', 'Description', 'Category', 'Account', 'Type', 'Amount']
        for col, header in enumerate(headers):
            trans_sheet.write(0, col, header, header_format)
        
        # Data
        row = 1
        for trans in transactions:
            trans_sheet.write(row, 0, trans.transaction_date, date_format)
            trans_sheet.write(row, 1, trans.description)
            trans_sheet.write(row, 2, trans.category.name if trans.category else 'Uncategorized')
            trans_sheet.write(row, 3, trans.bank_account.get_display_name())
            trans_sheet.write(row, 4, trans.transaction_type.title())
            trans_sheet.write(row, 5, float(trans.amount), money_format)
            row += 1
        
        # Auto-fit columns
        trans_sheet.set_column('A:A', 12)
        trans_sheet.set_column('B:B', 40)
        trans_sheet.set_column('C:C', 20)
        trans_sheet.set_column('D:D', 20)
        trans_sheet.set_column('E:E', 10)
        trans_sheet.set_column('F:F', 15)
        
        # Add filters
        trans_sheet.autofilter(0, 0, row-1, 5)
        
        workbook.close()
        buffer.seek(0)
        return buffer
    
    def _calculate_summary_stats(self, transactions) -> Dict[str, Any]:
        """Calculate summary statistics for transactions"""
        income = transactions.filter(transaction_type='credit').aggregate(
            total=Sum('amount'), count=Count('id')
        )
        expenses = transactions.filter(transaction_type='debit').aggregate(
            total=Sum('amount'), count=Count('id')
        )
        
        return {
            'total_count': transactions.count(),
            'total_income': income['total'] or Decimal('0'),
            'total_expenses': expenses['total'] or Decimal('0'),
            'net_balance': (income['total'] or Decimal('0')) - (expenses['total'] or Decimal('0'))
        }
    
    def _calculate_category_breakdown(self, transactions) -> List[Dict[str, Any]]:
        """Calculate expense breakdown by category"""
        expenses = transactions.filter(transaction_type='debit')
        
        category_data = expenses.values('category__name').annotate(
            total=Sum('amount'),
            count=Count('id')
        ).order_by('-total')
        
        return [
            {
                'name': item['category__name'] or 'Uncategorized',
                'total': item['total'],
                'count': item['count']
            }
            for item in category_data
        ]
    
    def generate_account_statement(
        self,
        account_id: int,
        start_date: datetime,
        end_date: datetime,
        format: str = 'pdf'
    ) -> io.BytesIO:
        """Generate bank account statement"""
        
        account = BankAccount.objects.get(id=account_id, company=self.company)
        transactions = Transaction.objects.filter(
            bank_account=account,
            transaction_date__gte=start_date,
            transaction_date__lte=end_date
        ).order_by('transaction_date')
        
        if format == 'pdf':
            return self._generate_statement_pdf(account, transactions, start_date, end_date)
        else:
            return self._generate_statement_excel(account, transactions, start_date, end_date)
    
    def _generate_statement_pdf(self, account, transactions, start_date, end_date) -> io.BytesIO:
        """Generate PDF bank statement"""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        story = []
        
        # Header
        story.append(Paragraph(f"Bank Statement - {account.get_display_name()}", self.styles['CustomTitle']))
        story.append(Paragraph(f"{self.company.name}", self.styles['Normal']))
        story.append(Paragraph(
            f"Period: {start_date.strftime('%B %d, %Y')} to {end_date.strftime('%B %d, %Y')}",
            self.styles['Normal']
        ))
        story.append(Spacer(1, 0.5*inch))
        
        # Account info
        info_data = [
            ['Bank:', account.bank_provider.name],
            ['Account Type:', account.get_account_type_display()],
            ['Account Number:', f"****{account.account_number[-4:]}"],
            ['Opening Balance:', f"R$ {account.get_balance_at_date(start_date):,.2f}"],
            ['Closing Balance:', f"R$ {account.get_balance_at_date(end_date):,.2f}"],
        ]
        
        info_table = Table(info_data, colWidths=[2*inch, 3*inch])
        info_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        story.append(info_table)
        story.append(Spacer(1, 0.5*inch))
        
        # Transactions
        story.append(Paragraph("Transaction History", self.styles['CustomHeading']))
        
        # Calculate running balance
        running_balance = account.get_balance_at_date(start_date)
        
        table_data = [['Date', 'Description', 'Debit', 'Credit', 'Balance']]
        
        for trans in transactions:
            if trans.transaction_type == 'debit':
                running_balance -= trans.amount
                debit = f"R$ {trans.amount:,.2f}"
                credit = ''
            else:
                running_balance += trans.amount
                debit = ''
                credit = f"R$ {trans.amount:,.2f}"
            
            table_data.append([
                trans.transaction_date.strftime('%Y-%m-%d'),
                trans.description[:50] + '...' if len(trans.description) > 50 else trans.description,
                debit,
                credit,
                f"R$ {running_balance:,.2f}"
            ])
        
        trans_table = Table(table_data, colWidths=[1.2*inch, 3*inch, 1.2*inch, 1.2*inch, 1.4*inch])
        trans_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (2, 0), (-1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
        ]))
        story.append(trans_table)
        
        # Build PDF
        doc.build(story)
        buffer.seek(0)
        return buffer
    
    def _generate_statement_excel(self, account, transactions, start_date, end_date) -> io.BytesIO:
        """Generate Excel bank statement"""
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
        
        # Sheet
        sheet = workbook.add_worksheet('Statement')
        
        # Header
        sheet.write('A1', f'Bank Statement - {account.get_display_name()}')
        sheet.write('A2', self.company.name)
        sheet.write('A3', f'Period: {start_date.strftime("%B %d, %Y")} to {end_date.strftime("%B %d, %Y")}')
        
        # Account info
        sheet.write('A5', 'Bank:')
        sheet.write('B5', account.bank_provider.name)
        sheet.write('A6', 'Account Type:')
        sheet.write('B6', account.get_account_type_display())
        sheet.write('A7', 'Opening Balance:')
        sheet.write('B7', float(account.get_balance_at_date(start_date)), money_format)
        sheet.write('A8', 'Closing Balance:')
        sheet.write('B8', float(account.get_balance_at_date(end_date)), money_format)
        
        # Transactions
        headers = ['Date', 'Description', 'Debit', 'Credit', 'Balance']
        for col, header in enumerate(headers):
            sheet.write(10, col, header, header_format)
        
        running_balance = account.get_balance_at_date(start_date)
        row = 11
        
        for trans in transactions:
            sheet.write(row, 0, trans.transaction_date, date_format)
            sheet.write(row, 1, trans.description)
            
            if trans.transaction_type == 'debit':
                running_balance -= trans.amount
                sheet.write(row, 2, float(trans.amount), money_format)
                sheet.write(row, 3, '')
            else:
                running_balance += trans.amount
                sheet.write(row, 2, '')
                sheet.write(row, 3, float(trans.amount), money_format)
            
            sheet.write(row, 4, float(running_balance), money_format)
            row += 1
        
        # Auto-fit columns
        sheet.set_column('A:A', 12)
        sheet.set_column('B:B', 50)
        sheet.set_column('C:E', 15)
        
        workbook.close()
        buffer.seek(0)
        return buffer