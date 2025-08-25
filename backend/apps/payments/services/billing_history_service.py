"""
Billing history and invoice management service
Provides comprehensive invoice and payment history functionality
"""
import logging
from typing import Dict, Any, Optional, List, Tuple
from decimal import Decimal
from datetime import datetime, timedelta
from django.utils import timezone
from django.db import models
from django.core.paginator import Paginator
from django.template.loader import render_to_string
from django.http import HttpResponse
import json

from .stripe_service import StripeService
from .audit_service import PaymentAuditService
from ..exceptions import BillingException

logger = logging.getLogger(__name__)


class BillingHistoryService:
    """Manages billing history and invoice operations"""
    
    def __init__(self):
        self.stripe_service = StripeService()
    
    def get_billing_history(self,
                          company: 'Company',
                          limit: int = 50,
                          page: int = 1,
                          start_date: Optional[datetime] = None,
                          end_date: Optional[datetime] = None,
                          status_filter: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Get comprehensive billing history for a company
        
        Args:
            company: Company instance
            limit: Number of items per page
            page: Page number
            start_date: Filter by start date
            end_date: Filter by end date
            status_filter: Filter by payment status
            
        Returns:
            Paginated billing history with metadata
        """
        from ..models import Payment, Subscription
        
        # Build query
        queryset = Payment.objects.filter(company=company)
        
        # Apply filters
        if start_date:
            queryset = queryset.filter(created_at__gte=start_date)
        if end_date:
            queryset = queryset.filter(created_at__lte=end_date)
        if status_filter:
            queryset = queryset.filter(status__in=status_filter)
        
        # Order by most recent first
        queryset = queryset.order_by('-created_at')
        
        # Include related data
        queryset = queryset.select_related(
            'subscription__plan',
            'payment_method'
        )
        
        # Paginate results
        paginator = Paginator(queryset, limit)
        page_obj = paginator.get_page(page)
        
        # Build response
        history_items = []
        for payment in page_obj:
            item = {
                'id': payment.id,
                'date': payment.created_at,
                'amount': float(payment.amount),
                'currency': payment.currency,
                'status': payment.status,
                'description': payment.description,
                'payment_method': {
                    'brand': payment.payment_method.brand if payment.payment_method else None,
                    'last4': payment.payment_method.last4 if payment.payment_method else None
                },
                'invoice_id': payment.stripe_invoice_id,
                'receipt_available': payment.status == 'succeeded',
                'refundable': self._is_refundable(payment),
                'metadata': payment.metadata
            }
            
            # Add subscription info if available
            if payment.subscription:
                item['subscription'] = {
                    'plan_name': payment.subscription.plan.display_name,
                    'billing_period': payment.subscription.billing_period
                }
            
            history_items.append(item)
        
        # Get summary statistics
        summary = self._get_billing_summary(company, start_date, end_date)
        
        return {
            'items': history_items,
            'pagination': {
                'current_page': page,
                'total_pages': paginator.num_pages,
                'total_items': paginator.count,
                'has_next': page_obj.has_next(),
                'has_previous': page_obj.has_previous()
            },
            'summary': summary,
            'filters_applied': {
                'start_date': start_date.isoformat() if start_date else None,
                'end_date': end_date.isoformat() if end_date else None,
                'status_filter': status_filter
            }
        }
    
    def get_invoice(self,
                   invoice_id: str,
                   company: 'Company',
                   user: Optional['User'] = None) -> Dict[str, Any]:
        """
        Get detailed invoice information
        
        Args:
            invoice_id: Stripe invoice ID
            company: Company instance (for authorization)
            user: User requesting the invoice
            
        Returns:
            Invoice details
            
        Raises:
            BillingException: If invoice not found or unauthorized
        """
        try:
            # Retrieve invoice from Stripe
            invoice = self.stripe_service.retrieve_invoice(invoice_id)
            
            # Verify invoice belongs to company
            subscription = company.subscription
            if not subscription or invoice['customer'] != subscription.stripe_customer_id:
                raise BillingException("Invoice not found or unauthorized")
            
            # Build detailed invoice data
            invoice_data = {
                'id': invoice['id'],
                'number': invoice.get('number'),
                'status': invoice['status'],
                'amount_due': Decimal(invoice['amount_due']) / 100,
                'amount_paid': Decimal(invoice['amount_paid']) / 100,
                'amount_remaining': Decimal(invoice['amount_remaining']) / 100,
                'currency': invoice['currency'].upper(),
                'created': datetime.fromtimestamp(invoice['created'], tz=timezone.utc),
                'due_date': datetime.fromtimestamp(invoice['due_date'], tz=timezone.utc) if invoice.get('due_date') else None,
                'paid_at': datetime.fromtimestamp(invoice['status_transitions']['paid_at'], tz=timezone.utc) if invoice.get('status_transitions', {}).get('paid_at') else None,
                'period_start': datetime.fromtimestamp(invoice['period_start'], tz=timezone.utc),
                'period_end': datetime.fromtimestamp(invoice['period_end'], tz=timezone.utc),
                'hosted_invoice_url': invoice.get('hosted_invoice_url'),
                'invoice_pdf': invoice.get('invoice_pdf'),
                'line_items': self._format_line_items(invoice.get('lines', {}).get('data', [])),
                'tax': Decimal(invoice.get('tax', 0)) / 100,
                'subtotal': Decimal(invoice['subtotal']) / 100,
                'total': Decimal(invoice['total']) / 100,
                'billing_reason': invoice.get('billing_reason'),
                'attempt_count': invoice.get('attempt_count', 0)
            }
            
            # Add payment method info if available
            if invoice.get('charge'):
                try:
                    charge = self.stripe_service.stripe.Charge.retrieve(invoice['charge'])
                    invoice_data['payment_method'] = {
                        'brand': charge.get('payment_method_details', {}).get('card', {}).get('brand'),
                        'last4': charge.get('payment_method_details', {}).get('card', {}).get('last4')
                    }
                except Exception:
                    pass
            
            # Log invoice access
            PaymentAuditService.log_payment_action(
                action='invoice_viewed',
                user=user,
                company=company,
                metadata={
                    'invoice_id': invoice_id,
                    'invoice_number': invoice_data['number']
                }
            )
            
            return invoice_data
            
        except Exception as e:
            logger.error(f"Failed to retrieve invoice {invoice_id}: {e}")
            raise BillingException(f"Failed to retrieve invoice: {str(e)}")
    
    def get_upcoming_invoice(self, company: 'Company') -> Optional[Dict[str, Any]]:
        """
        Get upcoming invoice preview
        
        Args:
            company: Company instance
            
        Returns:
            Upcoming invoice data or None if no upcoming invoice
        """
        subscription = company.subscription
        if not subscription or not subscription.stripe_customer_id:
            return None
        
        try:
            # Get upcoming invoice from Stripe
            upcoming = self.stripe_service.upcoming_invoice(
                customer_id=subscription.stripe_customer_id
            )
            
            if not upcoming:
                return None
            
            return {
                'amount_due': Decimal(upcoming['amount_due']) / 100,
                'currency': upcoming['currency'].upper(),
                'next_payment_attempt': datetime.fromtimestamp(
                    upcoming['next_payment_attempt'], tz=timezone.utc
                ) if upcoming.get('next_payment_attempt') else None,
                'period_start': datetime.fromtimestamp(
                    upcoming['period_start'], tz=timezone.utc
                ),
                'period_end': datetime.fromtimestamp(
                    upcoming['period_end'], tz=timezone.utc
                ),
                'line_items': self._format_line_items(upcoming.get('lines', {}).get('data', [])),
                'subtotal': Decimal(upcoming['subtotal']) / 100,
                'tax': Decimal(upcoming.get('tax', 0)) / 100,
                'total': Decimal(upcoming['total']) / 100
            }
            
        except Exception as e:
            logger.error(f"Failed to get upcoming invoice: {e}")
            return None
    
    def download_invoice(self,
                       invoice_id: str,
                       company: 'Company',
                       format: str = 'pdf',
                       user: Optional['User'] = None) -> HttpResponse:
        """
        Download invoice in specified format
        
        Args:
            invoice_id: Stripe invoice ID
            company: Company instance
            format: Download format ('pdf' or 'html')
            user: User downloading the invoice
            
        Returns:
            HttpResponse with invoice file
            
        Raises:
            BillingException: If download fails
        """
        # Get invoice data
        invoice_data = self.get_invoice(invoice_id, company, user)
        
        if format == 'pdf' and invoice_data.get('invoice_pdf'):
            # Download PDF from Stripe
            try:
                import requests
                response = requests.get(invoice_data['invoice_pdf'])
                response.raise_for_status()
                
                # Create HTTP response
                http_response = HttpResponse(
                    response.content,
                    content_type='application/pdf'
                )
                http_response['Content-Disposition'] = f'attachment; filename="invoice_{invoice_data["number"]}.pdf"'
                
                # Log download
                PaymentAuditService.log_payment_action(
                    action='invoice_downloaded',
                    user=user,
                    company=company,
                    metadata={
                        'invoice_id': invoice_id,
                        'format': 'pdf'
                    }
                )
                
                return http_response
                
            except Exception as e:
                logger.error(f"Failed to download invoice PDF: {e}")
                # Fall back to HTML generation
                format = 'html'
        
        if format == 'html':
            # Generate HTML invoice
            from ..models import Company
            
            # Get company details
            company_data = {
                'name': company.name,
                'email': company.owner.email if company.owner else '',
                'address': company.metadata.get('address', {})
            }
            
            # Render HTML template
            html_content = render_to_string('payments/invoice.html', {
                'invoice': invoice_data,
                'company': company_data,
                'generated_at': timezone.now()
            })
            
            # Create HTTP response
            http_response = HttpResponse(
                html_content,
                content_type='text/html'
            )
            http_response['Content-Disposition'] = f'inline; filename="invoice_{invoice_data["number"]}.html"'
            
            # Log download
            PaymentAuditService.log_payment_action(
                action='invoice_downloaded',
                user=user,
                company=company,
                metadata={
                    'invoice_id': invoice_id,
                    'format': 'html'
                }
            )
            
            return http_response
        
        raise BillingException(f"Unsupported invoice format: {format}")
    
    def get_payment_receipt(self,
                          payment_id: int,
                          company: 'Company',
                          user: Optional['User'] = None) -> Dict[str, Any]:
        """
        Get payment receipt data
        
        Args:
            payment_id: Payment ID
            company: Company instance
            user: User requesting receipt
            
        Returns:
            Receipt data
            
        Raises:
            BillingException: If receipt not available
        """
        from ..models import Payment
        
        try:
            # Get payment record
            payment = Payment.objects.get(
                id=payment_id,
                company=company,
                status='succeeded'
            )
        except Payment.DoesNotExist:
            raise BillingException("Payment not found or receipt not available")
        
        # Build receipt data
        receipt = {
            'payment_id': payment.id,
            'date': payment.paid_at or payment.created_at,
            'amount': float(payment.amount),
            'currency': payment.currency,
            'description': payment.description,
            'payment_method': {
                'brand': payment.payment_method.brand if payment.payment_method else 'Unknown',
                'last4': payment.payment_method.last4 if payment.payment_method else '****'
            },
            'company': {
                'name': company.name,
                'email': company.owner.email if company.owner else ''
            },
            'transaction_id': payment.stripe_payment_intent_id or payment.id,
            'invoice_id': payment.stripe_invoice_id
        }
        
        # Add subscription details if available
        if payment.subscription:
            receipt['subscription'] = {
                'plan': payment.subscription.plan.display_name,
                'billing_period': payment.subscription.billing_period
            }
        
        # Log receipt access
        PaymentAuditService.log_payment_action(
            action='receipt_viewed',
            user=user,
            company=company,
            payment_id=payment_id
        )
        
        return receipt
    
    def get_tax_summary(self,
                       company: 'Company',
                       year: int,
                       user: Optional['User'] = None) -> Dict[str, Any]:
        """
        Get annual tax summary for a company
        
        Args:
            company: Company instance
            year: Tax year
            user: User requesting summary
            
        Returns:
            Tax summary data
        """
        from ..models import Payment
        
        # Get all successful payments for the year
        start_date = timezone.datetime(year, 1, 1, tzinfo=timezone.utc)
        end_date = timezone.datetime(year, 12, 31, 23, 59, 59, tzinfo=timezone.utc)
        
        payments = Payment.objects.filter(
            company=company,
            status='succeeded',
            created_at__gte=start_date,
            created_at__lte=end_date
        ).order_by('created_at')
        
        # Calculate totals
        total_paid = Decimal('0.00')
        total_tax = Decimal('0.00')
        payments_by_month = {}
        
        for payment in payments:
            month_key = payment.created_at.strftime('%Y-%m')
            if month_key not in payments_by_month:
                payments_by_month[month_key] = {
                    'amount': Decimal('0.00'),
                    'tax': Decimal('0.00'),
                    'count': 0
                }
            
            payments_by_month[month_key]['amount'] += payment.amount
            payments_by_month[month_key]['tax'] += payment.metadata.get('tax_amount', Decimal('0.00'))
            payments_by_month[month_key]['count'] += 1
            
            total_paid += payment.amount
            total_tax += payment.metadata.get('tax_amount', Decimal('0.00'))
        
        # Build summary
        summary = {
            'year': year,
            'company': {
                'name': company.name,
                'tax_id': company.metadata.get('tax_id')
            },
            'total_paid': float(total_paid),
            'total_tax': float(total_tax),
            'currency': 'BRL',
            'payment_count': len(payments),
            'monthly_breakdown': [
                {
                    'month': month,
                    'amount': float(data['amount']),
                    'tax': float(data['tax']),
                    'payment_count': data['count']
                }
                for month, data in sorted(payments_by_month.items())
            ],
            'generated_at': timezone.now()
        }
        
        # Log tax summary access
        PaymentAuditService.log_payment_action(
            action='tax_summary_generated',
            user=user,
            company=company,
            metadata={
                'year': year,
                'total_amount': float(total_paid)
            }
        )
        
        return summary
    
    def _get_billing_summary(self,
                           company: 'Company',
                           start_date: Optional[datetime] = None,
                           end_date: Optional[datetime] = None) -> Dict[str, Any]:
        """
        Get billing summary statistics
        
        Args:
            company: Company instance
            start_date: Start date for summary
            end_date: End date for summary
            
        Returns:
            Summary statistics
        """
        from ..models import Payment
        from django.db.models import Sum, Count, Avg
        
        # Build query
        queryset = Payment.objects.filter(company=company)
        
        if start_date:
            queryset = queryset.filter(created_at__gte=start_date)
        if end_date:
            queryset = queryset.filter(created_at__lte=end_date)
        
        # Calculate aggregates
        aggregates = queryset.aggregate(
            total_amount=Sum('amount'),
            total_count=Count('id'),
            avg_amount=Avg('amount')
        )
        
        # Status breakdown
        status_breakdown = queryset.values('status').annotate(
            count=Count('id'),
            total=Sum('amount')
        )
        
        return {
            'total_amount': float(aggregates['total_amount'] or 0),
            'total_payments': aggregates['total_count'] or 0,
            'average_amount': float(aggregates['avg_amount'] or 0),
            'status_breakdown': {
                item['status']: {
                    'count': item['count'],
                    'total': float(item['total'] or 0)
                }
                for item in status_breakdown
            },
            'period': {
                'start': start_date.isoformat() if start_date else None,
                'end': end_date.isoformat() if end_date else None
            }
        }
    
    def _format_line_items(self, line_items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Format Stripe line items for display
        
        Args:
            line_items: Raw line items from Stripe
            
        Returns:
            Formatted line items
        """
        formatted = []
        
        for item in line_items:
            formatted_item = {
                'description': item.get('description', ''),
                'amount': Decimal(item.get('amount', 0)) / 100,
                'currency': item.get('currency', 'brl').upper(),
                'quantity': item.get('quantity', 1),
                'unit_amount': Decimal(item.get('unit_amount', 0)) / 100 if item.get('unit_amount') else None,
                'type': item.get('type', 'subscription'),
                'proration': item.get('proration', False)
            }
            
            # Add period information if available
            if item.get('period'):
                formatted_item['period'] = {
                    'start': datetime.fromtimestamp(
                        item['period']['start'], tz=timezone.utc
                    ),
                    'end': datetime.fromtimestamp(
                        item['period']['end'], tz=timezone.utc
                    )
                }
            
            formatted.append(formatted_item)
        
        return formatted
    
    def _is_refundable(self, payment: 'Payment') -> bool:
        """
        Check if a payment is eligible for refund
        
        Args:
            payment: Payment instance
            
        Returns:
            True if refundable
        """
        if payment.status != 'succeeded':
            return False
        
        # Check if already refunded
        if payment.metadata.get('refunded'):
            return False
        
        # Check time limit (e.g., 90 days)
        if payment.paid_at:
            days_since_payment = (timezone.now() - payment.paid_at).days
            if days_since_payment > 90:
                return False
        
        return True