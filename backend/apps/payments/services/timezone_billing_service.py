"""
Timezone-aware billing service for accurate billing cycles
Handles timezone conversions and billing period calculations
"""
import pytz
from datetime import datetime, timedelta, date
from typing import Optional, Dict, Any, Tuple
from django.utils import timezone
from django.conf import settings
from decimal import Decimal
from core.logging_utils import get_secure_logger

logger = get_secure_logger(__name__)


class TimezoneBillingService:
    """Service for handling timezone-aware billing operations"""
    
    # Brazilian timezones
    BRAZIL_TIMEZONES = {
        'SP': 'America/Sao_Paulo',  # São Paulo, Rio de Janeiro, Minas Gerais, etc.
        'AC': 'America/Rio_Branco',  # Acre
        'AM': 'America/Manaus',      # Amazonas, Roraima, Rondônia, Mato Grosso
        'CE': 'America/Fortaleza',   # Ceará, Bahia, etc.
        'DF': 'America/Sao_Paulo',   # Distrito Federal
        'default': 'America/Sao_Paulo'  # Default to São Paulo timezone
    }
    
    def __init__(self):
        self.utc = pytz.UTC
        self.default_timezone = pytz.timezone(self.BRAZIL_TIMEZONES['default'])
    
    def get_company_timezone(self, company: 'Company') -> pytz.BaseTzInfo:
        """
        Get the appropriate timezone for a company based on their location
        
        Args:
            company: Company instance
            
        Returns:
            pytz timezone object
        """
        try:
            # Try to get timezone from company's state
            state = getattr(company, 'address_state', '').upper()
            
            if state in self.BRAZIL_TIMEZONES:
                tz_name = self.BRAZIL_TIMEZONES[state]
            else:
                tz_name = self.BRAZIL_TIMEZONES['default']
            
            return pytz.timezone(tz_name)
            
        except Exception as e:
            logger.warning(f"Error determining timezone for company {company.id}: {e}")
            return self.default_timezone
    
    def convert_utc_to_company_time(self, utc_datetime: datetime, company: 'Company') -> datetime:
        """
        Convert UTC datetime to company's local time
        
        Args:
            utc_datetime: UTC datetime
            company: Company instance
            
        Returns:
            Localized datetime in company's timezone
        """
        if not utc_datetime:
            return None
        
        # Ensure datetime is timezone-aware and in UTC
        if timezone.is_naive(utc_datetime):
            utc_datetime = self.utc.localize(utc_datetime)
        elif utc_datetime.tzinfo != self.utc:
            utc_datetime = utc_datetime.astimezone(self.utc)
        
        company_tz = self.get_company_timezone(company)
        return utc_datetime.astimezone(company_tz)
    
    def convert_company_time_to_utc(self, local_datetime: datetime, company: 'Company') -> datetime:
        """
        Convert company's local time to UTC
        
        Args:
            local_datetime: Local datetime
            company: Company instance
            
        Returns:
            UTC datetime
        """
        if not local_datetime:
            return None
        
        company_tz = self.get_company_timezone(company)
        
        # Localize if naive
        if timezone.is_naive(local_datetime):
            local_datetime = company_tz.localize(local_datetime)
        
        return local_datetime.astimezone(self.utc)
    
    def get_billing_cycle_dates(self, 
                               company: 'Company',
                               billing_period: str = 'monthly',
                               start_date: Optional[datetime] = None) -> Dict[str, datetime]:
        """
        Calculate billing cycle dates in company's timezone
        
        Args:
            company: Company instance
            billing_period: 'monthly' or 'yearly'
            start_date: Optional start date (defaults to now)
            
        Returns:
            Dictionary with period_start, period_end, next_billing_date
        """
        try:
            company_tz = self.get_company_timezone(company)
            
            # Use provided start date or current time in company's timezone
            if start_date:
                if timezone.is_naive(start_date):
                    period_start = company_tz.localize(start_date)
                else:
                    period_start = start_date.astimezone(company_tz)
            else:
                period_start = timezone.now().astimezone(company_tz)
            
            # Normalize to start of day in company timezone
            period_start = period_start.replace(hour=0, minute=0, second=0, microsecond=0)
            
            # Calculate period end based on billing period
            if billing_period == 'yearly':
                # Add one year
                try:
                    period_end = period_start.replace(year=period_start.year + 1)
                except ValueError:
                    # Handle leap year edge case (Feb 29)
                    period_end = period_start.replace(year=period_start.year + 1, day=28)
            else:  # monthly
                # Add one month
                if period_start.month == 12:
                    next_year = period_start.year + 1
                    next_month = 1
                else:
                    next_year = period_start.year
                    next_month = period_start.month + 1
                
                try:
                    period_end = period_start.replace(year=next_year, month=next_month)
                except ValueError:
                    # Handle month-end edge cases (e.g., Jan 31 -> Feb 28)
                    if next_month == 2:
                        # February - use last day of February
                        import calendar
                        last_day = calendar.monthrange(next_year, next_month)[1]
                        period_end = period_start.replace(year=next_year, month=next_month, day=last_day)
                    else:
                        # Use last day of the month
                        import calendar
                        last_day = calendar.monthrange(next_year, next_month)[1]
                        period_end = period_start.replace(year=next_year, month=next_month, day=min(period_start.day, last_day))
            
            # Set period_end to end of day (23:59:59)
            period_end = period_end.replace(hour=23, minute=59, second=59, microsecond=999999)
            
            # Next billing date is the period_end + 1 second
            next_billing_date = period_end + timedelta(seconds=1)
            next_billing_date = next_billing_date.replace(hour=0, minute=0, second=0, microsecond=0)
            
            # Convert back to UTC for database storage
            result = {
                'period_start': period_start.astimezone(self.utc),
                'period_end': period_end.astimezone(self.utc),
                'next_billing_date': next_billing_date.astimezone(self.utc),
                'company_timezone': str(company_tz),
                'local_period_start': period_start,
                'local_period_end': period_end
            }
            
            logger.info("Calculated billing cycle dates", extra={
                'company_id': company.id,
                'billing_period': billing_period,
                'timezone': str(company_tz),
                'period_start': result['period_start'].isoformat(),
                'period_end': result['period_end'].isoformat()
            })
            
            return result
            
        except Exception as e:
            logger.error(f"Error calculating billing cycle dates for company {company.id}: {e}")
            raise
    
    def is_in_current_billing_period(self, 
                                   company: 'Company',
                                   check_datetime: datetime,
                                   period_start: datetime,
                                   period_end: datetime) -> bool:
        """
        Check if a datetime falls within the current billing period
        
        Args:
            company: Company instance
            check_datetime: Datetime to check
            period_start: Billing period start
            period_end: Billing period end
            
        Returns:
            bool: True if within billing period
        """
        try:
            # Convert all datetimes to company timezone for comparison
            company_tz = self.get_company_timezone(company)
            
            # Normalize check_datetime
            if timezone.is_naive(check_datetime):
                check_datetime = self.utc.localize(check_datetime)
            local_check = check_datetime.astimezone(company_tz)
            
            # Normalize period dates
            if timezone.is_naive(period_start):
                period_start = self.utc.localize(period_start)
            local_start = period_start.astimezone(company_tz)
            
            if timezone.is_naive(period_end):
                period_end = self.utc.localize(period_end)
            local_end = period_end.astimezone(company_tz)
            
            return local_start <= local_check <= local_end
            
        except Exception as e:
            logger.error(f"Error checking billing period for company {company.id}: {e}")
            return False
    
    def get_usage_reset_time(self, company: 'Company') -> datetime:
        """
        Get the next usage reset time in UTC
        
        Args:
            company: Company instance
            
        Returns:
            UTC datetime for next usage reset
        """
        try:
            company_tz = self.get_company_timezone(company)
            
            # Get current time in company timezone
            now_local = timezone.now().astimezone(company_tz)
            
            # Calculate next month's first day at midnight in company timezone
            if now_local.month == 12:
                next_reset = now_local.replace(
                    year=now_local.year + 1,
                    month=1,
                    day=1,
                    hour=0,
                    minute=0,
                    second=0,
                    microsecond=0
                )
            else:
                next_reset = now_local.replace(
                    month=now_local.month + 1,
                    day=1,
                    hour=0,
                    minute=0,
                    second=0,
                    microsecond=0
                )
            
            # Convert to UTC
            return next_reset.astimezone(self.utc)
            
        except Exception as e:
            logger.error(f"Error calculating usage reset time for company {company.id}: {e}")
            # Fallback to UTC calculation
            now_utc = timezone.now()
            if now_utc.month == 12:
                return now_utc.replace(
                    year=now_utc.year + 1,
                    month=1,
                    day=1,
                    hour=0,
                    minute=0,
                    second=0,
                    microsecond=0
                )
            else:
                return now_utc.replace(
                    month=now_utc.month + 1,
                    day=1,
                    hour=0,
                    minute=0,
                    second=0,
                    microsecond=0
                )
    
    def format_billing_date_for_company(self, 
                                      utc_datetime: datetime, 
                                      company: 'Company',
                                      format_str: str = '%d/%m/%Y %H:%M') -> str:
        """
        Format a UTC datetime for display to company in their local timezone
        
        Args:
            utc_datetime: UTC datetime
            company: Company instance
            format_str: Format string for datetime
            
        Returns:
            Formatted datetime string in company's timezone
        """
        try:
            local_datetime = self.convert_utc_to_company_time(utc_datetime, company)
            if local_datetime:
                return local_datetime.strftime(format_str)
            return "N/A"
            
        except Exception as e:
            logger.error(f"Error formatting billing date for company {company.id}: {e}")
            return utc_datetime.strftime(format_str) if utc_datetime else "N/A"
    
    def calculate_proration_amount(self,
                                 company: 'Company',
                                 old_amount: Decimal,
                                 new_amount: Decimal,
                                 change_date: datetime,
                                 period_start: datetime,
                                 period_end: datetime) -> Dict[str, Any]:
        """
        Calculate prorated amount for plan changes with timezone awareness
        
        Args:
            company: Company instance
            old_amount: Previous plan amount
            new_amount: New plan amount
            change_date: When the change occurred
            period_start: Billing period start
            period_end: Billing period end
            
        Returns:
            Dictionary with proration details
        """
        try:
            company_tz = self.get_company_timezone(company)
            
            # Convert all dates to company timezone for accurate calculation
            local_change = self.convert_utc_to_company_time(change_date, company)
            local_start = self.convert_utc_to_company_time(period_start, company)
            local_end = self.convert_utc_to_company_time(period_end, company)
            
            # Calculate total period duration in seconds
            total_period = (local_end - local_start).total_seconds()
            
            # Calculate remaining period from change date
            remaining_period = (local_end - local_change).total_seconds()
            
            # Calculate proration percentage
            proration_percentage = remaining_period / total_period if total_period > 0 else 0
            
            # Calculate amounts
            old_prorated = old_amount * Decimal(str(proration_percentage))
            new_prorated = new_amount * Decimal(str(proration_percentage))
            proration_amount = new_prorated - old_prorated
            
            result = {
                'proration_amount': proration_amount,
                'old_prorated_amount': old_prorated,
                'new_prorated_amount': new_prorated,
                'proration_percentage': proration_percentage,
                'remaining_days': remaining_period / (24 * 3600),  # Convert to days
                'total_days': total_period / (24 * 3600),
                'change_date_local': local_change,
                'timezone': str(company_tz)
            }
            
            logger.info("Calculated proration amount", extra={
                'company_id': company.id,
                'proration_amount': float(proration_amount),
                'proration_percentage': proration_percentage
            })
            
            return result
            
        except Exception as e:
            logger.error(f"Error calculating proration for company {company.id}: {e}")
            raise


# Global service instance
timezone_billing_service = TimezoneBillingService()


def get_company_billing_dates(company: 'Company', billing_period: str = 'monthly') -> Dict[str, datetime]:
    """
    Convenience function to get billing dates for a company
    
    Returns:
        Dictionary with timezone-aware billing dates
    """
    return timezone_billing_service.get_billing_cycle_dates(company, billing_period)


def format_date_for_company(company: 'Company', utc_datetime: datetime) -> str:
    """
    Convenience function to format dates for company display
    
    Returns:
        Formatted date string in company's timezone
    """
    return timezone_billing_service.format_billing_date_for_company(utc_datetime, company)