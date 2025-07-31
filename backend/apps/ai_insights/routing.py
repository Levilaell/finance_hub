"""
WebSocket URL routing for AI Insights
"""
from django.urls import path
from . import consumers

websocket_urlpatterns = [
    path('ws/ai-chat/<str:conversation_id>/', consumers.ChatConsumer.as_asgi()),
]