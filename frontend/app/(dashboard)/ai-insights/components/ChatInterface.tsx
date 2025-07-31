'use client';

import { useState, useEffect, useRef } from 'react';
import { MessageList } from './MessageList';
import { MessageInput } from './MessageInput';
import { QuickActions } from './QuickActions';
import { TypingIndicator } from './TypingIndicator';
import { useChat } from '../hooks/useChat';
import { Button } from '@/components/ui/button';
import { PlusIcon } from '@heroicons/react/24/outline';

interface ChatInterfaceProps {
  conversationId: string | null;
  onNewConversation: (id: string) => void;
}

export function ChatInterface({ conversationId, onNewConversation }: ChatInterfaceProps) {
  const {
    messages,
    loading,
    isTyping,
    sendMessage,
    createConversation
  } = useChat(conversationId);

  const handleNewConversation = async () => {
    const newConversation = await createConversation();
    if (newConversation) {
      onNewConversation(newConversation.id);
    }
  };

  const handleSendMessage = async (message: string) => {
    if (!conversationId) {
      // Criar nova conversa se não existir
      const newConv = await createConversation();
      if (newConv) {
        onNewConversation(newConv.id);
        await sendMessage(message, newConv.id);
      }
    } else {
      await sendMessage(message, conversationId);
    }
  };

  if (!conversationId) {
    return (
      <div className="flex-1 flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <h3 className="text-lg font-semibold text-gray-900 mb-2">
            Comece uma nova conversa
          </h3>
          <p className="text-gray-600 mb-4">
            Pergunte sobre suas finanças e receba insights personalizados
          </p>
          <Button onClick={handleNewConversation}>
            <PlusIcon className="h-5 w-5 mr-2" />
            Nova Conversa
          </Button>
          
          <QuickActions onSelect={handleSendMessage} />
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 flex flex-col bg-white rounded-lg shadow-sm border">
      {/* Header */}
      <div className="border-b px-6 py-4 flex items-center justify-between">
        <h2 className="text-lg font-semibold">Assistente Financeiro AI</h2>
        <Button 
          variant="outline" 
          size="sm"
          onClick={handleNewConversation}
        >
          <PlusIcon className="h-4 w-4 mr-1" />
          Nova
        </Button>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-hidden">
        <MessageList messages={messages} loading={loading} />
        {isTyping && <TypingIndicator />}
      </div>

      {/* Input */}
      <div className="border-t p-4">
        <MessageInput 
          onSend={handleSendMessage}
          disabled={loading || isTyping}
        />
      </div>
    </div>
  );
}