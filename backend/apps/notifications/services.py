"""
Simplified notification service with reliable delivery
"""
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.core.cache import cache
from django.db import transaction
from django.utils import timezone
from django.contrib.auth import get_user_model
import logging
import threading
import time
from typing import Dict, Any, Optional, List

from .models import Notification
from .constants import (
    MAX_NOTIFICATION_RETRIES,
    RETRY_WORKER_SLEEP_SECONDS,
    RETRY_BATCH_SIZE,
    UNREAD_COUNT_CACHE_TIMEOUT,
    USER_ONLINE_CACHE_TIMEOUT,
    PENDING_NOTIFICATIONS_LIMIT,
    OLD_NOTIFICATIONS_CLEANUP_DAYS
)

User = get_user_model()
logger = logging.getLogger(__name__)
channel_layer = get_channel_layer()


class NotificationService:
    """
    Simplified notification service with WebSocket delivery and reliability
    """
    
    @staticmethod
    def create_notification(
        event_name: str,
        company,
        user: Optional[User] = None,
        broadcast: bool = False,
        title: Optional[str] = None,
        message: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        action_url: Optional[str] = None,
        event_id: Optional[str] = None
    ) -> Optional[Notification]:
        """
        Create and deliver notification with deduplication
        """
        try:
            if broadcast and user is None:
                # Create notifications for all active company users
                notifications = []
                users = User.objects.filter(company=company, is_active=True)
                
                with transaction.atomic():
                    for u in users:
                        notification = Notification.create_from_event(
                            event_name=event_name,
                            company=company,
                            user=u,
                            title=title,
                            message=message,
                            metadata=metadata,
                            action_url=action_url,
                            event_id=event_id
                        )
                        if notification:
                            notifications.append(notification)
                
                # Deliver all notifications
                for notification in notifications:
                    NotificationService._deliver_via_websocket(notification)
                
                # Start background retry thread if any failed
                failed = [n for n in notifications if n.delivery_status != 'delivered']
                if failed:
                    NotificationService._start_retry_thread()
                
                return notifications[0] if notifications else None
            else:
                # Create single notification
                notification = Notification.create_from_event(
                    event_name=event_name,
                    company=company,
                    user=user,
                    title=title,
                    message=message,
                    metadata=metadata,
                    action_url=action_url,
                    event_id=event_id
                )
                
                if notification:
                    # Try immediate delivery
                    delivered = NotificationService._deliver_via_websocket(notification)
                    
                    # Start retry thread if failed
                    if not delivered:
                        NotificationService._start_retry_thread()
                
                return notification
                
        except Exception as e:
            logger.error(f"Failed to create notification: {e}")
            return None
    
    @staticmethod
    def _deliver_via_websocket(notification: Notification) -> bool:
        """
        Attempt to deliver notification via WebSocket
        """
        try:
            # Check if user has active WebSocket connection
            user_online = NotificationService._is_user_online(notification.user_id)
            
            if not user_online and not notification.is_critical:
                # Skip non-critical notifications for offline users
                logger.info(f"User {notification.user_id} offline, queuing notification {notification.id}")
                return False
            
            # Prepare notification data
            notification_data = {
                'id': str(notification.id),
                'event': notification.event,
                'is_critical': notification.is_critical,
                'title': notification.title,
                'message': notification.message,
                'metadata': notification.metadata,
                'action_url': notification.action_url,
                'created_at': notification.created_at.isoformat(),
                'is_read': notification.is_read,
            }
            
            # Send via WebSocket
            async_to_sync(channel_layer.group_send)(
                f"notifications_{notification.user_id}",
                {
                    "type": "notification_message",
                    "notification": notification_data
                }
            )
            
            # Mark as delivered
            notification.mark_as_delivered()
            
            # Update unread count cache
            NotificationService._update_unread_count_cache(
                notification.company_id,
                notification.user_id
            )
            
            logger.info(f"Notification {notification.id} delivered to user {notification.user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to deliver notification {notification.id}: {e}")
            return False
    
    @staticmethod
    def _is_user_online(user_id: int) -> bool:
        """
        Check if user has active WebSocket connection (via Redis)
        """
        try:
            # Simple online check - can be enhanced with Redis presence
            online_key = f"ws:online:{user_id}"
            return cache.get(online_key, False)
        except Exception:
            return False
    
    @staticmethod
    def _update_unread_count_cache(company_id: int, user_id: int):
        """
        Update cached unread count and send WebSocket update
        """
        try:
            # Clear cache to force recalculation
            cache_key = f'notifications:unread_count:{company_id}:{user_id}'
            cache.delete(cache_key)
            
            # Get fresh count
            count = Notification.objects.filter(
                company_id=company_id,
                user_id=user_id,
                is_read=False
            ).count()
            
            # Cache for 5 minutes
            cache.set(cache_key, count, timeout=UNREAD_COUNT_CACHE_TIMEOUT)
            
            # Send WebSocket update
            async_to_sync(channel_layer.group_send)(
                f"notifications_{user_id}",
                {
                    "type": "unread_count_update",
                    "count": count
                }
            )
        except Exception as e:
            logger.error(f"Failed to update unread count: {e}")
    
    # Simple retry mechanism without Celery
    _retry_thread = None
    _retry_lock = threading.Lock()
    
    @staticmethod
    def _start_retry_thread():
        """
        Start background thread for retrying failed notifications
        """
        with NotificationService._retry_lock:
            if NotificationService._retry_thread is None or not NotificationService._retry_thread.is_alive():
                NotificationService._retry_thread = threading.Thread(
                    target=NotificationService._retry_worker,
                    daemon=True
                )
                NotificationService._retry_thread.start()
    
    @staticmethod
    def _retry_worker():
        """
        Background worker to retry failed notifications
        """
        while True:
            try:
                # Find notifications that need retry
                failed_notifications = Notification.objects.filter(
                    delivery_status='failed'
                ).select_related('user', 'company')[:RETRY_BATCH_SIZE]
                
                if not failed_notifications:
                    # No more failed notifications, exit thread
                    break
                
                for notification in failed_notifications:
                    if notification.should_retry():
                        notification.increment_retry()
                        delivered = NotificationService._deliver_via_websocket(notification)
                        
                        if not delivered and notification.retry_count >= MAX_NOTIFICATION_RETRIES:
                            # Max retries reached, mark as permanently failed
                            notification.mark_as_failed()
                            logger.error(f"Notification {notification.id} permanently failed after 3 retries")
                
                # Wait before next retry batch
                time.sleep(RETRY_WORKER_SLEEP_SECONDS)
                
            except Exception as e:
                logger.error(f"Error in retry worker: {e}")
                time.sleep(60)
        
        # Clear thread reference when done
        with NotificationService._retry_lock:
            NotificationService._retry_thread = None
    
    @staticmethod
    def get_pending_notifications(user: User, company) -> List[Notification]:
        """
        Get pending notifications for user (for polling fallback)
        """
        return list(Notification.objects.filter(
            company=company,
            user=user,
            delivery_status='pending'
        ).order_by('-created_at')[:50])
    
    @staticmethod
    def mark_user_online(user_id: int):
        """
        Mark user as online when WebSocket connects
        """
        cache.set(f"ws:online:{user_id}", True, timeout=USER_ONLINE_CACHE_TIMEOUT)
        
        # Deliver any pending notifications
        pending = Notification.objects.filter(
            user_id=user_id,
            delivery_status='pending'
        )[:PENDING_NOTIFICATIONS_LIMIT]
        
        for notification in pending:
            NotificationService._deliver_via_websocket(notification)
    
    @staticmethod
    def mark_user_offline(user_id: int):
        """
        Mark user as offline when WebSocket disconnects
        """
        cache.delete(f"ws:online:{user_id}")
    
    @staticmethod
    def cleanup_old_notifications(days: int = OLD_NOTIFICATIONS_CLEANUP_DAYS):
        """
        Clean up old read notifications
        """
        cutoff_date = timezone.now() - timezone.timedelta(days=days)
        
        deleted_count, _ = Notification.objects.filter(
            is_read=True,
            read_at__lt=cutoff_date
        ).delete()
        
        logger.info(f"Cleaned up {deleted_count} old notifications")
        return deleted_count


# Event handlers for key system events
def handle_account_connected(company, user=None, account_name="Financial Account"):
    """Handle account connection event"""
    NotificationService.create_notification(
        event_name='account_connected',
        company=company,
        user=user,
        broadcast=(user is None),
        title="Account Connected",
        message=f"{account_name} has been successfully connected",
        metadata={'account_name': account_name}
    )


def handle_account_sync_failed(company, user=None, account_name="Account", error="Unknown error"):
    """Handle sync failure event"""
    NotificationService.create_notification(
        event_name='account_sync_failed',
        company=company,
        user=user,
        broadcast=(user is None),
        title="Sync Failed",
        message=f"Failed to sync {account_name}: {error}",
        metadata={'account_name': account_name, 'error': error}
    )


def handle_low_balance(company, user, account_name, balance, threshold):
    """Handle low balance event"""
    NotificationService.create_notification(
        event_name='low_balance',
        company=company,
        user=user,
        title="Low Balance Alert",
        message=f"{account_name} balance (${balance:.2f}) is below ${threshold:.2f}",
        metadata={
            'account_name': account_name,
            'balance': float(balance),
            'threshold': float(threshold)
        },
        action_url=f"/accounts"
    )


def handle_large_transaction(company, user, amount, description, account_name):
    """Handle large transaction event"""
    NotificationService.create_notification(
        event_name='large_transaction',
        company=company,
        user=user,
        title="Large Transaction Detected",
        message=f"${abs(amount):.2f} transaction: {description}",
        metadata={
            'amount': float(amount),
            'description': description,
            'account_name': account_name
        },
        action_url="/transactions"
    )


def handle_payment_failed(company, user, error_message="Payment processing failed"):
    """Handle payment failure event"""
    NotificationService.create_notification(
        event_name='payment_failed',
        company=company,
        user=user,
        title="Payment Failed",
        message=error_message,
        metadata={'error': error_message},
        action_url="/subscription"
    )


def handle_report_ready(company, user, report_name, report_id):
    """Handle report ready event"""
    NotificationService.create_notification(
        event_name='report_ready',
        company=company,
        user=user,
        title="Report Ready",
        message=f"Your {report_name} is ready for download",
        metadata={
            'report_name': report_name,
            'report_id': str(report_id)
        },
        action_url=f"/reports/{report_id}"
    )