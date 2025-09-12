"""
Reports app views - Optimized version
Financial reporting and analytics with performance improvements
"""
import logging
from decimal import Decimal
from datetime import datetime, timedelta, date
from typing import Dict, Any, List
import mimetypes
import hashlib

from django.core.files.base import ContentFile
from django.db.models import Count, Q, Sum, Avg, F, Prefetch, Value, CharField
from django.http import HttpResponse, Http404
from django.utils import timezone
from django.core.signing import TimestampSigner, BadSignature
from django.shortcuts import get_object_or_404
from django.db import transaction as db_transaction
from django.views.decorators.cache import cache_page
from django.core.cache import cache
from django.utils.decorators import method_decorator
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.throttling import UserRateThrottle


def parse_date_to_timezone_aware(date_str: str) -> datetime:
    """
    Convert date string to timezone-aware datetime
    This prevents timezone warnings when filtering DateTimeField with date objects
    """
    date_obj = datetime.strptime(date_str, '%Y-%m-%d')
    # Convert to timezone-aware datetime at start of day
    return timezone.make_aware(date_obj.replace(hour=0, minute=0, second=0, microsecond=0))


def parse_end_date_to_timezone_aware(date_str: str) -> datetime:
    """
    Convert end date string to timezone-aware datetime at end of day
    This ensures we capture all transactions for the end date
    """
    date_obj = datetime.strptime(date_str, '%Y-%m-%d')
    # Convert to timezone-aware datetime at end of day
    return timezone.make_aware(date_obj.replace(hour=23, minute=59, second=59, microsecond=999999))

from apps.banking.models import BankAccount, Transaction
from .models import Report, ReportTemplate
from .serializers import ReportSerializer, ReportTemplateSerializer
from .report_generator import ReportGenerator
from .tasks import generate_report_async
from .exceptions import (
    InvalidReportPeriodError,
    ReportGenerationInProgressError,
    ReportPermissionDeniedError
)

logger = logging.getLogger(__name__)


class ReportGenerationThrottle(UserRateThrottle):
    """Rate limiting for report generation"""
    scope = 'report_generation'
    rate = '10/hour'


class ReportViewSet(viewsets.ModelViewSet):
    """
    Report management viewset with optimizations
    """
    serializer_class = ReportSerializer
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [ReportGenerationThrottle]
    
    def get_queryset(self):
        """Optimized queryset with proper select_related and prefetch_related"""
        user = self.request.user
        
        # Handle users without company
        if not hasattr(user, 'company') or user.company is None:
            # Return empty queryset for users without company
            # Reports are always company-specific, unlike templates which can be public
            return Report.objects.none()
        
        return Report.objects.filter(
            company=user.company
        ).select_related(
            'created_by',
            'company',
            'company__subscription'
        ).order_by('-created_at')
    
    def create(self, request, *args, **kwargs):
        """Create report with async generation and validation"""
        logger.info(f"Report creation request from user {request.user.id}")
        
        # Check if user has a company
        if not hasattr(request.user, 'company') or request.user.company is None:
            return Response({
                'error': 'You must have a company associated to create reports'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Extract and validate data
        report_type = request.data.get('report_type')
        period_start = request.data.get('period_start')
        period_end = request.data.get('period_end')
        file_format = request.data.get('file_format', 'pdf')
        
        # Basic validation
        if not all([report_type, period_start, period_end]):
            return Response({
                'error': 'report_type, period_start, and period_end are required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Date validation (handle multiple formats) - FIXED
        try:
            # Standardize to always work with date objects
            if 'T' in period_start:
                start_date = datetime.fromisoformat(period_start.replace('Z', '+00:00')).date()
            else:
                start_date = datetime.strptime(period_start, '%Y-%m-%d').date()
                
            if 'T' in period_end:
                end_date = datetime.fromisoformat(period_end.replace('Z', '+00:00')).date()
            else:
                end_date = datetime.strptime(period_end, '%Y-%m-%d').date()
                
        except (ValueError, TypeError) as e:
            logger.error(f"Date parsing error: {str(e)} - start: {period_start}, end: {period_end}")
            raise InvalidReportPeriodError(f'Invalid date format: {str(e)}')

        # Validation with consistent date objects
        if start_date > end_date:
            raise InvalidReportPeriodError('Start date must be before end date')

        if (end_date - start_date).days > 365:
            raise InvalidReportPeriodError('Report period cannot exceed 365 days')

        if end_date > timezone.now().date():
            raise InvalidReportPeriodError('End date cannot be in the future')
        
        # Check for duplicate in-progress reports
        with db_transaction.atomic():
            existing = Report.objects.select_for_update().filter(
                company=request.user.company,
                report_type=report_type,
                period_start=start_date,
                period_end=end_date,
                is_generated=False,
                error_message=''
            ).exists()
            
            if existing:
                raise ReportGenerationInProgressError()
            
            # Create report
            report = Report.objects.create(
                company=request.user.company,
                report_type=report_type,
                title=request.data.get('title', f'{report_type} Report - {period_start} to {period_end}'),
                description=request.data.get('description', ''),
                period_start=start_date if isinstance(start_date, date) else start_date.date(),
                period_end=end_date if isinstance(end_date, date) else end_date.date(),
                file_format=file_format,
                parameters=request.data.get('parameters', {}),
                filters=request.data.get('filters', {}),
                created_by=request.user
            )
            
            # Try to generate asynchronously first
            try:
                task = generate_report_async.delay(report.id)
                logger.info(f"Report {report.id} created and queued for async generation")
            except Exception as celery_error:
                # Fallback to synchronous generation if Celery is not available
                logger.warning(f"Celery not available, generating report synchronously: {celery_error}")
                
                try:
                    # Import ReportGenerator and generate synchronously
                    from .report_generator import ReportGenerator
                    from django.core.files.base import ContentFile
                    
                    generator = ReportGenerator(report.company)
                    
                    # Generate the report
                    buffer = generator.generate_report(
                        report_type=report.report_type,
                        start_date=report.period_start,
                        end_date=report.period_end,
                        format=report.file_format,
                        filters=report.filters
                    )
                    
                    # Save the generated file
                    filename = f"{report.report_type}_{report.id}_{start_date}_{end_date}.{file_format}"
                    report.file.save(filename, ContentFile(buffer.read()))
                    report.is_generated = True
                    report.save(update_fields=['file', 'is_generated'])
                    
                    logger.info(f"Report {report.id} generated synchronously")
                except Exception as sync_error:
                    logger.error(f"Failed to generate report synchronously: {sync_error}")
                    report.error_message = str(sync_error)
                    report.save(update_fields=['error_message'])
        
        serializer = self.get_serializer(report)
        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED
        )
    
    @action(detail=True, methods=['get'])
    def download(self, request, pk=None):
        """Direct download of report file"""
        report = self.get_object()
        
        if not report.is_generated:
            return Response({
                'error': 'Report is not ready for download'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if not report.file:
            return Response({
                'error': 'Report file not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        try:
            # Direct file download
            file_handle = report.file.open('rb')
            
            # Set correct content type based on file format
            content_type = 'application/pdf' if report.file_format == 'pdf' else 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            
            response = HttpResponse(
                file_handle,
                content_type=content_type
            )
            
            # Set download filename
            filename = f"{report.title}_{report.id}.{report.file_format}".replace(' ', '_')
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            response['Content-Length'] = report.file.size
            
            # Log successful download
            logger.info(f"Direct download initiated for report {report.id} by user {request.user.id}")
            return response
            
        except Exception as e:
            logger.error(f"Download error for report {pk}: {str(e)}", exc_info=True)
            return Response({
                'error': 'Error downloading file'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Get reports summary with caching"""
        # Check if user has a company
        if not hasattr(request.user, 'company') or request.user.company is None:
            return Response({
                'total_reports': 0,
                'reports_generated': 0,
                'pending_reports': 0,
                'failed_reports': 0,
                'recent_reports': []
            })
        
        company = request.user.company
        cache_key = f'report_summary_{company.id}'
        
        # Check cache
        cached_data = cache.get(cache_key)
        if cached_data:
            return Response(cached_data)
        
        reports = self.get_queryset()
        last_30_days = timezone.now() - timedelta(days=30)
        
        summary_data = {
            'total_reports': reports.count(),
            'reports_generated': reports.filter(is_generated=True).count(),
            'reports_pending': reports.filter(is_generated=False, error_message='').count(),
            'reports_failed': reports.filter(is_generated=False).exclude(error_message='').count(),
            'reports_by_type': list(reports.values('report_type').annotate(
                count=Count('id')
            )),
            'recent_reports': ReportSerializer(
                reports.select_related('created_by')[:10], 
                many=True
            ).data,
            'reports_last_30_days': reports.filter(created_at__gte=last_30_days).count(),
        }
        
        # Cache for 5 minutes
        cache.set(cache_key, summary_data, 300)
        
        return Response(summary_data)
    
    @action(detail=True, methods=['post'])
    def regenerate(self, request, pk=None):
        """Regenerate a failed or completed report"""
        report = self.get_object()
        
        # Reset report status
        report.is_generated = False
        report.error_message = ''
        report.save(update_fields=['is_generated', 'error_message'])
        
        # Try to queue for regeneration
        try:
            generate_report_async.delay(report.id, regenerate=True)
            message = 'Report queued for regeneration'
            logger.info(f"Report {report.id} queued for async regeneration")
        except Exception as celery_error:
            # Fallback to synchronous regeneration if Celery is not available
            logger.warning(f"Celery not available, regenerating report synchronously: {celery_error}")
            
            try:
                from .report_generator import ReportGenerator
                from django.core.files.base import ContentFile
                
                generator = ReportGenerator(report.company)
                
                # Generate the report
                buffer = generator.generate_report(
                    report_type=report.report_type,
                    start_date=report.period_start,
                    end_date=report.period_end,
                    format=report.file_format,
                    filters=report.filters
                )
                
                # Save the generated file
                filename = f"{report.report_type}_{report.id}_{report.period_start}_{report.period_end}.{report.file_format}"
                report.file.save(filename, ContentFile(buffer.read()))
                report.is_generated = True
                report.save(update_fields=['file', 'is_generated'])
                
                message = 'Report regenerated successfully'
                logger.info(f"Report {report.id} regenerated synchronously")
            except Exception as sync_error:
                logger.error(f"Failed to regenerate report synchronously: {sync_error}")
                report.error_message = str(sync_error)
                report.save(update_fields=['error_message'])
                message = f'Failed to regenerate report: {sync_error}'
        
        return Response({
            'message': message,
            'report_id': report.id
        })


class SecureReportDownloadView(APIView):
    """Secure download endpoint with signed URLs"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, signed_id):
        """Download report with signature validation"""
        signer = TimestampSigner()
        
        try:
            # Validate signature (1 hour expiry)
            report_id = signer.unsign(signed_id, max_age=3600)
        except BadSignature:
            raise Http404("Invalid or expired download link")
        
        # Get report and verify permissions
        report = get_object_or_404(Report, id=report_id)
        
        if report.company != request.user.company:
            raise ReportPermissionDeniedError()
        
        if not report.file:
            raise Http404("Report file not found")
        
        # Stream file response
        try:
            file_handle = report.file.open('rb')
            response = HttpResponse(
                file_handle,
                content_type=mimetypes.guess_type(report.file.name)[0] or 'application/octet-stream'
            )
            response['Content-Disposition'] = f'attachment; filename="{report.title}_{report.id}.{report.file_format}"'
            response['Content-Length'] = report.file.size
            
            # Log download
            logger.info(f"Report {report.id} downloaded by user {request.user.id}")
            
            return response
        except Exception as e:
            logger.error(f"Error downloading report {report_id}: {str(e)}")
            raise Http404("Error downloading file")


class ReportTemplateViewSet(viewsets.ModelViewSet):
    """Report template management with optimizations"""
    serializer_class = ReportTemplateSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Get templates with proper filtering"""
        user = self.request.user
        
        # Handle users without company
        if not hasattr(user, 'company') or user.company is None:
            # Return only public templates for users without company
            return ReportTemplate.objects.filter(
                is_public=True,
                is_active=True
            ).select_related(
                'company',
                'created_by'
            ).order_by('name')
        
        # Normal filtering for users with company
        return ReportTemplate.objects.filter(
            Q(company=user.company) | Q(is_public=True),
            is_active=True
        ).select_related(
            'company',
            'created_by'
        ).order_by('name')


class AnalyticsView(APIView):
    """Optimized analytics endpoint with caching"""
    permission_classes = [permissions.IsAuthenticated]
    
    @method_decorator(cache_page(60 * 15))  # Cache for 15 minutes
    def get(self, request):
        """Get analytics data with heavy caching"""
        company = request.user.company
        period_days = int(request.query_params.get('days', 30))
        
        # Create cache key from parameters
        cache_key = hashlib.md5(
            f"analytics_{company.id}_{period_days}".encode()
        ).hexdigest()
        
        # Check cache
        cached_data = cache.get(cache_key)
        if cached_data:
            logger.info(f"Analytics cache hit for company {company.id}")
            return Response(cached_data)
        
        # Calculate date range
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=period_days)
        
        # Optimized queries with select_related
        accounts = BankAccount.objects.filter(
            company=company,
            is_active=True
        ).select_related('bank_provider')
        
        transactions = Transaction.active.filter(
            company=company,
            date__range=[start_date, end_date]
        ).select_related(
            'category',
            'account'
        )
        
        # Aggregate data
        total_income = transactions.filter(
            type__in=['CREDIT', 'INCOME']
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
        
        total_expenses = transactions.filter(
            type__in=['DEBIT', 'EXPENSE']
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
        
        # Top income sources
        top_income_sources = transactions.filter(
            type='CREDIT'
        ).values('description').annotate(
            total=Sum('amount'),
            count=Count('id')
        ).order_by('-total')[:10]
        
        # Top expense categories
        top_expense_categories = transactions.filter(
            type='DEBIT'
        ).values(
            'pluggy_category_description'
        ).annotate(
            total=Sum('amount'),
            count=Count('id'),
            avg=Avg('amount')
        ).order_by('-total')[:10]
        
        # Weekly trend with optimized query
        weekly_trend = []
        current_date = start_date
        
        while current_date <= end_date:
            week_end = min(current_date + timedelta(days=6), end_date)
            
            week_data = transactions.filter(
                date__range=[current_date, week_end]
            ).aggregate(
                income=Sum('amount', filter=Q(type='CREDIT')),
                expenses=Sum('amount', filter=Q(type='DEBIT'))
            )
            
            weekly_trend.append({
                'week_start': current_date.isoformat(),
                'week_end': week_end.isoformat(),
                'income': week_data['income'] or Decimal('0'),
                'expenses': abs(week_data['expenses'] or Decimal('0')),
                'net': (week_data['income'] or Decimal('0')) + (week_data['expenses'] or Decimal('0'))
            })
            
            current_date += timedelta(days=7)
        
        # Build response
        response_data = {
            'period': {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'days': period_days
            },
            'summary': {
                'total_income': float(total_income),
                'total_expenses': float(abs(total_expenses)),
                'net_result': float(total_income + total_expenses),
                'transaction_count': transactions.count(),
                'daily_avg_income': float(total_income / period_days),
                'daily_avg_expense': float(abs(total_expenses) / period_days)
            },
            'top_income_sources': list(top_income_sources),
            'top_expense_categories': list(top_expense_categories),
            'weekly_trend': weekly_trend,
            'accounts_count': accounts.count(),
            'active_categories': transactions.values('category').distinct().count()
        }
        
        # Cache for 1 hour
        cache.set(cache_key, response_data, 3600)
        
        logger.info(f"Analytics generated for company {company.id}")
        return Response(response_data)


class CashFlowView(APIView):
    """Optimized cash flow endpoint"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        """Get cash flow data with caching"""
        company = request.user.company
        start_date = request.data.get('start_date')
        end_date = request.data.get('end_date')
        
        if not all([start_date, end_date]):
            return Response({
                'error': 'start_date and end_date are required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Parse dates
        try:
            start_date = parse_date_to_timezone_aware(start_date)
            end_date = parse_end_date_to_timezone_aware(end_date)
        except ValueError:
            return Response({
                'error': 'Invalid date format. Use YYYY-MM-DD'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Create cache key
        cache_key = f"cashflow_{company.id}_{start_date}_{end_date}"
        cached_data = cache.get(cache_key)
        
        if cached_data:
            return Response(cached_data)
        
        # Get transactions with optimized query
        transactions = Transaction.active.filter(
            company=company,
            date__range=[start_date, end_date]
        ).select_related(
            'category',
            'account'
        ).order_by('date')
        
        # Build daily cash flow
        daily_flow = []
        current_date = start_date
        running_balance = Decimal('0')
        
        while current_date <= end_date:
            day_transactions = transactions.filter(date=current_date)
            
            # Use broader filters consistent with CategorySpendingView
            income_filter = (
                Q(type__iexact='CREDIT') | Q(type__iexact='INCOME') |
                Q(type__iexact='TRANSFER_IN') | Q(type__iexact='PIX_IN') | Q(type__iexact='INTEREST')
            )
            expense_filter = (
                Q(type__iexact='DEBIT') | Q(type__iexact='EXPENSE') |
                Q(type__iexact='TRANSFER_OUT') | Q(type__iexact='PIX_OUT') | Q(type__iexact='FEE')
            )
            
            daily_data = day_transactions.aggregate(
                income=Sum('amount', filter=income_filter),
                expenses=Sum('amount', filter=expense_filter)
            )
            
            income = daily_data['income'] or Decimal('0')
            expenses = abs(daily_data['expenses'] or Decimal('0'))
            balance = income - expenses
            running_balance += balance
            
            daily_flow.append({
                'date': current_date.isoformat(),
                'income': float(income),
                'expenses': float(expenses),
                'balance': float(running_balance)
            })
            
            current_date += timedelta(days=1)
        
        # Cache for 30 minutes
        cache.set(cache_key, daily_flow, 1800)
        
        return Response(daily_flow)


class QuickReportsView(APIView):
    """Quick report generation with async processing"""
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [ReportGenerationThrottle]
    
    def get(self, request):
        """Get quick report options"""
        return Response({
            'quick_reports': [
                {
                    'id': 'current_month',
                    'name': 'Resumo do Mês Atual',
                    'description': 'Relatório completo do mês em andamento',
                    'icon': 'calendar'
                },
                {
                    'id': 'last_month',
                    'name': 'Resumo do Mês Anterior',
                    'description': 'Relatório completo do mês passado',
                    'icon': 'calendar-check'
                },
                {
                    'id': 'quarterly',
                    'name': 'Relatório Trimestral',
                    'description': 'Análise dos últimos 3 meses',
                    'icon': 'chart-line'
                },
                {
                    'id': 'year_to_date',
                    'name': 'Acumulado do Ano',
                    'description': 'Resultados desde o início do ano',
                    'icon': 'chart-bar'
                },
                {
                    'id': 'cash_flow_30',
                    'name': 'Fluxo de Caixa 30 dias',
                    'description': 'Projeção de fluxo de caixa para os próximos 30 dias',
                    'icon': 'money-bill-wave'
                }
            ]
        })
    
    def post(self, request):
        """Generate quick report asynchronously"""
        
        report_id = request.data.get('report_id')
        company = request.user.company
        
        # Define date ranges for quick reports
        now = timezone.now()
        today = now.date()
        
        if report_id == 'current_month':
            period_start = today.replace(day=1)
            period_end = today
            report_type = 'monthly_summary'
            title = f'Resumo de {now.strftime("%B %Y")}'
            
        elif report_id == 'last_month':
            last_month = (today.replace(day=1) - timedelta(days=1))
            period_start = last_month.replace(day=1)
            period_end = last_month
            report_type = 'monthly_summary'
            title = f'Resumo de {last_month.strftime("%B %Y")}'
            
        elif report_id == 'quarterly':
            period_end = today
            period_start = today - timedelta(days=90)
            report_type = 'quarterly_report'
            title = f'Relatório Trimestral - {period_start.strftime("%b")} a {period_end.strftime("%b %Y")}'
            
        elif report_id == 'year_to_date':
            period_start = today.replace(month=1, day=1)
            period_end = today
            report_type = 'annual_report'
            title = f'Acumulado {today.year}'
            
        elif report_id == 'cash_flow_30':
            period_start = today
            period_end = today + timedelta(days=30)
            report_type = 'cash_flow'
            title = 'Projeção de Fluxo de Caixa - 30 dias'
            
        else:
            return Response({
                'error': 'Invalid report_id'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Create report
        with db_transaction.atomic():
            report = Report.objects.create(
                company=company,
                report_type=report_type,
                title=title,
                period_start=period_start,
                period_end=period_end,
                created_by=request.user,
                file_format='pdf'
            )
            
            # Generate asynchronously
            try:
                generate_report_async.delay(report.id)
            except Exception as celery_error:
                logger.warning(f"Could not queue quick report generation: {celery_error}")
        
        logger.info(f"Quick report {report_id} queued for user {request.user.id}")
        
        return Response({
            'status': 'processing',
            'report': ReportSerializer(report).data,
            'message': 'Relatório sendo gerado. Você será notificado quando estiver pronto.'
        })


class DashboardStatsView(APIView):
    """Dashboard statistics with caching and optimized queries"""
    permission_classes = [permissions.IsAuthenticated]
    
    @method_decorator(cache_page(60 * 5))  # Cache for 5 minutes
    def get(self, request):
        company = request.user.company
        
        # Create cache key
        cache_key = f"dashboard_stats_{company.id}"
        cached_data = cache.get(cache_key)
        
        if cached_data:
            logger.debug(f"Dashboard stats cache hit for company {company.id}")
            return Response(cached_data)
        
        # Optimized query with select_related
        accounts = BankAccount.objects.filter(
            company=company, 
            is_active=True
        ).select_related('bank_provider')
        
        # Current month stats
        now = timezone.now()
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        # Single query for transactions with optimizations
        transactions = Transaction.active.filter(
            company=company,
            date__gte=month_start
        ).select_related('account', 'category')
        
        # Aggregate in database
        stats = transactions.aggregate(
            income=Sum('amount', filter=Q(type__in=['credit', 'transfer_in', 'pix_in', 'CREDIT', 'INCOME'])),
            expenses=Sum('amount', filter=Q(type__in=['debit', 'transfer_out', 'pix_out', 'DEBIT', 'EXPENSE'])),
            transaction_count=Count('id')
        )
        
        total_balance = accounts.aggregate(total=Sum('balance'))['total'] or Decimal('0')
        income = stats['income'] or Decimal('0')
        expenses = abs(stats['expenses'] or Decimal('0'))
        
        response_data = {
            'total_balance': float(total_balance),
            'income_this_month': float(income),
            'expenses_this_month': float(expenses),
            'net_income': float(income - expenses),
            'transaction_count': stats['transaction_count'],
            'accounts_count': accounts.count(),
        }
        
        # Cache for 5 minutes
        cache.set(cache_key, response_data, 300)
        
        logger.info(f"Dashboard stats generated for company {company.id}")
        return Response(response_data)


class CashFlowDataView(APIView):
    """Cash flow data with query optimizations"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        company = request.user.company
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')
        
        if not start_date or not end_date:
            return Response({'error': 'start_date and end_date are required'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        try:
            start_date = parse_date_to_timezone_aware(start_date)
            end_date = parse_end_date_to_timezone_aware(end_date)
        except ValueError:
            return Response({'error': 'Invalid date format. Use YYYY-MM-DD'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        # Create cache key (safe for memcached)
        from .cache_utils import make_date_cache_key
        cache_key = make_date_cache_key("cashflow_data", company.id, start_date, end_date)
        cached_data = cache.get(cache_key)
        
        if cached_data:
            return Response(cached_data)
        
        # Optimized query - get all transactions at once
        transactions = Transaction.active.filter(
            company=company,
            date__range=[start_date, end_date]
        ).select_related(
            'account',
            'category'
        ).values(
            'date',
            'type',
            'amount'
        ).order_by('date')
        
        # Process in Python for better performance
        daily_data = {}
        current_date = start_date.date() if hasattr(start_date, 'date') else start_date
        end_date_date = end_date.date() if hasattr(end_date, 'date') else end_date
        
        # Initialize all dates
        while current_date <= end_date_date:
            daily_data[current_date] = {'income': Decimal('0'), 'expenses': Decimal('0')}
            current_date += timedelta(days=1)
        
        # Aggregate transactions
        for trans in transactions:
            # Convert datetime to date for matching with daily_data keys
            date_key = trans['date'].date() if hasattr(trans['date'], 'date') else trans['date']
            amount = trans['amount']
            trans_type = trans['type'].upper() if trans['type'] else ''
            
            if date_key in daily_data:
                # Use case-insensitive matching and include all transaction types
                # Income types (consistent with CategorySpendingView)
                if trans_type in ['CREDIT', 'INCOME', 'TRANSFER_IN', 'PIX_IN', 'INTEREST']:
                    daily_data[date_key]['income'] += amount
                # Expense types (consistent with CategorySpendingView)
                elif trans_type in ['DEBIT', 'EXPENSE', 'TRANSFER_OUT', 'PIX_OUT', 'FEE']:
                    daily_data[date_key]['expenses'] += abs(amount)
        
        # Build response with running balance
        cash_flow_data = []
        running_balance = Decimal('0')
        
        for date in sorted(daily_data.keys()):
            data = daily_data[date]
            running_balance += data['income'] - data['expenses']
            
            cash_flow_data.append({
                'date': date.strftime('%Y-%m-%d'),
                'income': float(data['income']),
                'expenses': float(data['expenses']),
                'balance': float(running_balance)
            })
        
        # Cache for 30 minutes
        cache.set(cache_key, cash_flow_data, 1800)
        
        return Response(cash_flow_data)


class CategorySpendingView(APIView):
    """Category spending with optimized aggregation"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        company = request.user.company
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')
        category_type = request.GET.get('type', 'expense')
        
        if not start_date or not end_date:
            return Response({'error': 'start_date and end_date are required'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        try:
            start_date = parse_date_to_timezone_aware(start_date)
            end_date = parse_end_date_to_timezone_aware(end_date)
        except ValueError:
            return Response({'error': 'Invalid date format. Use YYYY-MM-DD'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        # Cache key (safe for memcached)
        from .cache_utils import make_date_cache_key
        cache_key = make_date_cache_key("category_spending", company.id, start_date, end_date, category_type)
        cached_data = cache.get(cache_key)
        
        if cached_data:
            return Response(cached_data)
        
        # Build query filter based on type (case-insensitive)
        from django.db.models import Q
        
        if category_type == 'expense':
            # Include all expense-related transaction types (case-insensitive)
            type_filter = (
                Q(type__iexact='DEBIT') | 
                Q(type__iexact='EXPENSE') | 
                Q(type__iexact='debit') | 
                Q(type__iexact='expense') |
                Q(type__iexact='transfer_out') | 
                Q(type__iexact='pix_out') | 
                Q(type__iexact='fee')
            )
        else:
            # Include all income-related transaction types (case-insensitive)
            type_filter = (
                Q(type__iexact='CREDIT') | 
                Q(type__iexact='INCOME') | 
                Q(type__iexact='credit') | 
                Q(type__iexact='income') |
                Q(type__iexact='transfer_in') | 
                Q(type__iexact='pix_in') | 
                Q(type__iexact='interest')
            )
        
        # Optimized query with proper joins and case-insensitive filtering
        category_data = Transaction.active.filter(
            company=company,
            date__range=[start_date, end_date]
        ).filter(
            type_filter
        ).values(
            'pluggy_category_description', 'category__name'
        ).exclude(
            pluggy_category_description__isnull=True,
            pluggy_category_description__exact=''
        ).annotate(
            total_amount=Sum('amount'),
            transaction_count=Count('id')
        ).order_by(
            '-total_amount' if category_type == 'income' else 'total_amount'
        )
        
        # If no categorized data, try to get aggregated data without category filter
        if not category_data:
            logger.info(f"No categorized transactions found, trying aggregated view for company {company.id}")
            category_data = Transaction.active.filter(
                company=company,
                date__range=[start_date, end_date]
            ).filter(
                type_filter
            ).values(
                'pluggy_category_description'
            ).annotate(
                total_amount=Sum('amount'),
                transaction_count=Count('id'),
                category__name=Value('Sem categoria', output_field=CharField())
            ).order_by(
                '-total_amount' if category_type == 'income' else 'total_amount'
            )
        
        # Calculate percentages
        total_amount = sum(abs(item['total_amount']) for item in category_data if item['total_amount'])
        
        result = []
        for item in category_data:
            amount = abs(item['total_amount'])
            percentage = (amount / total_amount * 100) if total_amount else 0
            
            # Use internal category name if available, otherwise use Pluggy description
            category_name = (
                item.get('category__name') or 
                item.get('pluggy_category_description') or 
                'Outros'
            )
            
            result.append({
                'category': {
                    'name': category_name,
                    'icon': 'folder'
                },
                'amount': float(amount),
                'percentage': round(percentage, 1),
                'transaction_count': item['transaction_count']
            })
        
        # Cache for 1 hour
        cache.set(cache_key, result, 3600)
        
        return Response(result)


class IncomeVsExpensesView(APIView):
    """Income vs expenses with optimized monthly aggregation"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        company = request.user.company
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')
        
        if not start_date or not end_date:
            return Response({'error': 'start_date and end_date are required'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        try:
            start_date = parse_date_to_timezone_aware(start_date)
            end_date = parse_end_date_to_timezone_aware(end_date)
        except ValueError:
            return Response({'error': 'Invalid date format. Use YYYY-MM-DD'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        # Cache key
        cache_key = f"income_vs_expenses_{company.id}_{start_date}_{end_date}"
        cached_data = cache.get(cache_key)
        
        if cached_data:
            return Response(cached_data)
        
        # Get all transactions in date range with optimized query
        transactions = Transaction.active.filter(
            company=company,
            date__range=[start_date, end_date]
        ).select_related(
            'account'
        ).values(
            'date__year',
            'date__month',
            'type',
            'amount'
        )
        
        # Aggregate by month
        monthly_data = {}
        
        for trans in transactions:
            year = trans['date__year']
            month = trans['date__month']
            month_key = f"{year}-{month:02d}"
            
            if month_key not in monthly_data:
                monthly_data[month_key] = {'income': Decimal('0'), 'expenses': Decimal('0')}
            
            amount = trans['amount']
            trans_type = trans['type']
            
            if trans_type in ['CREDIT', 'INCOME']:
                monthly_data[month_key]['income'] += amount
            elif trans_type in ['DEBIT', 'EXPENSE']:
                monthly_data[month_key]['expenses'] += abs(amount)
        
        # Build response
        result = []
        for month_key in sorted(monthly_data.keys()):
            data = monthly_data[month_key]
            
            result.append({
                'month': month_key,
                'income': float(data['income']),
                'expenses': float(data['expenses']),
                'net': float(data['income'] - data['expenses'])
            })
        
        # Cache for 1 hour
        cache.set(cache_key, result, 3600)
        
        return Response(result)