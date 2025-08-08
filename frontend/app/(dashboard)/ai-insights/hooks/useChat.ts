import { useState, useEffect, useCallback } from 'react';
import { AIMessage, AIConversation, WSMessage, WSAIResponse, WSError, WSTypingIndicator } from '../types/ai-insights.types';
import { aiInsightsService } from '../services/ai-insights.service';
import { useAuthStore } from '@/store/auth-store';
import { useSecureWebSocket } from './useSecureWebSocket';
import toast from 'react-hot-toast';

export function useChat(conversationId: string | null) {
  const [messages, setMessages] = useState<AIMessage[]>([]);
  const [loading, setLoading] = useState(false);
  const [isTyping, setIsTyping] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  const { user } = useAuthStore();

  // WebSocket URL
  const wsUrl = conversationId 
    ? `${process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000'}/ws/ai-chat/${conversationId}/`
    : null;

  // Handle WebSocket messages
  const handleWebSocketMessage = useCallback((data: WSMessage) => {
    try {
      switch (data.type) {
        case 'connection_established':
          // Connection established successfully
          break;
          
        case 'ai_response':
          const response = data as WSAIResponse;
          const aiMessage: AIMessage = {
            id: response.data.message_id,
            role: 'assistant',
            content: response.data.message,
            credits_used: response.data.credits_used,
            structured_data: response.data.structured_data,
            insights: response.data.insights,
            created_at: response.data.created_at,
          };
          setMessages(prev => [...prev, aiMessage]);
          setIsTyping(false);
          
          // Handle fallback response
          if (response.data.is_fallback) {
            toast.error('AI service temporarily unavailable. Please try again later.');
          }
          break;
          
        case 'assistant_typing':
          const typingData = data as WSTypingIndicator;
          setIsTyping(typingData.typing);
          break;
          
        case 'error':
          const errorData = data as WSError;
          setError(errorData.message);
          setIsTyping(false);
          
          if (errorData.error_code === 'INSUFFICIENT_CREDITS') {
            toast.error('Insufficient credits. Please purchase more credits to continue.');
          } else if (errorData.error_code === 'RATE_LIMITED') {
            toast.error('You are sending messages too quickly. Please slow down.');
          } else {
            toast.error(errorData.message || 'An error occurred');
          }
          break;
          
        case 'new_message':
          // Handle messages from other users in the conversation
          if (data.message && data.message.role) {
            setMessages(prev => [...prev, data.message]);
          }
          break;
          
        case 'user_typing':
          // Handle typing indicators from other users
          // Can be implemented if needed for multi-user conversations
          break;
      }
    } catch (err) {
      setError('Failed to process message');
      toast.error('Communication error occurred');
    }
  }, []);

  // Initialize WebSocket connection
  const {
    isConnected,
    isConnecting,
    reconnectCount,
    lastError,
    sendMessage: sendWebSocketMessage,
    connect,
    disconnect,
  } = useSecureWebSocket({
    url: wsUrl || '',
    onMessage: handleWebSocketMessage,
    onOpen: () => {
      setError(null);
    },
    onClose: () => {
      setIsTyping(false);
    },
    onError: () => {
      setError('Connection error occurred');
    },
  });

  // Load existing messages
  const loadMessages = useCallback(async () => {
    if (!conversationId) return;

    setLoading(true);
    setError(null);
    
    try {
      const data = await aiInsightsService.getConversationMessages(conversationId);
      setMessages(data);
    } catch (err) {
      setError('Failed to load messages');
      toast.error('Failed to load conversation messages');
    } finally {
      setLoading(false);
    }
  }, [conversationId]);

  // Send message
  const sendMessage = useCallback(async (content: string, convId?: string) => {
    const targetConvId = convId || conversationId;
    
    if (!targetConvId) {
      toast.error('No conversation selected');
      return;
    }

    if (!isConnected && wsUrl) {
      toast.error('Connection not established. Trying to reconnect...');
      connect();
      return;
    }

    // Add user message optimistically
    const userMessage: AIMessage = {
      id: `temp-${Date.now()}`,
      role: 'user',
      content,
      created_at: new Date().toISOString(),
    };
    
    setMessages(prev => [...prev, userMessage]);
    setError(null);
    
    // Send via WebSocket
    const sent = sendWebSocketMessage({
      type: 'message',
      message: content,
    });
    
    if (!sent) {
      // Remove optimistic message if send failed
      setMessages(prev => prev.filter(m => m.id !== userMessage.id));
      toast.error('Failed to send message');
    }
  }, [conversationId, isConnected, wsUrl, connect, sendWebSocketMessage]);

  // Create new conversation
  const createConversation = useCallback(async () => {
    try {
      const conversation = await aiInsightsService.createConversation({
        title: 'Nova Conversa',
      });
      return conversation;
    } catch (err) {
      toast.error('Failed to create conversation');
      return null;
    }
  }, []);

  // Send typing indicator
  const sendTypingIndicator = useCallback((typing: boolean) => {
    if (isConnected) {
      sendWebSocketMessage({
        type: 'typing',
        typing,
      });
    }
  }, [isConnected, sendWebSocketMessage]);

  // Send read receipt
  const markMessageRead = useCallback((messageId: string) => {
    if (isConnected) {
      sendWebSocketMessage({
        type: 'read_receipt',
        message_id: messageId,
      });
    }
  }, [isConnected, sendWebSocketMessage]);

  // Effects
  useEffect(() => {
    if (conversationId) {
      loadMessages();
    } else {
      setMessages([]);
    }
  }, [conversationId, loadMessages]);

  // Clean up on unmount
  useEffect(() => {
    return () => {
      disconnect();
    };
  }, [disconnect]);

  return {
    messages,
    loading,
    isTyping,
    error,
    connected: isConnected,
    connecting: isConnecting,
    reconnectCount,
    connectionError: lastError,
    sendMessage,
    createConversation,
    sendTypingIndicator,
    markMessageRead,
    reconnect: connect,
  };
}