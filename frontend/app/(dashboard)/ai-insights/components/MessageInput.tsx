'use client';

import { useState, useRef, KeyboardEvent } from 'react';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Send, Paperclip } from 'lucide-react';
import { testId, TEST_IDS } from '@/utils/test-helpers';

interface MessageInputProps {
  onSend: (message: string) => void;
  disabled?: boolean;
}

export function MessageInput({ onSend, disabled }: MessageInputProps) {
  const [message, setMessage] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const handleSend = () => {
    const trimmedMessage = message.trim();
    if (trimmedMessage && !disabled) {
      onSend(trimmedMessage);
      setMessage('');
      textareaRef.current?.focus();
    }
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="flex gap-2">
      <div className="flex-1 relative">
        <Textarea
          ref={textareaRef}
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Digite sua mensagem..."
          disabled={disabled}
          className="resize-none pr-10"
          rows={1}
          style={{
            minHeight: '44px',
            maxHeight: '120px',
          }}
          {...testId(TEST_IDS.aiInsights.chatInput)}
        />
        <Button
          size="icon"
          variant="ghost"
          className="absolute right-1 bottom-1 h-8 w-8"
          disabled
          title="Anexar arquivo (em breve)"
        >
          <Paperclip className="h-4 w-4" />
        </Button>
      </div>
      <Button
        onClick={handleSend}
        disabled={disabled || !message.trim()}
        size="icon"
        className="h-[44px] w-[44px]"
        {...testId(TEST_IDS.aiInsights.sendMessageButton)}
      >
        <Send className="h-4 w-4" />
      </Button>
    </div>
  );
}