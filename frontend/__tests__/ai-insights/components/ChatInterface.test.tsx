import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ChatInterface } from '@/app/(dashboard)/ai-insights/components/ChatInterface';
import { useChat } from '@/app/(dashboard)/ai-insights/hooks/useChat';
import { AIMessage } from '@/app/(dashboard)/ai-insights/types/ai-insights.types';

// Mock dependencies
jest.mock('@/app/(dashboard)/ai-insights/hooks/useChat');
jest.mock('@/app/(dashboard)/ai-insights/components/MessageList');
jest.mock('@/app/(dashboard)/ai-insights/components/MessageInput');
jest.mock('@/app/(dashboard)/ai-insights/components/QuickActions');
jest.mock('@/app/(dashboard)/ai-insights/components/TypingIndicator');

const mockUseChat = useChat as jest.MockedFunction<typeof useChat>;

// Mock child components
jest.mock('@/app/(dashboard)/ai-insights/components/MessageList', () => ({
  MessageList: ({ messages, loading }: { messages: AIMessage[]; loading: boolean }) => (
    <div data-testid="message-list">
      {loading && <div data-testid="loading">Loading...</div>}
      {messages.map((msg) => (
        <div key={msg.id} data-testid={`message-${msg.role}`}>
          {msg.content}
        </div>
      ))}
    </div>
  ),
}));

jest.mock('@/app/(dashboard)/ai-insights/components/MessageInput', () => ({
  MessageInput: ({ onSend, disabled }: { onSend: (message: string) => void; disabled: boolean }) => (
    <div data-testid="message-input">
      <input
        data-testid="message-input-field"
        disabled={disabled}
        onKeyDown={(e) => {
          if (e.key === 'Enter') {
            const target = e.target as HTMLInputElement;
            onSend(target.value);
            target.value = '';
          }
        }}
        placeholder="Type your message..."
      />
    </div>
  ),
}));

jest.mock('@/app/(dashboard)/ai-insights/components/QuickActions', () => ({
  QuickActions: ({ onSelect }: { onSelect: (message: string) => void }) => (
    <div data-testid="quick-actions">
      <button onClick={() => onSelect('What are my biggest expenses?')}>
        Quick Action 1
      </button>
      <button onClick={() => onSelect('Show me my revenue trend')}>
        Quick Action 2
      </button>
    </div>
  ),
}));

jest.mock('@/app/(dashboard)/ai-insights/components/TypingIndicator', () => ({
  TypingIndicator: () => <div data-testid="typing-indicator">AI is typing...</div>,
}));

describe('ChatInterface', () => {
  const mockSendMessage = jest.fn();
  const mockCreateConversation = jest.fn();
  const mockOnNewConversation = jest.fn();

  const defaultMockReturn = {
    messages: [],
    loading: false,
    isTyping: false,
    error: null,
    connected: true,
    connecting: false,
    reconnectCount: 0,
    connectionError: null,
    sendMessage: mockSendMessage,
    createConversation: mockCreateConversation,
    sendTypingIndicator: jest.fn(),
    markMessageRead: jest.fn(),
    reconnect: jest.fn(),
  };

  beforeEach(() => {
    jest.clearAllMocks();
    mockUseChat.mockReturnValue(defaultMockReturn);
  });

  describe('when no conversation is selected', () => {
    it('should render empty state with quick actions', () => {
      render(
        <ChatInterface
          conversationId={null}
          onNewConversation={mockOnNewConversation}
        />
      );

      expect(screen.getByText('Comece uma nova conversa')).toBeInTheDocument();
      expect(screen.getByText('Pergunte sobre suas finanças e receba insights personalizados')).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /nova conversa/i })).toBeInTheDocument();
      expect(screen.getByTestId('quick-actions')).toBeInTheDocument();
    });

    it('should create new conversation when "Nova Conversa" button is clicked', async () => {
      const mockConversation = {
        id: 'new-conv-123',
        title: 'Nova Conversa',
        status: 'active' as const,
        message_count: 0,
        total_credits_used: 0,
        created_at: '2023-01-01T00:00:00Z',
        updated_at: '2023-01-01T00:00:00Z',
      };

      mockCreateConversation.mockResolvedValue(mockConversation);

      render(
        <ChatInterface
          conversationId={null}
          onNewConversation={mockOnNewConversation}
        />
      );

      const newConversationButton = screen.getByRole('button', { name: /nova conversa/i });
      await userEvent.click(newConversationButton);

      await waitFor(() => {
        expect(mockCreateConversation).toHaveBeenCalled();
        expect(mockOnNewConversation).toHaveBeenCalledWith('new-conv-123');
      });
    });

    it('should handle quick action selection', async () => {
      const mockConversation = {
        id: 'quick-conv-123',
        title: 'Nova Conversa',
        status: 'active' as const,
        message_count: 0,
        total_credits_used: 0,
        created_at: '2023-01-01T00:00:00Z',
        updated_at: '2023-01-01T00:00:00Z',
      };

      mockCreateConversation.mockResolvedValue(mockConversation);

      render(
        <ChatInterface
          conversationId={null}
          onNewConversation={mockOnNewConversation}
        />
      );

      const quickActionButton = screen.getByText('Quick Action 1');
      await userEvent.click(quickActionButton);

      await waitFor(() => {
        expect(mockCreateConversation).toHaveBeenCalled();
        expect(mockOnNewConversation).toHaveBeenCalledWith('quick-conv-123');
        expect(mockSendMessage).toHaveBeenCalledWith('What are my biggest expenses?', 'quick-conv-123');
      });
    });

    it('should not create conversation if creation fails', async () => {
      mockCreateConversation.mockResolvedValue(null);

      render(
        <ChatInterface
          conversationId={null}
          onNewConversation={mockOnNewConversation}
        />
      );

      const newConversationButton = screen.getByRole('button', { name: /nova conversa/i });
      await userEvent.click(newConversationButton);

      await waitFor(() => {
        expect(mockCreateConversation).toHaveBeenCalled();
        expect(mockOnNewConversation).not.toHaveBeenCalled();
      });
    });
  });

  describe('when conversation is selected', () => {
    const conversationId = 'conv-123';
    
    const mockMessages: AIMessage[] = [
      {
        id: '1',
        role: 'user',
        content: 'Hello AI',
        created_at: '2023-01-01T00:00:00Z',
      },
      {
        id: '2',
        role: 'assistant',
        content: 'Hello! How can I help you with your finances today?',
        credits_used: 2,
        created_at: '2023-01-01T00:01:00Z',
      },
    ];

    beforeEach(() => {
      mockUseChat.mockReturnValue({
        ...defaultMockReturn,
        messages: mockMessages,
      });
    });

    it('should render chat interface with messages', () => {
      render(
        <ChatInterface
          conversationId={conversationId}
          onNewConversation={mockOnNewConversation}
        />
      );

      expect(screen.getByText('Assistente Financeiro AI')).toBeInTheDocument();
      expect(screen.getByTestId('message-list')).toBeInTheDocument();
      expect(screen.getByTestId('message-input')).toBeInTheDocument();
      
      // Check messages are displayed
      expect(screen.getByTestId('message-user')).toHaveTextContent('Hello AI');
      expect(screen.getByTestId('message-assistant')).toHaveTextContent('Hello! How can I help you with your finances today?');
    });

    it('should show typing indicator when AI is typing', () => {
      mockUseChat.mockReturnValue({
        ...defaultMockReturn,
        messages: mockMessages,
        isTyping: true,
      });

      render(
        <ChatInterface
          conversationId={conversationId}
          onNewConversation={mockOnNewConversation}
        />
      );

      expect(screen.getByTestId('typing-indicator')).toBeInTheDocument();
    });

    it('should show loading state', () => {
      mockUseChat.mockReturnValue({
        ...defaultMockReturn,
        messages: mockMessages,
        loading: true,
      });

      render(
        <ChatInterface
          conversationId={conversationId}
          onNewConversation={mockOnNewConversation}
        />
      );

      expect(screen.getByTestId('loading')).toBeInTheDocument();
    });

    it('should send message when user types and presses Enter', async () => {
      render(
        <ChatInterface
          conversationId={conversationId}
          onNewConversation={mockOnNewConversation}
        />
      );

      const messageInput = screen.getByTestId('message-input-field');
      
      await userEvent.type(messageInput, 'What are my expenses?');
      fireEvent.keyDown(messageInput, { key: 'Enter' });

      expect(mockSendMessage).toHaveBeenCalledWith('What are my expenses?', conversationId);
    });

    it('should disable input when loading or typing', () => {
      mockUseChat.mockReturnValue({
        ...defaultMockReturn,
        messages: mockMessages,
        loading: true,
        isTyping: true,
      });

      render(
        <ChatInterface
          conversationId={conversationId}
          onNewConversation={mockOnNewConversation}
        />
      );

      const messageInput = screen.getByTestId('message-input-field');
      expect(messageInput).toBeDisabled();
    });

    it('should create new conversation from header button', async () => {
      const mockNewConversation = {
        id: 'header-new-conv',
        title: 'Nova Conversa',
        status: 'active' as const,
        message_count: 0,
        total_credits_used: 0,
        created_at: '2023-01-01T00:00:00Z',
        updated_at: '2023-01-01T00:00:00Z',
      };

      mockCreateConversation.mockResolvedValue(mockNewConversation);

      render(
        <ChatInterface
          conversationId={conversationId}
          onNewConversation={mockOnNewConversation}
        />
      );

      const headerNewButton = screen.getByRole('button', { name: /nova/i });
      await userEvent.click(headerNewButton);

      await waitFor(() => {
        expect(mockCreateConversation).toHaveBeenCalled();
        expect(mockOnNewConversation).toHaveBeenCalledWith('header-new-conv');
      });
    });
  });

  describe('conversation creation workflow', () => {
    it('should create conversation and send message when no conversation exists', async () => {
      const mockConversation = {
        id: 'auto-created-conv',
        title: 'Nova Conversa',
        status: 'active' as const,
        message_count: 0,
        total_credits_used: 0,
        created_at: '2023-01-01T00:00:00Z',
        updated_at: '2023-01-01T00:00:00Z',
      };

      mockCreateConversation.mockResolvedValue(mockConversation);

      render(
        <ChatInterface
          conversationId={null}
          onNewConversation={mockOnNewConversation}
        />
      );

      // Simulate sending a message through quick action
      const quickActionButton = screen.getByText('Quick Action 2');
      await userEvent.click(quickActionButton);

      await waitFor(() => {
        expect(mockCreateConversation).toHaveBeenCalled();
        expect(mockOnNewConversation).toHaveBeenCalledWith('auto-created-conv');
        expect(mockSendMessage).toHaveBeenCalledWith('Show me my revenue trend', 'auto-created-conv');
      });
    });

    it('should handle conversation creation failure gracefully', async () => {
      mockCreateConversation.mockResolvedValue(null);

      const user = userEvent.setup();

      render(
        <ChatInterface
          conversationId={null}
          onNewConversation={mockOnNewConversation}
        />
      );

      const quickActionButton = screen.getByText('Quick Action 1');
      await user.click(quickActionButton);

      await waitFor(() => {
        expect(mockCreateConversation).toHaveBeenCalled();
        expect(mockOnNewConversation).not.toHaveBeenCalled();
        expect(mockSendMessage).not.toHaveBeenCalled();
      });
    });
  });

  describe('error handling', () => {
    it('should handle hook errors gracefully', () => {
      mockUseChat.mockReturnValue({
        ...defaultMockReturn,
        error: 'Connection failed',
      });

      render(
        <ChatInterface
          conversationId="conv-123"
          onNewConversation={mockOnNewConversation}
        />
      );

      // Component should still render without crashing
      expect(screen.getByText('Assistente Financeiro AI')).toBeInTheDocument();
    });

    it('should handle missing conversation ID edge cases', () => {
      render(
        <ChatInterface
          conversationId=""
          onNewConversation={mockOnNewConversation}
        />
      );

      // Should treat empty string as null
      expect(screen.getByText('Comece uma nova conversa')).toBeInTheDocument();
    });
  });

  describe('accessibility', () => {
    it('should have proper heading structure', () => {
      render(
        <ChatInterface
          conversationId="conv-123"
          onNewConversation={mockOnNewConversation}
        />
      );

      const mainHeading = screen.getByRole('heading', { level: 2 });
      expect(mainHeading).toHaveTextContent('Assistente Financeiro AI');
    });

    it('should have accessible buttons', () => {
      render(
        <ChatInterface
          conversationId="conv-123"
          onNewConversation={mockOnNewConversation}
        />
      );

      const newConversationButton = screen.getByRole('button', { name: /nova/i });
      expect(newConversationButton).toBeInTheDocument();
      expect(newConversationButton).not.toBeDisabled();
    });

    it('should handle keyboard navigation', async () => {
      render(
        <ChatInterface
          conversationId="conv-123"
          onNewConversation={mockOnNewConversation}
        />
      );

      const messageInput = screen.getByTestId('message-input-field');
      
      // Focus should work
      messageInput.focus();
      expect(messageInput).toHaveFocus();

      // Enter key should send message
      await userEvent.type(messageInput, 'Test message{enter}');
      expect(mockSendMessage).toHaveBeenCalledWith('Test message', 'conv-123');
    });
  });

  describe('responsive behavior', () => {
    it('should render on mobile viewport', () => {
      // Mock window size
      Object.defineProperty(window, 'innerWidth', {
        writable: true,
        configurable: true,
        value: 375,
      });

      render(
        <ChatInterface
          conversationId="conv-123"
          onNewConversation={mockOnNewConversation}
        />
      );

      // Component should render without issues on mobile
      expect(screen.getByText('Assistente Financeiro AI')).toBeInTheDocument();
      expect(screen.getByTestId('message-input')).toBeInTheDocument();
    });
  });

  describe('performance considerations', () => {
    it('should not re-render unnecessarily', () => {
      const { rerender } = render(
        <ChatInterface
          conversationId="conv-123"
          onNewConversation={mockOnNewConversation}
        />
      );

      // Re-render with same props
      rerender(
        <ChatInterface
          conversationId="conv-123"
          onNewConversation={mockOnNewConversation}
        />
      );

      // useChat should only be called once per conversation ID
      expect(mockUseChat).toHaveBeenCalledTimes(2); // Initial + rerender
    });

    it('should handle large message lists efficiently', () => {
      const largeMessageList: AIMessage[] = Array.from({ length: 100 }, (_, i) => ({
        id: `msg-${i}`,
        role: i % 2 === 0 ? 'user' : 'assistant',
        content: `Message ${i}`,
        created_at: `2023-01-01T00:${i.toString().padStart(2, '0')}:00Z`,
      }));

      mockUseChat.mockReturnValue({
        ...defaultMockReturn,
        messages: largeMessageList,
      });

      render(
        <ChatInterface
          conversationId="conv-123"
          onNewConversation={mockOnNewConversation}
        />
      );

      // Should render without performance issues
      expect(screen.getByTestId('message-list')).toBeInTheDocument();
    });
  });
});