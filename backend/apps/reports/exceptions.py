"""
Custom exceptions for reports app
"""
from rest_framework.exceptions import APIException
from rest_framework import status


class ReportGenerationError(APIException):
    """Raised when report generation fails"""
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    default_detail = 'Failed to generate report.'
    default_code = 'report_generation_error'


class InvalidReportPeriodError(APIException):
    """Raised when report period is invalid"""
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = 'Invalid report period specified.'
    default_code = 'invalid_report_period'


class ReportPermissionDeniedError(APIException):
    """Raised when user doesn't have permission to access report"""
    status_code = status.HTTP_403_FORBIDDEN
    default_detail = 'You do not have permission to access this report.'
    default_code = 'report_permission_denied'


class ReportGenerationInProgressError(APIException):
    """Raised when report generation is already in progress"""
    status_code = status.HTTP_409_CONFLICT
    default_detail = 'Report generation already in progress for this period.'
    default_code = 'report_generation_in_progress'


class ReportDataInsufficientError(APIException):
    """Raised when there's insufficient data for report generation"""
    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    default_detail = 'Insufficient data for report generation.'
    default_code = 'report_data_insufficient'