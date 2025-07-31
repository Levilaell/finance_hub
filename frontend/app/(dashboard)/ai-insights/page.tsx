'use client';

import { useState, useEffect } from 'react';
import { ChatInterface } from './components/ChatInterface';
import { InsightsList } from './components/InsightsList';
import { CreditBalance } from './components/CreditBalance';
import { ConversationList } from './components/ConversationList';
import { useCredits } from './hooks/useCredits';
import { useInsights } from './hooks/useInsights';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';

export default function AIInsightsPage() {
  const [activeConversationId, setActiveConversationId] = useState<string | null>(null);
  const { credits, loading: creditsLoading } = useCredits();
  const { insights, loading: insightsLoading, takeAction, dismissInsight } = useInsights();

  const handleInsightAction = async (insightId: string, action: 'complete' | 'dismiss') => {
    if (action === 'complete') {
      await takeAction(insightId, {
        action_taken: true,
      });
    } else {
      await dismissInsight(insightId);
    }
  };

  return (
    <div className="flex h-[calc(100vh-4rem)] gap-4">
      {/* Sidebar */}
      <div className="w-80 flex flex-col gap-4">
        {/* Credit Balance */}
        <CreditBalance 
          balance={credits?.balance || 0}
          monthlyAllowance={credits?.monthly_allowance || 0}
          bonusCredits={credits?.bonus_credits}
        />
        
        {/* Conversations */}
        <div className="flex-1 bg-white rounded-lg shadow-sm border overflow-hidden">
          <ConversationList
            activeId={activeConversationId}
            onSelect={setActiveConversationId}
          />
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex flex-col">
        <Tabs defaultValue="chat" className="flex-1 flex flex-col">
          <TabsList className="w-full justify-start">
            <TabsTrigger value="chat">Chat com IA</TabsTrigger>
            <TabsTrigger value="insights">Insights</TabsTrigger>
          </TabsList>
          
          <TabsContent value="chat" className="flex-1 flex">
            <ChatInterface
              conversationId={activeConversationId}
              onNewConversation={(id) => setActiveConversationId(id)}
            />
          </TabsContent>
          
          <TabsContent value="insights" className="flex-1 overflow-auto p-6">
            <InsightsList 
              insights={insights} 
              loading={insightsLoading}
              onInsightAction={handleInsightAction}
            />
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}