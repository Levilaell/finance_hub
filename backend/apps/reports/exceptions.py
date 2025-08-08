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


class ReportNotFoundError(APIException):
    """Raised when report is not found"""
    status_code = status.HTTP_404_NOT_FOUND
    default_detail = 'Report not found.'
    default_code = 'report_not_found'


class ReportPermissionDeniedError(APIException):
    """Raised when user doesn't have permission to access report"""
    status_code = status.HTTP_403_FORBIDDEN
    default_detail = 'You do not have permission to access this report.'
    default_code = 'report_permission_denied'


class ReportQuotaExceededError(APIException):
    """Raised when user exceeds report generation quota"""
    status_code = status.HTTP_429_TOO_MANY_REQUESTS
    default_detail = 'Report generation quota exceeded. Please try again later.'
    default_code = 'report_quota_exceeded'


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


class ReportFileSizeExceededError(APIException):
    """Raised when generated report exceeds size limits"""
    status_code = status.HTTP_413_REQUEST_ENTITY_TOO_LARGE
    default_detail = 'Generated report exceeds maximum file size limit.'
    default_code = 'report_file_size_exceeded'