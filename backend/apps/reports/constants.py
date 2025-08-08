"""
Report constants and enums
"""
from enum import Enum
from typing import List, Tuple


class TransactionType(Enum):
    """Transaction type constants"""
    # Income types
    CREDIT = 'credit'
    TRANSFER_IN = 'transfer_in'
    PIX_IN = 'pix_in'
    INTEREST = 'interest'
    
    # Expense types
    DEBIT = 'debit'
    TRANSFER_OUT = 'transfer_out'
    PIX_OUT = 'pix_out'
    FEE = 'fee'
    
    @classmethod
    def income_types(cls) -> List[str]:
        """Get all income transaction types"""
        return [cls.CREDIT.value, cls.TRANSFER_IN.value, cls.PIX_IN.value, cls.INTEREST.value]
    
    @classmethod
    def expense_types(cls) -> List[str]:
        """Get all expense transaction types"""
        return [cls.DEBIT.value, cls.TRANSFER_OUT.value, cls.PIX_OUT.value, cls.FEE.value]


class ReportPeriod(Enum):
    """Common report periods"""
    CURRENT_MONTH = 'current_month'
    LAST_MONTH = 'last_month'
    QUARTERLY = 'quarterly'
    YEAR_TO_DATE = 'year_to_date'
    CUSTOM = 'custom'


# Report type display names
REPORT_TYPE_DISPLAY = {
    'monthly_summary': 'Resumo Mensal',
    'quarterly_report': 'Relatório Trimestral',
    'annual_report': 'Relatório Anual',
    'cash_flow': 'Fluxo de Caixa',
    'profit_loss': 'DRE - Demonstração de Resultados',
    'category_analysis': 'Análise por Categoria',
    'tax_report': 'Relatório Fiscal',
    'custom': 'Personalizado',
}

# Maximum report period in days
MAX_REPORT_PERIOD_DAYS = 365

# Cache timeouts (in seconds)
CACHE_TIMEOUT_SHORT = 60 * 5  # 5 minutes
CACHE_TIMEOUT_MEDIUM = 60 * 60  # 1 hour
CACHE_TIMEOUT_LONG = 60 * 60 * 24  # 24 hours

# Pagination settings
DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100

# File size limits
MAX_REPORT_FILE_SIZE = 50 * 1024 * 1024  # 50MB