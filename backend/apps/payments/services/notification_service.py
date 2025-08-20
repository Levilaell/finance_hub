"""Service for sending real-time payment notifications via WebSocket"""
import logging
from typing import Dict, Any, Optional
from django.utils import timezone
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

logger = logging.getLogger(__name__)


class PaymentNotificationService:
    """Service for sending payment-related notifications through WebSocket"""
    
    def __init__(self):
        self.channel_layer = get_channel_layer()
    
    def notify_payment_success(self, company_id: int, payment_data: Dict[str, Any]):
        """Notify about successful payment"""
        # Send WebSocket notification
        self._send_to_company_group(company_id, {
            'type': 'payment_success',
            'payment_id': payment_data.get('payment_id'),
            'subscription_id': payment_data.get('subscription_id'),
            'amount': str(payment_data.get('amount', 0)),
            'currency': payment_data.get('currency', 'BRL'),
            'timestamp': timezone.now().isoformat()
        })
        
        # Create notification in database
        try:
            from apps.companies.models import Company
            from apps.notifications.services import NotificationService
            
            company = Company.objects.get(id=company_id)
            amount = payment_data.get('amount', 0)
            currency = payment_data.get('currency', 'BRL')
            
            NotificationService.create_notification(
                event_name='payment_success',
                company=company,
                broadcast=True,
                title="Payment Successful",
                message=f"Payment of {currency} {amount} processed successfully",
                metadata=payment_data
            )
        except Exception as e:
            logger.error(f"Failed to create payment success notification: {e}")
    
    def notify_payment_failed(self, company_id: int, payment_data: Dict[str, Any]):
        """Notify about failed payment"""
        # Send WebSocket notification
        self._send_to_company_group(company_id, {
            'type': 'payment_failed',
            'payment_id': payment_data.get('payment_id'),
            'reason': payment_data.get('reason', 'Payment processing failed'),
            'retry_available': payment_data.get('retry_available', True),
            'timestamp': timezone.now().isoformat()
        })
        
        # Create critical notification in database
        try:
            from apps.companies.models import Company
            from apps.notifications.services import handle_payment_failed
            
            company = Company.objects.get(id=company_id)
            reason = payment_data.get('reason', 'Payment processing failed')
            
            # Notify all company users about payment failure
            handle_payment_failed(
                company=company,
                user=None,  # Broadcast to all
                error_message=reason
            )
        except Exception as e:
            logger.error(f"Failed to create payment failed notification: {e}")
    
    def notify_subscription_updated(self, company_id: int, subscription_data: Dict[str, Any]):
        """Notify about subscription updates"""
        self._send_to_company_group(company_id, {
            'type': 'subscription_updated',
            'subscription_id': subscription_data.get('subscription_id'),
            'status': subscription_data.get('status'),
            'plan': subscription_data.get('plan'),
            'changes': subscription_data.get('changes', {}),
            'timestamp': timezone.now().isoformat()
        })
    
    def notify_payment_method_updated(self, company_id: int, method_data: Dict[str, Any]):
        """Notify about payment method updates"""
        self._send_to_company_group(company_id, {
            'type': 'payment_method_updated',
            'payment_method_id': method_data.get('payment_method_id'),
            'action': method_data.get('action'),  # added, removed, updated
            'details': {
                'brand': method_data.get('brand'),
                'last4': method_data.get('last4'),
                'exp_month': method_data.get('exp_month'),
                'exp_year': method_data.get('exp_year'),
            },
            'timestamp': timezone.now().isoformat()
        })
    
    def notify_trial_ending(self, company_id: int, trial_data: Dict[str, Any]):
        """Notify about trial ending soon"""
        self._send_to_company_group(company_id, {
            'type': 'trial_ending',
            'days_remaining': trial_data.get('days_remaining'),
            'trial_end_date': trial_data.get('trial_end_date'),
            'timestamp': timezone.now().isoformat()
        })
    
    def notify_trial_converted(self, company_id: int, conversion_data: Dict[str, Any]):
        """Notify about successful trial to paid conversion"""
        # Send WebSocket notification
        self._send_to_company_group(company_id, {
            'type': 'trial_converted',
            'subscription_id': conversion_data.get('subscription_id'),
            'plan_name': conversion_data.get('plan_name'),
            'billing_period': conversion_data.get('billing_period'),
            'converted_at': conversion_data.get('converted_at'),
            'timestamp': timezone.now().isoformat()
        })
        
        # Create celebration notification in database
        try:
            from apps.companies.models import Company
            from apps.notifications.services import NotificationService
            
            company = Company.objects.get(id=company_id)
            plan_name = conversion_data.get('plan_name', 'Unknown Plan')
            
            NotificationService.create_notification(
                event_name='trial_converted',
                company=company,
                broadcast=True,
                title="Welcome to Premium! 🎉",
                message=f"Your trial has been successfully converted to {plan_name}. Thank you for choosing us!",
                metadata=conversion_data,
                is_critical=False  # Positive notification
            )
        except Exception as e:
            logger.error(f"Failed to create trial conversion notification: {e}")
    
    def notify_payment_action_required(self, company, payment, invoice_url: Optional[str] = None):
        """Notify about payment requiring additional action (3D Secure, etc)"""
        company_id = company.id if hasattr(company, 'id') else company
        
        # Send WebSocket notification
        self._send_to_company_group(company_id, {
            'type': 'payment_action_required',
            'payment_id': payment.id if hasattr(payment, 'id') else payment.get('id'),
            'amount': str(payment.amount) if hasattr(payment, 'amount') else payment.get('amount'),
            'currency': payment.currency if hasattr(payment, 'currency') else payment.get('currency'),
            'invoice_url': invoice_url,
            'requires_authentication': True,
            'timestamp': timezone.now().isoformat()
        })
        
        # Create urgent notification in database
        try:
            from apps.companies.models import Company
            from apps.notifications.services import NotificationService
            
            if hasattr(company, 'id'):
                company_obj = company
            else:
                company_obj = Company.objects.get(id=company_id)
            
            amount = payment.amount if hasattr(payment, 'amount') else payment.get('amount', 0)
            currency = payment.currency if hasattr(payment, 'currency') else payment.get('currency', 'BRL')
            
            message = f"Payment of {currency} {amount} requires additional authentication. Please complete the verification process."
            if invoice_url:
                message += f" Click here to complete: {invoice_url}"
            
            NotificationService.create_notification(
                event_name='payment_action_required',
                company=company_obj,
                broadcast=True,
                title="Payment Authentication Required",
                message=message,
                metadata={
                    'payment_id': payment.id if hasattr(payment, 'id') else payment.get('id'),
                    'invoice_url': invoice_url,
                    'requires_3ds': True
                },
                is_critical=True  # Requires user action
            )
        except Exception as e:
            logger.error(f"Failed to create payment action required notification: {e}")
    
    def notify_usage_limit_warning(self, company_id: int, usage_data: Dict[str, Any]):
        """Notify about approaching usage limits"""
        self._send_to_company_group(company_id, {
            'type': 'usage_limit_warning',
            'usage_type': usage_data.get('usage_type'),
            'current': usage_data.get('current'),
            'limit': usage_data.get('limit'),
            'percentage': usage_data.get('percentage'),
            'timestamp': timezone.now().isoformat()
        })
    
    def notify_checkout_completed(self, session_id: str, checkout_data: Dict[str, Any]):
        """Notify specific checkout session about completion"""
        group_name = f'checkout_{session_id}'
        
        async_to_sync(self.channel_layer.group_send)(
            group_name,
            {
                'type': 'checkout_completed',
                'session_id': session_id,
                'subscription_id': checkout_data.get('subscription_id'),
                'timestamp': timezone.now().isoformat()
            }
        )
    
    def notify_checkout_failed(self, session_id: str, reason: str):
        """Notify specific checkout session about failure"""
        group_name = f'checkout_{session_id}'
        
        async_to_sync(self.channel_layer.group_send)(
            group_name,
            {
                'type': 'checkout_failed',
                'session_id': session_id,
                'reason': reason,
                'timestamp': timezone.now().isoformat()
            }
        )
    
    def _send_to_company_group(self, company_id: int, message: Dict[str, Any]):
        """Send message to company's payment group"""
        group_name = f'payment_updates_{company_id}'
        
        try:
            async_to_sync(self.channel_layer.group_send)(
                group_name,
                message
            )
            logger.info(
                f"Sent {message['type']} notification to company {company_id}"
            )
        except Exception as e:
            logger.error(
                f"Failed to send notification to company {company_id}: {e}"
            )


# Singleton instance
notification_service = PaymentNotificationService()


def notify_payment_event(event_type: str, company_id: int, data: Dict[str, Any]):
    """Convenience function to notify payment events"""
    if event_type == 'payment_success':
        notification_service.notify_payment_success(company_id, data)
    elif event_type == 'payment_failed':
        notification_service.notify_payment_failed(company_id, data)
    elif event_type == 'subscription_updated':
        notification_service.notify_subscription_updated(company_id, data)
    elif event_type == 'payment_method_updated':
        notification_service.notify_payment_method_updated(company_id, data)
    elif event_type == 'trial_ending':
        notification_service.notify_trial_ending(company_id, data)
    elif event_type == 'trial_converted':
        notification_service.notify_trial_converted(company_id, data)
    elif event_type == 'usage_limit_warning':
        notification_service.notify_usage_limit_warning(company_id, data)
    else:
        logger.warning(f"Unknown payment event type: {event_type}")