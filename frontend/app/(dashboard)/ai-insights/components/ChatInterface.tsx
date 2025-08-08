'use client';

import { useState, useEffect, useRef } from 'react';
import { MessageList } from './MessageList';
import { MessageInput } from './MessageInput';
import { QuickActions } from './QuickActions';
import { TypingIndicator } from './TypingIndicator';
import { useChat } from '../hooks/useChat';
import { Button } from '@/components/ui/button';
import { PlusIcon } from '@heroicons/react/24/outline';
import { testId, TEST_IDS } from '@/utils/test-helpers';

interface ChatInterfaceProps {
  conversationId: string | null;
  onNewConversation: (id: string) => void;
  createConversation?: (title?: string) => Promise<any>;
}

export function ChatInterface({ conversationId, onNewConversation, createConversation: createConversationProp }: ChatInterfaceProps) {
  const {
    messages,
    loading,
    isTyping,
    sendMessage,
    createConversation: createConversationHook
  } = useChat(conversationId);

  // Usar createConversation passado como prop ou do hook
  const createConversationFn = createConversationProp || createConversationHook;

  const handleNewConversation = async () => {
    const newConversation = await createConversationFn();
    if (newConversation) {
      onNewConversation(newConversation.id);
    }
  };

  const handleSendMessage = async (message: string) => {
    if (!conversationId) {
      // Criar nova conversa se não existir
      const newConv = await createConversationFn();
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
      <div className="flex-1 flex items-center justify-center bg-gradient-subtle rounded-xl">
        <div className="text-center p-8">
          <div className="mb-4">
            <h3 className="text-2xl font-bold mb-2 text-white">
              Assistente Financeiro IA
            </h3>
          </div>
          <p className="text-muted-foreground mb-6 max-w-md">
            Pergunte sobre suas finanças e receba insights personalizados com o poder da inteligência artificial
          </p>
          <Button 
            onClick={handleNewConversation} 
            className="btn-gradient text-white shadow-md hover-lift transition-all duration-300"
            size="lg"
            {...testId(TEST_IDS.aiInsights.newConversationButton)}
          >
            <PlusIcon className="h-5 w-5 mr-2" />
            Nova Conversa
          </Button>
          
          <QuickActions onSelect={handleSendMessage} />
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 flex flex-col glass rounded-xl hover-lift transition-all duration-300" {...testId(TEST_IDS.aiInsights.chatInterface)}>
      {/* Header */}
      <div className="border-b border-border px-6 py-4 flex items-center justify-between bg-muted/50 rounded-t-xl">
        <h2 className="text-lg font-semibold text-white">
          Assistente Financeiro AI
        </h2>
        <Button 
          variant="outline"
          size="sm"
          onClick={handleNewConversation}
          className="border-pink-200 text-pink-700 hover:bg-gradient-to-r hover:from-pink-500 hover:to-purple-600 hover:text-white hover:border-transparent transition-all duration-300 hover:shadow-md"
          {...testId(TEST_IDS.aiInsights.newConversationButtonSmall)}
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
      <div className="border-t border-white/20 p-4 bg-gradient-to-r from-pink-50/30 to-purple-50/30 rounded-b-xl">
        <MessageInput 
          onSend={handleSendMessage}
          disabled={loading || isTyping}
        />
      </div>
    </div>
  );
}