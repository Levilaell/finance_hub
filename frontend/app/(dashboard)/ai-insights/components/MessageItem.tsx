'use client';

import { useState } from 'react';
import { format } from 'date-fns';
import { ptBR } from 'date-fns/locale';
import { AIMessage } from '../types/ai-insights.types';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { ThumbsUp, ThumbsDown, Copy, Check } from 'lucide-react';
import { cn } from '@/lib/utils';
import { InsightPreview } from './InsightPreview';
import { ChartRenderer } from './ChartRenderer';

interface MessageItemProps {
  message: AIMessage;
}

export function MessageItem({ message }: MessageItemProps) {
  const [copied, setCopied] = useState(false);
  const [feedbackGiven, setFeedbackGiven] = useState<boolean | null>(null);

  const handleCopy = () => {
    navigator.clipboard.writeText(message.content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleFeedback = async (helpful: boolean) => {
    setFeedbackGiven(helpful);
    // TODO: Send feedback to API
  };

  const isUser = message.role === 'user';

  return (
    <div
      className={cn(
        'flex gap-3',
        isUser ? 'justify-end' : 'justify-start'
      )}
    >
      {/* Avatar */}
      {!isUser && (
        <div className="flex-shrink-0 w-8 h-8 rounded-full bg-blue-500 flex items-center justify-center">
          <span className="text-white text-sm font-semibold">AI</span>
        </div>
      )}

      <div className={cn('max-w-[80%]', isUser && 'order-first')}>
        {/* Message bubble */}
        <div
          className={cn(
            'rounded-lg px-4 py-3',
            isUser
              ? 'bg-blue-500 text-white'
              : 'bg-gray-100 text-gray-900'
          )}
        >
          <p className="whitespace-pre-wrap">{message.content}</p>

          {/* Timestamp and credits */}
          <div
            className={cn(
              'mt-2 text-xs flex items-center gap-2',
              isUser ? 'text-blue-100' : 'text-gray-500'
            )}
          >
            <span>
              {format(new Date(message.created_at), 'HH:mm', {
                locale: ptBR,
              })}
            </span>
            {message.credits_used && (
              <span>• {message.credits_used} créditos</span>
            )}
          </div>
        </div>

        {/* Structured data (charts, tables) */}
        {message.structured_data && (
          <Card className="mt-3 p-4">
            <ChartRenderer data={message.structured_data} />
          </Card>
        )}

        {/* Insights */}
        {message.insights && message.insights.length > 0 && (
          <div className="mt-3 space-y-2">
            {message.insights.map((insight, index) => (
              <InsightPreview key={index} insight={insight} compact />
            ))}
          </div>
        )}

        {/* Actions for assistant messages */}
        {!isUser && (
          <div className="mt-2 flex items-center gap-2">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => handleFeedback(true)}
              className={cn(
                'h-8',
                feedbackGiven === true && 'text-green-600'
              )}
            >
              <ThumbsUp className="h-4 w-4" />
            </Button>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => handleFeedback(false)}
              className={cn(
                'h-8',
                feedbackGiven === false && 'text-red-600'
              )}
            >
              <ThumbsDown className="h-4 w-4" />
            </Button>
            <Button
              variant="ghost"
              size="sm"
              onClick={handleCopy}
              className="h-8"
            >
              {copied ? (
                <Check className="h-4 w-4" />
              ) : (
                <Copy className="h-4 w-4" />
              )}
            </Button>
          </div>
        )}
      </div>

      {/* User avatar */}
      {isUser && (
        <div className="flex-shrink-0 w-8 h-8 rounded-full bg-gray-300 flex items-center justify-center">
          <span className="text-gray-700 text-sm font-semibold">U</span>
        </div>
      )}
    </div>
  );
}