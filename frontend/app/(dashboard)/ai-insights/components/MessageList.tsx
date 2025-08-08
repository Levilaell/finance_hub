'use client';

import { useEffect, useRef } from 'react';
import { MessageItem } from './MessageItem';
import { AIMessage } from '../types/ai-insights.types';
import { Card, CardContent } from '@/components/ui/card';
import { Loader2 } from 'lucide-react';
import { testId, TEST_IDS } from '@/utils/test-helpers';

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
      <div className="flex-1 flex items-center justify-center bg-card">
        <div className="text-center">
          <div className="relative">
            <Loader2 className="h-8 w-8 animate-spin text-primary mx-auto mb-4" />
            <div className="absolute inset-0 h-8 w-8 mx-auto animate-ping rounded-full bg-primary/20"></div>
          </div>
          <p className="text-muted-foreground font-medium">Carregando conversas...</p>
        </div>
      </div>
    );
  }

  if (messages.length === 0) {
    return (
      <div className="flex-1 flex items-center justify-center p-8 bg-card">
        <div className="text-center max-w-md">
          <p className="text-lg font-semibold text-foreground mb-4">
            Nenhuma mensagem ainda. Comece perguntando sobre suas finanças!
          </p>
          <Card className="bg-muted/30 border-border">
            <CardContent className="p-4">
              <p className="text-sm text-muted-foreground font-medium mb-3">Exemplos de perguntas:</p>
              <ul className="space-y-2 text-sm">
                <li className="p-3 bg-card rounded-lg hover:bg-muted/50 transition-colors duration-200 text-foreground">&quot;Quais foram meus maiores gastos este mês?&quot;</li>
                <li className="p-3 bg-card rounded-lg hover:bg-muted/50 transition-colors duration-200 text-foreground">&quot;Como posso reduzir minhas despesas?&quot;</li>
                <li className="p-3 bg-card rounded-lg hover:bg-muted/50 transition-colors duration-200 text-foreground">&quot;Mostre uma análise do meu fluxo de caixa&quot;</li>
                <li className="p-3 bg-card rounded-lg hover:bg-muted/50 transition-colors duration-200 text-foreground">&quot;Existem transações suspeitas na minha conta?&quot;</li>
              </ul>
            </CardContent>
          </Card>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-gradient-subtle" {...testId(TEST_IDS.aiInsights.messageList)}>
      {messages.map((message) => (
        <MessageItem key={message.id} message={message} />
      ))}
      <div ref={bottomRef} />
    </div>
  );
}