"""
Reports ViewSet for financial reports API.
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.http import HttpResponse
from datetime import datetime, timedelta
from django.utils import timezone

from .services import ReportsService


class ReportsViewSet(viewsets.ViewSet):
    """ViewSet for financial reports."""

    permission_classes = [IsAuthenticated]

    def _parse_date(self, date_str: str) -> datetime:
        """Parse date string to datetime."""
        return datetime.strptime(date_str, '%Y-%m-%d').replace(tzinfo=timezone.utc)

    @action(detail=False, methods=['get'])
    def dre(self, request):
        """
        Get DRE (Demonstrativo de Resultado do Exercício) report.

        Query params:
            - start_date: Start date (YYYY-MM-DD) - required
            - end_date: End date (YYYY-MM-DD) - required
            - compare_with_previous: Compare with previous period (true/false)
        """
        start_date_str = request.query_params.get('start_date')
        end_date_str = request.query_params.get('end_date')
        compare_with_previous = request.query_params.get('compare_with_previous', 'false').lower() == 'true'

        # Validate required params
        if not start_date_str or not end_date_str:
            return Response(
                {'error': 'start_date and end_date are required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            start_date = self._parse_date(start_date_str)
            end_date = self._parse_date(end_date_str)
        except ValueError:
            return Response(
                {'error': 'Invalid date format. Use YYYY-MM-DD'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if start_date > end_date:
            return Response(
                {'error': 'start_date must be before end_date'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Limit period to 1 year for performance
        if (end_date - start_date).days > 366:
            return Response(
                {'error': 'Period cannot exceed 1 year'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Calculate comparison period if requested
        compare_start = None
        compare_end = None
        if compare_with_previous:
            period_days = (end_date - start_date).days
            compare_end = start_date - timedelta(days=1)
            compare_start = compare_end - timedelta(days=period_days)

        try:
            report = ReportsService.get_dre_report(
                user=request.user,
                start_date=start_date,
                end_date=end_date,
                compare_start=compare_start,
                compare_end=compare_end
            )
            return Response(report)
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'])
    def dre_export_pdf(self, request):
        """
        Export DRE report as PDF.

        Query params:
            - start_date: Start date (YYYY-MM-DD) - required
            - end_date: End date (YYYY-MM-DD) - required
            - compare_with_previous: Compare with previous period (true/false)
        """
        start_date_str = request.query_params.get('start_date')
        end_date_str = request.query_params.get('end_date')
        compare_with_previous = request.query_params.get('compare_with_previous', 'false').lower() == 'true'

        if not start_date_str or not end_date_str:
            return Response(
                {'error': 'start_date and end_date are required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            start_date = self._parse_date(start_date_str)
            end_date = self._parse_date(end_date_str)
        except ValueError:
            return Response(
                {'error': 'Invalid date format. Use YYYY-MM-DD'},
                status=status.HTTP_400_BAD_REQUEST
            )

        compare_start = None
        compare_end = None
        if compare_with_previous:
            period_days = (end_date - start_date).days
            compare_end = start_date - timedelta(days=1)
            compare_start = compare_end - timedelta(days=period_days)

        try:
            pdf_content = ReportsService.export_dre_pdf(
                user=request.user,
                start_date=start_date,
                end_date=end_date,
                compare_start=compare_start,
                compare_end=compare_end
            )

            response = HttpResponse(pdf_content, content_type='application/pdf')
            filename = f"DRE_{start_date_str}_{end_date_str}.pdf"
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            return response
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'])
    def dre_export_excel(self, request):
        """
        Export DRE report as Excel.

        Query params:
            - start_date: Start date (YYYY-MM-DD) - required
            - end_date: End date (YYYY-MM-DD) - required
            - compare_with_previous: Compare with previous period (true/false)
        """
        start_date_str = request.query_params.get('start_date')
        end_date_str = request.query_params.get('end_date')
        compare_with_previous = request.query_params.get('compare_with_previous', 'false').lower() == 'true'

        if not start_date_str or not end_date_str:
            return Response(
                {'error': 'start_date and end_date are required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            start_date = self._parse_date(start_date_str)
            end_date = self._parse_date(end_date_str)
        except ValueError:
            return Response(
                {'error': 'Invalid date format. Use YYYY-MM-DD'},
                status=status.HTTP_400_BAD_REQUEST
            )

        compare_start = None
        compare_end = None
        if compare_with_previous:
            period_days = (end_date - start_date).days
            compare_end = start_date - timedelta(days=1)
            compare_start = compare_end - timedelta(days=period_days)

        try:
            excel_content = ReportsService.export_dre_excel(
                user=request.user,
                start_date=start_date,
                end_date=end_date,
                compare_start=compare_start,
                compare_end=compare_end
            )

            response = HttpResponse(
                excel_content,
                content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
            filename = f"DRE_{start_date_str}_{end_date_str}.xlsx"
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            return response
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'])
    def cash_flow(self, request):
        """Get cash flow report."""
        start_date_str = request.query_params.get('start_date')
        end_date_str = request.query_params.get('end_date')
        granularity = request.query_params.get('granularity', 'daily')

        start_date = self._parse_date(start_date_str) if start_date_str else None
        end_date = self._parse_date(end_date_str) if end_date_str else None

        report = ReportsService.get_cash_flow_report(
            user=request.user,
            start_date=start_date,
            end_date=end_date,
            granularity=granularity
        )
        return Response(report)

    @action(detail=False, methods=['get'])
    def category_breakdown(self, request):
        """Get category breakdown report."""
        start_date_str = request.query_params.get('start_date')
        end_date_str = request.query_params.get('end_date')
        transaction_type = request.query_params.get('transaction_type', 'DEBIT')

        start_date = self._parse_date(start_date_str) if start_date_str else None
        end_date = self._parse_date(end_date_str) if end_date_str else None

        report = ReportsService.get_category_breakdown(
            user=request.user,
            start_date=start_date,
            end_date=end_date,
            transaction_type=transaction_type
        )
        return Response(report)

    @action(detail=False, methods=['get'])
    def monthly_summary(self, request):
        """Get monthly summary report."""
        month = request.query_params.get('month')
        year = request.query_params.get('year')

        if not month or not year:
            now = timezone.now()
            month = now.month
            year = now.year
        else:
            month = int(month)
            year = int(year)

        report = ReportsService.get_monthly_summary(
            user=request.user,
            month=month,
            year=year
        )
        return Response(report)

    @action(detail=False, methods=['get'])
    def trend_analysis(self, request):
        """Get trend analysis report."""
        months = int(request.query_params.get('months', 6))
        end_date_str = request.query_params.get('end_date')

        end_date = self._parse_date(end_date_str) if end_date_str else None

        report = ReportsService.get_trend_analysis(
            user=request.user,
            months=months,
            end_date=end_date
        )
        return Response(report)

    @action(detail=False, methods=['post'])
    def comparison(self, request):
        """Get period comparison report."""
        data = request.data

        try:
            period1_start = self._parse_date(data.get('period1_start'))
            period1_end = self._parse_date(data.get('period1_end'))
            period2_start = self._parse_date(data.get('period2_start'))
            period2_end = self._parse_date(data.get('period2_end'))
        except (ValueError, TypeError):
            return Response(
                {'error': 'Invalid date format. Use YYYY-MM-DD'},
                status=status.HTTP_400_BAD_REQUEST
            )

        report = ReportsService.get_comparison_report(
            user=request.user,
            period1_start=period1_start,
            period1_end=period1_end,
            period2_start=period2_start,
            period2_end=period2_end
        )
        return Response(report)
