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
        return Response({"message": "Notification list"})


class MarkAsReadView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request, notification_id):
        return Response({"message": f"Mark notification {notification_id} as read"})


class MarkAllAsReadView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        return Response({"message": "Mark all notifications as read"})


class NotificationPreferencesView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        return Response({"message": "Notification preferences"})


class UpdatePreferencesView(APIView):
    permission_classes = [IsAuthenticated]
    
    def put(self, request):
        return Response({"message": "Update notification preferences"})


class NotificationCountView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        unread_count = Notification.objects.filter(
            user=request.user,
            is_read=False
        ).count()
        return Response({"unread_count": unread_count})


class WebSocketHealthView(APIView):
    """Health check for WebSocket functionality"""
    permission_classes = [AllowAny]
    
    def get(self, request):
        channel_layer = get_channel_layer()
        
        if channel_layer is None:
            return JsonResponse({
                'websocket_status': 'unavailable',
                'timestamp': timezone.now().isoformat()
            }, status=503)
        
        try:
            # Test channel layer connection
            return JsonResponse({
                'websocket_status': 'healthy',
                'channel_layer': str(type(channel_layer).__name__),
                'timestamp': timezone.now().isoformat()
            })
        except Exception as e:
            return JsonResponse({
                'websocket_status': 'error',
                'error': str(e),
                'timestamp': timezone.now().isoformat()
            }, status=503)