'use client';

import { useEffect, useRef } from 'react';
import { MessageItem } from './MessageItem';
import { AIMessage } from '../types/ai-insights.types';
import { Loader2 } from 'lucide-react';

interface MessageListProps {
  messages: AIMessage[];
  loading: boolean;
}

export function MessageList({ messages, loading }: MessageListProps) {
  const bottomRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom on new messages
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  if (loading && messages.length === 0) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="h-8 w-8 animate-spin text-gray-400 mx-auto mb-4" />
          <p className="text-gray-500">Carregando conversas...</p>
        </div>
      </div>
    );
  }

  if (messages.length === 0) {
    return (
      <div className="flex-1 flex items-center justify-center p-8">
        <div className="text-center max-w-md">
          <p className="text-gray-500 mb-4">
            Nenhuma mensagem ainda. Comece perguntando sobre suas finanças!
          </p>
          <div className="text-sm text-gray-400">
            <p className="mb-2">Exemplos de perguntas:</p>
            <ul className="space-y-1">
              <li>&quot;Quais foram meus maiores gastos este mês?&quot;</li>
              <li>&quot;Como posso reduzir minhas despesas?&quot;</li>
              <li>&quot;Mostre uma análise do meu fluxo de caixa&quot;</li>
              <li>&quot;Existem transações suspeitas na minha conta?&quot;</li>
            </ul>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 overflow-y-auto p-4 space-y-4">
      {messages.map((message) => (
        <MessageItem key={message.id} message={message} />
      ))}
      <div ref={bottomRef} />
    </div>
  );
}