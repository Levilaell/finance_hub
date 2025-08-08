"""
Simplified notification views focused on essentials
"""
from django.core.cache import cache
from django.db import transaction
from django.utils import timezone
from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
import logging

from .models import Notification
from .serializers import (
    NotificationSerializer, 
    NotificationListSerializer
)
from .services import NotificationService

logger = logging.getLogger(__name__)


class NotificationPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 50


class NotificationListView(APIView):
    """
    List notifications with filtering and pagination
    """
    permission_classes = [IsAuthenticated]
    pagination_class = NotificationPagination
    
    def get(self, request):
        company = getattr(request.user, 'company', None)
        if not company:
            return Response(
                {"error": "User not associated with a company"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Base queryset
        queryset = Notification.objects.filter(
            company=company,
            user=request.user
        ).select_related('user', 'company')
        
        # Apply filters
        event = request.query_params.get('event')
        if event:
            queryset = queryset.filter(event=event)
        
        is_critical = request.query_params.get('is_critical')
        if is_critical is not None:
            queryset = queryset.filter(is_critical=is_critical.lower() == 'true')
        
        is_read = request.query_params.get('is_read')
        if is_read is not None:
            queryset = queryset.filter(is_read=is_read.lower() == 'true')
        
        # Order by created_at descending
        queryset = queryset.order_by('-created_at')
        
        # Paginate
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(queryset, request, view=self)
        
        if page is not None:
            serializer = NotificationListSerializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)
        
        serializer = NotificationListSerializer(queryset, many=True)
        return Response(serializer.data)


class NotificationDetailView(APIView):
    """
    Get single notification detail
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request, notification_id):
        try:
            notification = Notification.objects.select_related(
                'user', 'company'
            ).get(
                id=notification_id,
                user=request.user
            )
        except Notification.DoesNotExist:
            return Response(
                {"error": "Notification not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = NotificationSerializer(notification)
        return Response(serializer.data)


class MarkAsReadView(APIView):
    """
    Mark notification(s) as read
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request, notification_id=None):
        if notification_id:
            # Mark single notification as read
            try:
                notification = Notification.objects.get(
                    id=notification_id,
                    user=request.user
                )
                
                if not notification.is_read:
                    notification.mark_as_read()
                    
                    # Update unread count cache
                    NotificationService._update_unread_count_cache(
                        notification.company_id,
                        request.user.id
                    )
                
                serializer = NotificationSerializer(notification)
                return Response(serializer.data)
                
            except Notification.DoesNotExist:
                return Response(
                    {"error": "Notification not found"},
                    status=status.HTTP_404_NOT_FOUND
                )
        else:
            # Mark all as read
            company = getattr(request.user, 'company', None)
            if not company:
                return Response(
                    {"error": "User not associated with a company"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            with transaction.atomic():
                updated_count = Notification.objects.filter(
                    company=company,
                    user=request.user,
                    is_read=False
                ).update(
                    is_read=True,
                    read_at=timezone.now()
                )
                
                # Update cache
                NotificationService._update_unread_count_cache(
                    company.id,
                    request.user.id
                )
            
            return Response({
                "message": "All notifications marked as read",
                "count": updated_count
            })


class UnreadCountView(APIView):
    """
    Get unread notification count
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        company = getattr(request.user, 'company', None)
        if not company:
            return Response({"count": 0})
        
        count = Notification.get_unread_count(company, request.user)
        return Response({"count": count})


class PendingNotificationsView(APIView):
    """
    Get pending notifications (polling fallback)
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        company = getattr(request.user, 'company', None)
        if not company:
            return Response({"notifications": []})
        
        notifications = NotificationService.get_pending_notifications(
            request.user, 
            company
        )
        
        serializer = NotificationListSerializer(notifications, many=True)
        return Response({"notifications": serializer.data})


class NotificationDeleteView(APIView):
    """
    Delete a notification (optional endpoint)
    """
    permission_classes = [IsAuthenticated]
    
    def delete(self, request, notification_id):
        try:
            notification = Notification.objects.get(
                id=notification_id,
                user=request.user
            )
            
            # Update cache if unread
            if not notification.is_read:
                NotificationService._update_unread_count_cache(
                    notification.company_id,
                    request.user.id
                )
            
            notification.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
            
        except Notification.DoesNotExist:
            return Response(
                {"error": "Notification not found"},
                status=status.HTTP_404_NOT_FOUND
            )