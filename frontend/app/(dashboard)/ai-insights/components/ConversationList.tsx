'use client';

import { useState } from 'react';
import { format } from 'date-fns';
import { ptBR } from 'date-fns/locale';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { ScrollArea } from '@/components/ui/scroll-area';
import { AIConversation } from '../types/ai-insights.types';
import { 
  Search, 
  MessageSquare, 
  Archive,
  Clock,
  Zap
} from 'lucide-react';
import { cn } from '@/lib/utils';

interface ConversationListProps {
  conversations?: AIConversation[];
  activeId: string | null;
  onSelect: (id: string) => void;
  loading?: boolean;
}

// Mock data for development
const mockConversations: AIConversation[] = [
  {
    id: '1',
    title: 'Análise de gastos mensais',
    status: 'active',
    message_count: 15,
    total_credits_used: 23,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
    last_message_at: new Date().toISOString(),
  },
  {
    id: '2',
    title: 'Fluxo de caixa projetado',
    status: 'active',
    message_count: 8,
    total_credits_used: 12,
    created_at: new Date(Date.now() - 86400000).toISOString(),
    updated_at: new Date(Date.now() - 3600000).toISOString(),
    last_message_at: new Date(Date.now() - 3600000).toISOString(),
  },
  {
    id: '3',
    title: 'Oportunidades de economia',
    status: 'archived',
    message_count: 20,
    total_credits_used: 35,
    created_at: new Date(Date.now() - 604800000).toISOString(),
    updated_at: new Date(Date.now() - 259200000).toISOString(),
    last_message_at: new Date(Date.now() - 259200000).toISOString(),
  },
];

export function ConversationList({ 
  conversations = mockConversations, 
  activeId, 
  onSelect,
  loading 
}: ConversationListProps) {
  const [searchTerm, setSearchTerm] = useState('');
  const [showArchived, setShowArchived] = useState(false);

  const filteredConversations = conversations.filter(conv => {
    const matchesSearch = conv.title.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesStatus = showArchived ? conv.status === 'archived' : conv.status === 'active';
    return matchesSearch && matchesStatus;
  });

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="p-4 border-b">
        <h3 className="font-semibold text-gray-900 mb-3">Conversas</h3>
        
        {/* Search */}
        <div className="relative mb-3">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
          <Input
            type="search"
            placeholder="Buscar conversas..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="pl-9"
          />
        </div>

        {/* Toggle archived */}
        <div className="flex items-center gap-2">
          <Button
            variant={!showArchived ? 'default' : 'outline'}
            size="sm"
            onClick={() => setShowArchived(false)}
            className="flex-1"
          >
            <MessageSquare className="h-4 w-4 mr-1" />
            Ativas
          </Button>
          <Button
            variant={showArchived ? 'default' : 'outline'}
            size="sm"
            onClick={() => setShowArchived(true)}
            className="flex-1"
          >
            <Archive className="h-4 w-4 mr-1" />
            Arquivadas
          </Button>
        </div>
      </div>

      {/* Conversations list */}
      <ScrollArea className="flex-1">
        <div className="p-2">
          {loading ? (
            <div className="text-center py-8">
              <p className="text-sm text-gray-500">Carregando conversas...</p>
            </div>
          ) : filteredConversations.length === 0 ? (
            <div className="text-center py-8">
              <p className="text-sm text-gray-500">
                {searchTerm 
                  ? 'Nenhuma conversa encontrada' 
                  : showArchived 
                    ? 'Nenhuma conversa arquivada' 
                    : 'Nenhuma conversa ativa'}
              </p>
            </div>
          ) : (
            <div className="space-y-1">
              {filteredConversations.map((conversation) => (
                <button
                  key={conversation.id}
                  onClick={() => onSelect(conversation.id)}
                  className={cn(
                    'w-full text-left p-3 rounded-lg transition-colors',
                    'hover:bg-gray-100',
                    activeId === conversation.id && 'bg-blue-50 hover:bg-blue-50'
                  )}
                >
                  <div className="flex items-start justify-between mb-1">
                    <h4 className={cn(
                      'font-medium text-sm truncate pr-2',
                      activeId === conversation.id ? 'text-blue-900' : 'text-gray-900'
                    )}>
                      {conversation.title}
                    </h4>
                    {conversation.status === 'archived' && (
                      <Archive className="h-3 w-3 text-gray-400 flex-shrink-0" />
                    )}
                  </div>
                  
                  <div className="flex items-center gap-3 text-xs text-gray-500">
                    <span className="flex items-center gap-1">
                      <MessageSquare className="h-3 w-3" />
                      {conversation.message_count}
                    </span>
                    <span className="flex items-center gap-1">
                      <Zap className="h-3 w-3" />
                      {conversation.total_credits_used}
                    </span>
                  </div>
                  
                  {conversation.last_message_at && (
                    <div className="flex items-center gap-1 mt-1 text-xs text-gray-400">
                      <Clock className="h-3 w-3" />
                      {format(new Date(conversation.last_message_at), 'dd MMM HH:mm', {
                        locale: ptBR,
                      })}
                    </div>
                  )}
                </button>
              ))}
            </div>
          )}
        </div>
      </ScrollArea>
    </div>
  );
}