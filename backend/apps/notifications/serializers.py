"""
Simplified notification serializers
"""
from rest_framework import serializers
from .models import Notification


class NotificationSerializer(serializers.ModelSerializer):
    """
    Simplified notification serializer
    """
    # Display fields
    event_display = serializers.CharField(source='get_event_display', read_only=True)
    
    class Meta:
        model = Notification
        fields = [
            'id',
            'event',
            'event_display',
            'is_critical',
            'title',
            'message',
            'metadata',
            'action_url',
            'is_read',
            'read_at',
            'delivery_status',
            'created_at',
        ]
        read_only_fields = [
            'id',
            'event_display',
            'delivery_status',
            'created_at',
        ]


class NotificationListSerializer(serializers.ModelSerializer):
    """
    Lightweight serializer for notification lists
    """
    class Meta:
        model = Notification
        fields = [
            'id',
            'event',
            'is_critical',
            'title',
            'message',
            'action_url',
            'is_read',
            'created_at',
        ]