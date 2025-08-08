import { renderHook, act, waitFor } from '@testing-library/react';
import { useChat } from '@/app/(dashboard)/ai-insights/hooks/useChat';
import { aiInsightsService } from '@/app/(dashboard)/ai-insights/services/ai-insights.service';
import { useAuthStore } from '@/store/auth-store';
import toast from 'react-hot-toast';

// Mock dependencies
jest.mock('@/app/(dashboard)/ai-insights/services/ai-insights.service');
jest.mock('@/app/(dashboard)/ai-insights/hooks/useSecureWebSocket');
jest.mock('@/store/auth-store');
jest.mock('react-hot-toast');

const mockAiInsightsService = aiInsightsService as jest.Mocked<typeof aiInsightsService>;
const mockUseAuthStore = useAuthStore as jest.MockedFunction<typeof useAuthStore>;
const mockToast = toast as jest.Mocked<typeof toast>;

// Import and mock useSecureWebSocket
import { useSecureWebSocket } from '@/app/(dashboard)/ai-insights/hooks/useSecureWebSocket';
const mockUseSecureWebSocket = useSecureWebSocket as jest.MockedFunction<typeof useSecureWebSocket>;

describe('useChat', () => {
  const mockUser = {
    id: '1',
    email: 'test@example.com',
    name: 'Test User',
  };

  const mockWebSocketReturn = {
    isConnected: true,
    isConnecting: false,
    reconnectCount: 0,
    lastError: null,
    sendMessage: jest.fn(),
    connect: jest.fn(),
    disconnect: jest.fn(),
  };

  beforeEach(() => {
    jest.clearAllMocks();
    
    mockUseAuthStore.mockReturnValue({ user: mockUser });
    mockUseSecureWebSocket.mockReturnValue(mockWebSocketReturn);
    
    // Mock environment variable
    process.env.NEXT_PUBLIC_WS_URL = 'ws://localhost:8000';
  });

  afterEach(() => {
    delete process.env.NEXT_PUBLIC_WS_URL;
  });

  describe('initialization', () => {
    it('should initialize with default state', () => {
      const { result } = renderHook(() => useChat('conv-123'));

      expect(result.current.messages).toEqual([]);
      expect(result.current.loading).toBe(false);
      expect(result.current.isTyping).toBe(false);
      expect(result.current.error).toBe(null);
      expect(result.current.connected).toBe(true);
      expect(result.current.connecting).toBe(false);
      expect(result.current.reconnectCount).toBe(0);
    });

    it('should construct correct WebSocket URL', () => {
      const conversationId = 'conv-123';
      renderHook(() => useChat(conversationId));

      expect(mockUseSecureWebSocket).toHaveBeenCalledWith({
        url: `ws://localhost:8000/ws/ai-chat/${conversationId}/`,
        onMessage: expect.any(Function),
        onOpen: expect.any(Function),
        onClose: expect.any(Function),
        onError: expect.any(Function),
      });
    });

    it('should handle null conversation ID', () => {
      renderHook(() => useChat(null));

      expect(mockUseSecureWebSocket).toHaveBeenCalledWith({
        url: '',
        onMessage: expect.any(Function),
        onOpen: expect.any(Function),
        onClose: expect.any(Function),
        onError: expect.any(Function),
      });
    });
  });

  describe('message loading', () => {
    it('should load messages successfully', async () => {
      const mockMessages = [
        {
          id: '1',
          role: 'user' as const,
          content: 'Hello',
          created_at: '2023-01-01T00:00:00Z',
        },
        {
          id: '2',
          role: 'assistant' as const,
          content: 'Hi there!',
          created_at: '2023-01-01T00:01:00Z',
        },
      ];

      mockAiInsightsService.getConversationMessages.mockResolvedValue(mockMessages);

      const { result } = renderHook(() => useChat('conv-123'));

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      expect(result.current.messages).toEqual(mockMessages);
      expect(mockAiInsightsService.getConversationMessages).toHaveBeenCalledWith('conv-123');
    });

    it('should handle message loading error', async () => {
      mockAiInsightsService.getConversationMessages.mockRejectedValue(
        new Error('Failed to load messages')
      );

      const { result } = renderHook(() => useChat('conv-123'));

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      expect(result.current.error).toBe('Failed to load messages');
      expect(mockToast.error).toHaveBeenCalledWith('Failed to load conversation messages');
    });

    it('should not load messages when conversation ID is null', () => {
      renderHook(() => useChat(null));

      expect(mockAiInsightsService.getConversationMessages).not.toHaveBeenCalled();
    });
  });

  describe('WebSocket message handling', () => {
    let messageHandler: (data: any) => void;

    beforeEach(() => {
      const { result } = renderHook(() => useChat('conv-123'));
      const wsCall = mockUseSecureWebSocket.mock.calls[0][0];
      messageHandler = wsCall.onMessage;
    });

    it('should handle connection established message', () => {
      const connectionMessage = {
        type: 'connection_established',
        message: 'Connected successfully',
      };

      act(() => {
        messageHandler(connectionMessage);
      });

      // Should not cause any state changes for connection messages
    });

    it('should handle AI response message', () => {
      const { result } = renderHook(() => useChat('conv-123'));

      const aiResponse = {
        type: 'ai_response',
        data: {
          message_id: 'msg-123',
          message: 'AI response content',
          credits_used: 3,
          structured_data: { charts: [] },
          insights: [],
          created_at: '2023-01-01T00:00:00Z',
        },
      };

      act(() => {
        const wsCall = mockUseSecureWebSocket.mock.calls[0][0];
        wsCall.onMessage(aiResponse);
      });

      expect(result.current.messages).toHaveLength(1);
      expect(result.current.messages[0]).toEqual({
        id: 'msg-123',
        role: 'assistant',
        content: 'AI response content',
        credits_used: 3,
        structured_data: { charts: [] },
        insights: [],
        created_at: '2023-01-01T00:00:00Z',
      });
      expect(result.current.isTyping).toBe(false);
    });

    it('should handle AI response with fallback', () => {
      const { result } = renderHook(() => useChat('conv-123'));

      const fallbackResponse = {
        type: 'ai_response',
        data: {
          message_id: 'msg-fallback',
          message: 'Service temporarily unavailable',
          credits_used: 0,
          is_fallback: true,
          created_at: '2023-01-01T00:00:00Z',
        },
      };

      act(() => {
        const wsCall = mockUseSecureWebSocket.mock.calls[0][0];
        wsCall.onMessage(fallbackResponse);
      });

      expect(mockToast.error).toHaveBeenCalledWith(
        'AI service temporarily unavailable. Please try again later.'
      );
      expect(result.current.messages).toHaveLength(1);
    });

    it('should handle typing indicator', () => {
      const { result } = renderHook(() => useChat('conv-123'));

      const typingMessage = {
        type: 'assistant_typing',
        typing: true,
      };

      act(() => {
        const wsCall = mockUseSecureWebSocket.mock.calls[0][0];
        wsCall.onMessage(typingMessage);
      });

      expect(result.current.isTyping).toBe(true);

      act(() => {
        const wsCall = mockUseSecureWebSocket.mock.calls[0][0];
        wsCall.onMessage({ type: 'assistant_typing', typing: false });
      });

      expect(result.current.isTyping).toBe(false);
    });

    it('should handle error messages', () => {
      const { result } = renderHook(() => useChat('conv-123'));

      const errorMessage = {
        type: 'error',
        error_code: 'INSUFFICIENT_CREDITS',
        message: 'Not enough credits',
      };

      act(() => {
        const wsCall = mockUseSecureWebSocket.mock.calls[0][0];
        wsCall.onMessage(errorMessage);
      });

      expect(result.current.error).toBe('Not enough credits');
      expect(result.current.isTyping).toBe(false);
      expect(mockToast.error).toHaveBeenCalledWith(
        'Insufficient credits. Please purchase more credits to continue.'
      );
    });

    it('should handle rate limit errors', () => {
      const { result } = renderHook(() => useChat('conv-123'));

      const rateLimitError = {
        type: 'error',
        error_code: 'RATE_LIMITED',
        message: 'Too many requests',
      };

      act(() => {
        const wsCall = mockUseSecureWebSocket.mock.calls[0][0];
        wsCall.onMessage(rateLimitError);
      });

      expect(mockToast.error).toHaveBeenCalledWith(
        'You are sending messages too quickly. Please slow down.'
      );
    });

    it('should handle generic errors', () => {
      const { result } = renderHook(() => useChat('conv-123'));

      const genericError = {
        type: 'error',
        message: 'Something went wrong',
      };

      act(() => {
        const wsCall = mockUseSecureWebSocket.mock.calls[0][0];
        wsCall.onMessage(genericError);
      });

      expect(mockToast.error).toHaveBeenCalledWith('Something went wrong');
    });

    it('should handle invalid JSON gracefully', () => {
      const { result } = renderHook(() => useChat('conv-123'));

      act(() => {
        const wsCall = mockUseSecureWebSocket.mock.calls[0][0];
        wsCall.onMessage({ type: 'invalid', invalidData: 'test' });
      });

      expect(result.current.error).toBe('Failed to process message');
      expect(mockToast.error).toHaveBeenCalledWith('Communication error occurred');
    });
  });

  describe('sending messages', () => {
    it('should send message successfully when connected', async () => {
      mockWebSocketReturn.sendMessage.mockReturnValue(true);

      const { result } = renderHook(() => useChat('conv-123'));

      act(() => {
        result.current.sendMessage('Hello AI');
      });

      // Should add optimistic user message
      expect(result.current.messages).toHaveLength(1);
      expect(result.current.messages[0]).toMatchObject({
        role: 'user',
        content: 'Hello AI',
      });

      // Should send via WebSocket
      expect(mockWebSocketReturn.sendMessage).toHaveBeenCalledWith({
        type: 'message',
        message: 'Hello AI',
      });
    });

    it('should handle send failure', async () => {
      mockWebSocketReturn.sendMessage.mockReturnValue(false);

      const { result } = renderHook(() => useChat('conv-123'));

      act(() => {
        result.current.sendMessage('Hello AI');
      });

      // Should remove optimistic message on failure
      await waitFor(() => {
        expect(result.current.messages).toHaveLength(0);
      });

      expect(mockToast.error).toHaveBeenCalledWith('Failed to send message');
    });

    it('should handle no conversation ID', async () => {
      const { result } = renderHook(() => useChat(null));

      act(() => {
        result.current.sendMessage('Hello AI');
      });

      expect(mockToast.error).toHaveBeenCalledWith('No conversation selected');
    });

    it('should handle disconnected state', async () => {
      mockUseSecureWebSocket.mockReturnValue({
        ...mockWebSocketReturn,
        isConnected: false,
      });

      const { result } = renderHook(() => useChat('conv-123'));

      act(() => {
        result.current.sendMessage('Hello AI');
      });

      expect(mockToast.error).toHaveBeenCalledWith(
        'Connection not established. Trying to reconnect...'
      );
      expect(mockWebSocketReturn.connect).toHaveBeenCalled();
    });

    it('should send message to specific conversation', async () => {
      mockWebSocketReturn.sendMessage.mockReturnValue(true);

      const { result } = renderHook(() => useChat('conv-123'));

      act(() => {
        result.current.sendMessage('Hello AI', 'conv-456');
      });

      expect(mockWebSocketReturn.sendMessage).toHaveBeenCalledWith({
        type: 'message',
        message: 'Hello AI',
      });
    });
  });

  describe('conversation management', () => {
    it('should create new conversation', async () => {
      const mockConversation = {
        id: 'new-conv-123',
        title: 'Nova Conversa',
        status: 'active' as const,
        message_count: 0,
        total_credits_used: 0,
        created_at: '2023-01-01T00:00:00Z',
        updated_at: '2023-01-01T00:00:00Z',
      };

      mockAiInsightsService.createConversation.mockResolvedValue(mockConversation);

      const { result } = renderHook(() => useChat('conv-123'));

      let createdConversation: any;
      await act(async () => {
        createdConversation = await result.current.createConversation();
      });

      expect(createdConversation).toEqual(mockConversation);
      expect(mockAiInsightsService.createConversation).toHaveBeenCalledWith({
        title: 'Nova Conversa',
      });
    });

    it('should handle conversation creation error', async () => {
      mockAiInsightsService.createConversation.mockRejectedValue(
        new Error('Failed to create conversation')
      );

      const { result } = renderHook(() => useChat('conv-123'));

      let createdConversation: any;
      await act(async () => {
        createdConversation = await result.current.createConversation();
      });

      expect(createdConversation).toBe(null);
      expect(mockToast.error).toHaveBeenCalledWith('Failed to create conversation');
    });
  });

  describe('typing indicators', () => {
    it('should send typing indicator', () => {
      const { result } = renderHook(() => useChat('conv-123'));

      act(() => {
        result.current.sendTypingIndicator(true);
      });

      expect(mockWebSocketReturn.sendMessage).toHaveBeenCalledWith({
        type: 'typing',
        typing: true,
      });
    });

    it('should not send typing indicator when disconnected', () => {
      mockUseSecureWebSocket.mockReturnValue({
        ...mockWebSocketReturn,
        isConnected: false,
      });

      const { result } = renderHook(() => useChat('conv-123'));

      act(() => {
        result.current.sendTypingIndicator(true);
      });

      expect(mockWebSocketReturn.sendMessage).not.toHaveBeenCalled();
    });
  });

  describe('read receipts', () => {
    it('should mark message as read', () => {
      const { result } = renderHook(() => useChat('conv-123'));

      act(() => {
        result.current.markMessageRead('msg-123');
      });

      expect(mockWebSocketReturn.sendMessage).toHaveBeenCalledWith({
        type: 'read_receipt',
        message_id: 'msg-123',
      });
    });
  });

  describe('connection management', () => {
    it('should disconnect on unmount', () => {
      const { unmount } = renderHook(() => useChat('conv-123'));

      unmount();

      expect(mockWebSocketReturn.disconnect).toHaveBeenCalled();
    });

    it('should reconnect on demand', () => {
      const { result } = renderHook(() => useChat('conv-123'));

      act(() => {
        result.current.reconnect();
      });

      expect(mockWebSocketReturn.connect).toHaveBeenCalled();
    });
  });

  describe('error handling', () => {
    it('should clear error on successful connection', () => {
      const { result } = renderHook(() => useChat('conv-123'));

      // Simulate error
      act(() => {
        const wsCall = mockUseSecureWebSocket.mock.calls[0][0];
        wsCall.onError();
      });

      expect(result.current.error).toBe('Connection error occurred');

      // Simulate successful connection
      act(() => {
        const wsCall = mockUseSecureWebSocket.mock.calls[0][0];
        wsCall.onOpen();
      });

      expect(result.current.error).toBe(null);
    });

    it('should handle connection close', () => {
      const { result } = renderHook(() => useChat('conv-123'));

      act(() => {
        const wsCall = mockUseSecureWebSocket.mock.calls[0][0];
        wsCall.onClose();
      });

      expect(result.current.isTyping).toBe(false);
    });
  });
});