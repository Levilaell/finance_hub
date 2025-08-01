"""
Validation service for report generation
Comprehensive input validation and sanitization
"""
import re
from datetime import datetime, date, timedelta
from typing import Dict, Any, Optional, List, Tuple
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.utils import timezone

from apps.reports.exceptions import (
    InvalidReportPeriodError,
    ReportDataInsufficientError
)
from apps.reports.models import Report


class ReportValidationService:
    """Service for validating report generation inputs"""
    
    # Maximum report period in days
    MAX_REPORT_PERIOD_DAYS = 365
    MIN_REPORT_PERIOD_DAYS = 1
    
    # Valid report types
    VALID_REPORT_TYPES = [
        'monthly_summary',
        'quarterly_report',
        'annual_report',
        'cash_flow',
        'profit_loss',
        'category_analysis',
        'tax_report',
        'custom'
    ]
    
    # Valid file formats
    VALID_FILE_FORMATS = ['pdf', 'xlsx', 'csv', 'json']
    
    # Parameter limits
    MAX_CATEGORIES = 50
    MAX_ACCOUNTS = 20
    MAX_TITLE_LENGTH = 200
    MAX_DESCRIPTION_LENGTH = 1000
    
    @classmethod
    def validate_report_request(cls, data: Dict[str, Any], company: Any) -> Dict[str, Any]:
        """
        Validate complete report generation request
        
        Args:
            data: Request data
            company: Company instance
            
        Returns:
            Validated and sanitized data
            
        Raises:
            ValidationError: If validation fails
        """
        validated_data = {}
        
        # Validate report type
        validated_data['report_type'] = cls._validate_report_type(
            data.get('report_type')
        )
        
        # Validate date range
        period_start, period_end = cls._validate_date_range(
            data.get('period_start'),
            data.get('period_end')
        )
        validated_data['period_start'] = period_start
        validated_data['period_end'] = period_end
        
        # Validate file format
        validated_data['file_format'] = cls._validate_file_format(
            data.get('file_format', 'pdf')
        )
        
        # Validate title and description
        validated_data['title'] = cls._validate_string_field(
            data.get('title'),
            'title',
            max_length=cls.MAX_TITLE_LENGTH,
            required=False,
            default=f"{validated_data['report_type']} - {period_start} to {period_end}"
        )
        
        validated_data['description'] = cls._validate_string_field(
            data.get('description'),
            'description',
            max_length=cls.MAX_DESCRIPTION_LENGTH,
            required=False,
            default=''
        )
        
        # Validate filters
        validated_data['filters'] = cls._validate_filters(
            data.get('filters', {})
        )
        
        # Validate parameters
        validated_data['parameters'] = cls._validate_parameters(
            data.get('parameters', {}),
            validated_data['report_type']
        )
        
        # Validate data sufficiency
        cls._validate_data_sufficiency(
            company,
            period_start,
            period_end,
            validated_data['filters']
        )
        
        return validated_data
    
    @classmethod
    def _validate_report_type(cls, report_type: Optional[str]) -> str:
        """Validate report type"""
        if not report_type:
            raise ValidationError("Report type is required")
        
        report_type = report_type.lower().strip()
        
        if report_type not in cls.VALID_REPORT_TYPES:
            raise ValidationError(
                f"Invalid report type '{report_type}'. "
                f"Valid types: {', '.join(cls.VALID_REPORT_TYPES)}"
            )
        
        return report_type
    
    @classmethod
    def _validate_date_range(cls, start_date: Optional[str], 
                           end_date: Optional[str]) -> Tuple[date, date]:
        """
        Validate date range for report
        
        Args:
            start_date: Start date string (YYYY-MM-DD)
            end_date: End date string (YYYY-MM-DD)
            
        Returns:
            Tuple of (start_date, end_date) as date objects
            
        Raises:
            InvalidReportPeriodError: If dates are invalid
        """
        if not start_date or not end_date:
            raise InvalidReportPeriodError("Both start_date and end_date are required")
        
        # Parse dates
        try:
            start = datetime.strptime(start_date, '%Y-%m-%d').date()
            end = datetime.strptime(end_date, '%Y-%m-%d').date()
        except ValueError as e:
            raise InvalidReportPeriodError(
                f"Invalid date format. Use YYYY-MM-DD. Error: {str(e)}"
            )
        
        # Validate date logic
        if start > end:
            raise InvalidReportPeriodError("Start date must be before or equal to end date")
        
        # Check future dates
        today = timezone.now().date()
        if end > today:
            raise InvalidReportPeriodError("End date cannot be in the future")
        
        # Check date range limits
        days_diff = (end - start).days
        if days_diff > cls.MAX_REPORT_PERIOD_DAYS:
            raise InvalidReportPeriodError(
                f"Report period cannot exceed {cls.MAX_REPORT_PERIOD_DAYS} days"
            )
        
        if days_diff < cls.MIN_REPORT_PERIOD_DAYS - 1:
            raise InvalidReportPeriodError(
                f"Report period must be at least {cls.MIN_REPORT_PERIOD_DAYS} day(s)"
            )
        
        return start, end
    
    @classmethod
    def _validate_file_format(cls, file_format: Optional[str]) -> str:
        """Validate file format"""
        if not file_format:
            return 'pdf'  # Default
        
        file_format = file_format.lower().strip()
        
        if file_format not in cls.VALID_FILE_FORMATS:
            raise ValidationError(
                f"Invalid file format '{file_format}'. "
                f"Valid formats: {', '.join(cls.VALID_FILE_FORMATS)}"
            )
        
        return file_format
    
    @classmethod
    def _validate_string_field(cls, value: Optional[str], field_name: str,
                              max_length: int, required: bool = True,
                              default: str = '') -> str:
        """
        Validate and sanitize string field
        
        Args:
            value: Field value
            field_name: Name of field for error messages
            max_length: Maximum allowed length
            required: Whether field is required
            default: Default value if not required
            
        Returns:
            Sanitized string
        """
        if not value:
            if required:
                raise ValidationError(f"{field_name} is required")
            return default
        
        # Sanitize string
        value = str(value).strip()
        
        # Remove potentially dangerous characters
        value = re.sub(r'[<>\"\'&]', '', value)
        
        # Check length
        if len(value) > max_length:
            raise ValidationError(
                f"{field_name} exceeds maximum length of {max_length} characters"
            )
        
        return value
    
    @classmethod
    def _validate_filters(cls, filters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate report filters
        
        Args:
            filters: Filter dictionary
            
        Returns:
            Validated filters
        """
        validated_filters = {}
        
        # Validate category IDs
        if 'category_ids' in filters:
            category_ids = filters['category_ids']
            if not isinstance(category_ids, list):
                raise ValidationError("category_ids must be a list")
            
            if len(category_ids) > cls.MAX_CATEGORIES:
                raise ValidationError(
                    f"Cannot filter by more than {cls.MAX_CATEGORIES} categories"
                )
            
            # Validate each ID is an integer
            validated_ids = []
            for cat_id in category_ids:
                try:
                    validated_ids.append(int(cat_id))
                except (ValueError, TypeError):
                    raise ValidationError(f"Invalid category ID: {cat_id}")
            
            validated_filters['category_ids'] = validated_ids
        
        # Validate account IDs
        if 'account_ids' in filters:
            account_ids = filters['account_ids']
            if not isinstance(account_ids, list):
                raise ValidationError("account_ids must be a list")
            
            if len(account_ids) > cls.MAX_ACCOUNTS:
                raise ValidationError(
                    f"Cannot filter by more than {cls.MAX_ACCOUNTS} accounts"
                )
            
            # Validate each ID is an integer
            validated_ids = []
            for acc_id in account_ids:
                try:
                    validated_ids.append(int(acc_id))
                except (ValueError, TypeError):
                    raise ValidationError(f"Invalid account ID: {acc_id}")
            
            validated_filters['account_ids'] = validated_ids
        
        # Validate transaction type
        if 'transaction_type' in filters:
            trans_type = filters['transaction_type']
            valid_types = ['credit', 'debit', 'all']
            
            if trans_type not in valid_types:
                raise ValidationError(
                    f"Invalid transaction type. Valid types: {', '.join(valid_types)}"
                )
            
            validated_filters['transaction_type'] = trans_type
        
        # Validate amount range
        if 'min_amount' in filters or 'max_amount' in filters:
            min_amount = filters.get('min_amount')
            max_amount = filters.get('max_amount')
            
            if min_amount is not None:
                try:
                    min_amount = Decimal(str(min_amount))
                    if min_amount < 0:
                        raise ValidationError("min_amount cannot be negative")
                    validated_filters['min_amount'] = float(min_amount)
                except (ValueError, TypeError):
                    raise ValidationError("Invalid min_amount")
            
            if max_amount is not None:
                try:
                    max_amount = Decimal(str(max_amount))
                    if max_amount < 0:
                        raise ValidationError("max_amount cannot be negative")
                    validated_filters['max_amount'] = float(max_amount)
                except (ValueError, TypeError):
                    raise ValidationError("Invalid max_amount")
            
            if min_amount and max_amount and min_amount > max_amount:
                raise ValidationError("min_amount cannot be greater than max_amount")
        
        return validated_filters
    
    @classmethod
    def _validate_parameters(cls, parameters: Dict[str, Any], 
                           report_type: str) -> Dict[str, Any]:
        """
        Validate report-specific parameters
        
        Args:
            parameters: Parameters dictionary
            report_type: Type of report
            
        Returns:
            Validated parameters
        """
        validated_params = {}
        
        # Report-type specific validation
        if report_type == 'cash_flow':
            # Validate grouping
            grouping = parameters.get('grouping', 'daily')
            valid_groupings = ['daily', 'weekly', 'monthly']
            
            if grouping not in valid_groupings:
                raise ValidationError(
                    f"Invalid grouping. Valid options: {', '.join(valid_groupings)}"
                )
            
            validated_params['grouping'] = grouping
        
        elif report_type == 'category_analysis':
            # Validate sort order
            sort_by = parameters.get('sort_by', 'amount')
            valid_sorts = ['amount', 'count', 'name']
            
            if sort_by not in valid_sorts:
                raise ValidationError(
                    f"Invalid sort_by. Valid options: {', '.join(valid_sorts)}"
                )
            
            validated_params['sort_by'] = sort_by
            
            # Validate limit
            limit = parameters.get('limit')
            if limit is not None:
                try:
                    limit = int(limit)
                    if limit < 1 or limit > 100:
                        raise ValidationError("limit must be between 1 and 100")
                    validated_params['limit'] = limit
                except (ValueError, TypeError):
                    raise ValidationError("Invalid limit value")
        
        # Include charts parameter
        include_charts = parameters.get('include_charts', True)
        validated_params['include_charts'] = bool(include_charts)
        
        # Include summary parameter
        include_summary = parameters.get('include_summary', True)
        validated_params['include_summary'] = bool(include_summary)
        
        return validated_params
    
    @classmethod
    def _validate_data_sufficiency(cls, company: Any, start_date: date,
                                 end_date: date, filters: Dict[str, Any]) -> None:
        """
        Validate that sufficient data exists for report generation
        
        Args:
            company: Company instance
            start_date: Report start date
            end_date: Report end date
            filters: Applied filters
            
        Raises:
            ReportDataInsufficientError: If insufficient data
        """
        from apps.banking.models import Transaction, BankAccount
        
        # Check if company has any accounts
        account_count = BankAccount.objects.filter(
            company=company,
            is_active=True
        ).count()
        
        if account_count == 0:
            raise ReportDataInsufficientError(
                "No active bank accounts found. Please connect a bank account first."
            )
        
        # Build transaction query
        transaction_query = Transaction.objects.filter(
            bank_account__company=company,
            transaction_date__gte=start_date,
            transaction_date__lte=end_date
        )
        
        # Apply filters
        if filters.get('account_ids'):
            transaction_query = transaction_query.filter(
                bank_account_id__in=filters['account_ids']
            )
        
        if filters.get('category_ids'):
            transaction_query = transaction_query.filter(
                category_id__in=filters['category_ids']
            )
        
        # Check transaction count
        transaction_count = transaction_query.count()
        
        if transaction_count == 0:
            raise ReportDataInsufficientError(
                "No transactions found for the selected period and filters. "
                "Please adjust your date range or filters."
            )
        
        # Check minimum data requirements by report type
        # This could be expanded based on specific report requirements
        
    @classmethod
    def validate_template_data(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate report template data
        
        Args:
            data: Template data
            
        Returns:
            Validated template data
        """
        validated_data = {}
        
        # Validate name
        validated_data['name'] = cls._validate_string_field(
            data.get('name'),
            'name',
            max_length=100,
            required=True
        )
        
        # Validate description
        validated_data['description'] = cls._validate_string_field(
            data.get('description'),
            'description',
            max_length=500,
            required=False,
            default=''
        )
        
        # Validate report type
        validated_data['report_type'] = cls._validate_report_type(
            data.get('report_type')
        )
        
        # Validate template config
        template_config = data.get('template_config', {})
        if not isinstance(template_config, dict):
            raise ValidationError("template_config must be a dictionary")
        
        validated_data['template_config'] = template_config
        
        # Validate default parameters
        default_params = data.get('default_parameters', {})
        if not isinstance(default_params, dict):
            raise ValidationError("default_parameters must be a dictionary")
        
        validated_data['default_parameters'] = cls._validate_parameters(
            default_params,
            validated_data['report_type']
        )
        
        # Validate default filters
        default_filters = data.get('default_filters', {})
        if not isinstance(default_filters, dict):
            raise ValidationError("default_filters must be a dictionary")
        
        validated_data['default_filters'] = cls._validate_filters(default_filters)
        
        # Validate boolean fields
        validated_data['is_active'] = bool(data.get('is_active', True))
        validated_data['is_public'] = bool(data.get('is_public', False))
        
        return validated_data