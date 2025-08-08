'use client';

import { useState, useEffect } from 'react';
import { ChatInterface } from './components/ChatInterface';
import { InsightsList } from './components/InsightsList';
import { CreditBalance } from './components/CreditBalance';
import { ConversationList } from './components/ConversationList';
import { AIInsightsErrorBoundary } from './components/AIInsightsErrorBoundary';
import { useCredits } from './hooks/useCredits';
import { useInsights } from './hooks/useInsights';
import { useConversations } from './hooks/useConversations';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { testId, TEST_IDS } from '@/utils/test-helpers';

function AIInsightsContent() {
  const [activeConversationId, setActiveConversationId] = useState<string | null>(null);
  const { credits, loading: creditsLoading } = useCredits();
  const { insights, loading: insightsLoading, takeAction, dismissInsight } = useInsights();
  const { conversations, loading: conversationsLoading, createConversation } = useConversations();

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
    <div className="flex h-[calc(100vh-4rem)] gap-6 p-6">
      {/* Sidebar */}
      <div className="w-80 flex flex-col gap-4">
        {/* Credit Balance */}
        <CreditBalance 
          balance={credits?.balance || 0}
          monthlyAllowance={credits?.monthly_allowance || 0}
          bonusCredits={credits?.bonus_credits}
        />
        
        {/* Conversations */}
        <div className="flex-1 glass rounded-xl overflow-hidden hover-lift transition-all duration-300">
          <ConversationList
            conversations={conversations}
            activeId={activeConversationId}
            onSelect={setActiveConversationId}
            loading={conversationsLoading}
          />
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex flex-col">
        <Tabs defaultValue="chat" className="flex-1 flex flex-col">
          <TabsList className="w-full justify-start bg-card border border-border rounded-xl">
            <TabsTrigger 
              value="chat" 
              className="data-[state=active]:bg-gradient-primary data-[state=active]:text-white data-[state=active]:shadow-md transition-all duration-300 hover:bg-muted"
            >
              Chat com IA
            </TabsTrigger>
            <TabsTrigger 
              value="insights"
              className="data-[state=active]:bg-gradient-primary data-[state=active]:text-white data-[state=active]:shadow-md transition-all duration-300 hover:bg-muted"
            >
              Insights
            </TabsTrigger>
          </TabsList>
          
          <TabsContent value="chat" className="flex-1 flex mt-4">
            <ChatInterface
              conversationId={activeConversationId}
              onNewConversation={(id) => setActiveConversationId(id)}
              createConversation={createConversation}
            />
          </TabsContent>
          
          <TabsContent value="insights" className="flex-1 overflow-auto p-6 mt-4">
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

export default function AIInsightsPage() {
  return (
    <AIInsightsErrorBoundary>
      <AIInsightsContent />
    </AIInsightsErrorBoundary>
  );
}