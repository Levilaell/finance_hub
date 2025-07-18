from channels.layers import get_channel_layer
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.http import JsonResponse
from django.utils import timezone

from .models import Notification, NotificationPreference


class NotificationListView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        notifications = Notification.objects.filter(user=request.user).order_by('-created_at')
        # TODO: Implement proper serialization
        return Response({"results": [], "count": 0})


class NotificationDetailView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request, notification_id):
        # TODO: Implement get notification detail
        return Response({"id": notification_id})


class NotificationUpdateView(APIView):
    permission_classes = [IsAuthenticated]
    
    def patch(self, request, notification_id):
        # TODO: Implement update notification (mark as read)
        return Response({"id": notification_id, "is_read": True})


class NotificationDeleteView(APIView):
    permission_classes = [IsAuthenticated]
    
    def delete(self, request, notification_id):
        # TODO: Implement delete notification
        return Response(status=status.HTTP_204_NO_CONTENT)


class MarkAllAsReadView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        return Response({"message": "Mark all notifications as read"})


class UnreadCountView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        count = Notification.objects.filter(user=request.user, is_read=False).count()
        return Response({"count": count})


class DeleteAllReadView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        deleted = Notification.objects.filter(user=request.user, is_read=True).delete()
        return Response({"deleted": deleted[0]})


