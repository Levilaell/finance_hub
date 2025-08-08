import { aiInsightsService } from '@/app/(dashboard)/ai-insights/services/ai-insights.service';
import apiClient from '@/lib/api-client';
import {
  AICredit,
  AIConversation,
  AIMessage,
  AIInsight,
  SendMessageRequest,
  PurchaseCreditsRequest,
  InsightActionRequest,
} from '@/app/(dashboard)/ai-insights/types/ai-insights.types';

// Mock the API client
jest.mock('@/lib/api-client');
const mockApiClient = apiClient as jest.Mocked<typeof apiClient>;

describe('AIInsightsService', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Credits endpoints', () => {
    describe('getCredits', () => {
      it('should fetch credits successfully', async () => {
        const mockCredits: AICredit = {
          id: '1',
          balance: 100,
          monthly_allowance: 50,
          bonus_credits: 25,
          last_reset: '2023-01-01T00:00:00Z',
          total_purchased: 200,
          created_at: '2023-01-01T00:00:00Z',
          updated_at: '2023-01-01T00:00:00Z',
        };

        mockApiClient.get.mockResolvedValue(mockCredits);

        const result = await aiInsightsService.getCredits();

        expect(mockApiClient.get).toHaveBeenCalledWith('/ai-insights/credits/');
        expect(result).toEqual(mockCredits);
      });

      it('should handle get credits error', async () => {
        const error = new Error('Failed to fetch credits');
        mockApiClient.get.mockRejectedValue(error);

        await expect(aiInsightsService.getCredits()).rejects.toThrow(
          'Failed to fetch credits'
        );
      });
    });

    describe('getCreditTransactions', () => {
      it('should fetch credit transactions with pagination', async () => {
        const mockResponse = {
          results: [
            {
              id: '1',
              type: 'usage' as const,
              amount: -5,
              balance_before: 100,
              balance_after: 95,
              description: 'AI chat usage',
              metadata: { model: 'gpt-4o-mini' },
              created_at: '2023-01-01T00:00:00Z',
            },
          ],
          count: 1,
        };

        mockApiClient.get.mockResolvedValue(mockResponse);

        const result = await aiInsightsService.getCreditTransactions({
          page: 1,
          page_size: 20,
          type: 'usage',
        });

        expect(mockApiClient.get).toHaveBeenCalledWith(
          '/ai-insights/credits/transactions/',
          { page: 1, page_size: 20, type: 'usage' }
        );
        expect(result).toEqual(mockResponse);
      });

      it('should fetch transactions without parameters', async () => {
        const mockResponse = { results: [], count: 0 };
        mockApiClient.get.mockResolvedValue(mockResponse);

        const result = await aiInsightsService.getCreditTransactions();

        expect(mockApiClient.get).toHaveBeenCalledWith(
          '/ai-insights/credits/transactions/',
          undefined
        );
        expect(result).toEqual(mockResponse);
      });
    });

    describe('purchaseCredits', () => {
      it('should purchase credits successfully', async () => {
        const purchaseRequest: PurchaseCreditsRequest = {
          amount: 100,
          payment_method_id: 'pm_test_123',
        };

        const mockResponse = {
          payment_intent_id: 'pi_test_123',
          credits_added: 100,
          new_balance: 200,
          transaction_id: 'txn_123',
        };

        mockApiClient.post.mockResolvedValue(mockResponse);

        const result = await aiInsightsService.purchaseCredits(purchaseRequest);

        expect(mockApiClient.post).toHaveBeenCalledWith(
          '/ai-insights/credits/purchase/',
          purchaseRequest
        );
        expect(result).toEqual(mockResponse);
      });
    });
  });

  describe('Conversations endpoints', () => {
    describe('getConversations', () => {
      it('should fetch conversations with filters', async () => {
        const mockResponse = {
          results: [
            {
              id: '1',
              title: 'Test Conversation',
              status: 'active' as const,
              message_count: 5,
              total_credits_used: 10,
              created_at: '2023-01-01T00:00:00Z',
              updated_at: '2023-01-01T00:00:00Z',
            },
          ],
          count: 1,
        };

        mockApiClient.get.mockResolvedValue(mockResponse);

        const result = await aiInsightsService.getConversations({
          status: 'active',
          search: 'test',
          page: 1,
          page_size: 10,
        });

        expect(mockApiClient.get).toHaveBeenCalledWith(
          '/ai-insights/conversations/',
          { status: 'active', search: 'test', page: 1, page_size: 10 }
        );
        expect(result).toEqual(mockResponse);
      });
    });

    describe('getConversation', () => {
      it('should fetch specific conversation', async () => {
        const mockConversation: AIConversation = {
          id: '1',
          title: 'Test Conversation',
          status: 'active',
          message_count: 5,
          total_credits_used: 10,
          created_at: '2023-01-01T00:00:00Z',
          updated_at: '2023-01-01T00:00:00Z',
        };

        mockApiClient.get.mockResolvedValue(mockConversation);

        const result = await aiInsightsService.getConversation('1');

        expect(mockApiClient.get).toHaveBeenCalledWith('/ai-insights/conversations/1/');
        expect(result).toEqual(mockConversation);
      });
    });

    describe('createConversation', () => {
      it('should create new conversation', async () => {
        const mockConversation: AIConversation = {
          id: '1',
          title: 'New Conversation',
          status: 'active',
          message_count: 0,
          total_credits_used: 0,
          created_at: '2023-01-01T00:00:00Z',
          updated_at: '2023-01-01T00:00:00Z',
        };

        mockApiClient.post.mockResolvedValue(mockConversation);

        const result = await aiInsightsService.createConversation({
          title: 'New Conversation',
        });

        expect(mockApiClient.post).toHaveBeenCalledWith(
          '/ai-insights/conversations/',
          { title: 'New Conversation' }
        );
        expect(result).toEqual(mockConversation);
      });
    });

    describe('updateConversation', () => {
      it('should update conversation', async () => {
        const updatedConversation: AIConversation = {
          id: '1',
          title: 'Updated Title',
          status: 'active',
          message_count: 0,
          total_credits_used: 0,
          created_at: '2023-01-01T00:00:00Z',
          updated_at: '2023-01-01T00:01:00Z',
        };

        mockApiClient.patch.mockResolvedValue(updatedConversation);

        const result = await aiInsightsService.updateConversation('1', {
          title: 'Updated Title',
        });

        expect(mockApiClient.patch).toHaveBeenCalledWith(
          '/ai-insights/conversations/1/',
          { title: 'Updated Title' }
        );
        expect(result).toEqual(updatedConversation);
      });
    });

    describe('archiveConversation', () => {
      it('should archive conversation', async () => {
        const archivedConversation: AIConversation = {
          id: '1',
          title: 'Test Conversation',
          status: 'archived',
          message_count: 5,
          total_credits_used: 10,
          created_at: '2023-01-01T00:00:00Z',
          updated_at: '2023-01-01T00:01:00Z',
        };

        mockApiClient.post.mockResolvedValue(archivedConversation);

        const result = await aiInsightsService.archiveConversation('1');

        expect(mockApiClient.post).toHaveBeenCalledWith(
          '/ai-insights/conversations/1/archive/'
        );
        expect(result).toEqual(archivedConversation);
      });
    });

    describe('deleteConversation', () => {
      it('should delete conversation', async () => {
        mockApiClient.delete.mockResolvedValue(undefined);

        await aiInsightsService.deleteConversation('1');

        expect(mockApiClient.delete).toHaveBeenCalledWith(
          '/ai-insights/conversations/1/'
        );
      });
    });
  });

  describe('Messages endpoints', () => {
    describe('getConversationMessages', () => {
      it('should fetch messages with results format', async () => {
        const mockMessages: AIMessage[] = [
          {
            id: '1',
            role: 'user',
            content: 'Hello',
            created_at: '2023-01-01T00:00:00Z',
          },
          {
            id: '2',
            role: 'assistant',
            content: 'Hi there!',
            created_at: '2023-01-01T00:01:00Z',
          },
        ];

        mockApiClient.get.mockResolvedValue({ results: mockMessages });

        const result = await aiInsightsService.getConversationMessages(
          'conv-123',
          { page: 1, page_size: 20 }
        );

        expect(mockApiClient.get).toHaveBeenCalledWith(
          '/ai-insights/conversations/conv-123/messages/',
          { page: 1, page_size: 20 }
        );
        expect(result).toEqual(mockMessages);
      });

      it('should fetch messages with data format', async () => {
        const mockMessages: AIMessage[] = [
          {
            id: '1',
            role: 'user',
            content: 'Hello',
            created_at: '2023-01-01T00:00:00Z',
          },
        ];

        mockApiClient.get.mockResolvedValue({ data: mockMessages });

        const result = await aiInsightsService.getConversationMessages('conv-123');

        expect(result).toEqual(mockMessages);
      });

      it('should handle empty response', async () => {
        mockApiClient.get.mockResolvedValue({});

        const result = await aiInsightsService.getConversationMessages('conv-123');

        expect(result).toEqual([]);
      });
    });

    describe('sendMessage', () => {
      it('should send message successfully', async () => {
        const messageRequest: SendMessageRequest = {
          content: 'Analyze my expenses',
          request_type: 'analysis',
        };

        const mockResponse = {
          message_id: 'msg-123',
          content: 'Here is your expense analysis...',
          credits_used: 5,
          credits_remaining: 95,
          structured_data: { charts: [] },
          insights: [],
          created_at: '2023-01-01T00:00:00Z',
        };

        mockApiClient.post.mockResolvedValue(mockResponse);

        const result = await aiInsightsService.sendMessage('conv-123', messageRequest);

        expect(mockApiClient.post).toHaveBeenCalledWith(
          '/ai-insights/conversations/conv-123/send_message/',
          messageRequest
        );
        expect(result).toEqual(mockResponse);
      });
    });

    describe('updateMessageFeedback', () => {
      it('should update message feedback', async () => {
        const mockMessage: AIMessage = {
          id: 'msg-123',
          role: 'assistant',
          content: 'AI response',
          helpful: true,
          user_feedback: 'Very helpful!',
          created_at: '2023-01-01T00:00:00Z',
        };

        mockApiClient.patch.mockResolvedValue(mockMessage);

        const result = await aiInsightsService.updateMessageFeedback('msg-123', {
          helpful: true,
          feedback: 'Very helpful!',
        });

        expect(mockApiClient.patch).toHaveBeenCalledWith(
          '/ai-insights/messages/msg-123/feedback/',
          { helpful: true, feedback: 'Very helpful!' }
        );
        expect(result).toEqual(mockMessage);
      });
    });
  });

  describe('Insights endpoints', () => {
    describe('getInsights', () => {
      it('should fetch insights with filters', async () => {
        const mockInsights: AIInsight[] = [
          {
            id: '1',
            type: 'cost_saving',
            priority: 'high',
            status: 'new',
            title: 'Reduce costs',
            description: 'Cost reduction opportunity',
            created_at: '2023-01-01T00:00:00Z',
          },
        ];

        mockApiClient.get.mockResolvedValue({ results: mockInsights });

        const result = await aiInsightsService.getInsights({
          priority: 'high',
          status: 'new',
          type: 'cost_saving',
          page: 1,
          page_size: 20,
        });

        expect(mockApiClient.get).toHaveBeenCalledWith('/ai-insights/insights/', {
          priority: 'high',
          status: 'new',
          type: 'cost_saving',
          page: 1,
          page_size: 20,
        });
        expect(result).toEqual(mockInsights);
      });

      it('should handle data format response', async () => {
        const mockInsights: AIInsight[] = [
          {
            id: '1',
            type: 'opportunity',
            priority: 'medium',
            status: 'viewed',
            title: 'Revenue opportunity',
            description: 'Revenue growth opportunity',
            created_at: '2023-01-01T00:00:00Z',
          },
        ];

        mockApiClient.get.mockResolvedValue({ data: mockInsights });

        const result = await aiInsightsService.getInsights();

        expect(result).toEqual(mockInsights);
      });
    });

    describe('getInsight', () => {
      it('should fetch specific insight', async () => {
        const mockInsight: AIInsight = {
          id: '1',
          type: 'risk',
          priority: 'critical',
          status: 'new',
          title: 'Cash flow risk',
          description: 'Critical cash flow issue',
          potential_impact: 50000,
          created_at: '2023-01-01T00:00:00Z',
        };

        mockApiClient.get.mockResolvedValue(mockInsight);

        const result = await aiInsightsService.getInsight('1');

        expect(mockApiClient.get).toHaveBeenCalledWith('/ai-insights/insights/1/');
        expect(result).toEqual(mockInsight);
      });
    });

    describe('getDashboardInsights', () => {
      it('should fetch dashboard insights', async () => {
        const mockInsights: AIInsight[] = [
          {
            id: '1',
            type: 'trend',
            priority: 'medium',
            status: 'new',
            title: 'Market trend',
            description: 'Important market trend',
            created_at: '2023-01-01T00:00:00Z',
          },
        ];

        mockApiClient.get.mockResolvedValue({ results: mockInsights });

        const result = await aiInsightsService.getDashboardInsights();

        expect(mockApiClient.get).toHaveBeenCalledWith(
          '/ai-insights/insights/dashboard/'
        );
        expect(result).toEqual(mockInsights);
      });
    });

    describe('getInsightStats', () => {
      it('should fetch insight statistics', async () => {
        const mockStats = {
          total: 50,
          by_priority: { critical: 5, high: 15, medium: 20, low: 10 },
          by_status: { new: 30, viewed: 10, completed: 10 },
          by_type: { cost_saving: 20, opportunity: 15, risk: 10, trend: 5 },
          completion_rate: 20,
          total_impact: 100000,
        };

        mockApiClient.get.mockResolvedValue(mockStats);

        const result = await aiInsightsService.getInsightStats();

        expect(mockApiClient.get).toHaveBeenCalledWith('/ai-insights/insights/stats/');
        expect(result).toEqual(mockStats);
      });
    });

    describe('markInsightViewed', () => {
      it('should mark insight as viewed', async () => {
        const mockInsight: AIInsight = {
          id: '1',
          type: 'opportunity',
          priority: 'high',
          status: 'viewed',
          title: 'Revenue opportunity',
          description: 'Growth opportunity',
          viewed_at: '2023-01-01T00:01:00Z',
          created_at: '2023-01-01T00:00:00Z',
        };

        mockApiClient.post.mockResolvedValue(mockInsight);

        const result = await aiInsightsService.markInsightViewed('1');

        expect(mockApiClient.post).toHaveBeenCalledWith(
          '/ai-insights/insights/1/mark-viewed/'
        );
        expect(result).toEqual(mockInsight);
      });
    });

    describe('takeInsightAction', () => {
      it('should take action on insight', async () => {
        const actionRequest: InsightActionRequest = {
          action_taken: true,
          actual_impact: 15000,
          user_feedback: 'Successfully implemented cost-saving measures',
        };

        const mockInsight: AIInsight = {
          id: '1',
          type: 'cost_saving',
          priority: 'high',
          status: 'completed',
          title: 'Cost reduction',
          description: 'Reduce operational costs',
          action_taken: true,
          actual_impact: 15000,
          user_feedback: 'Successfully implemented cost-saving measures',
          created_at: '2023-01-01T00:00:00Z',
        };

        mockApiClient.post.mockResolvedValue(mockInsight);

        const result = await aiInsightsService.takeInsightAction('1', actionRequest);

        expect(mockApiClient.post).toHaveBeenCalledWith(
          '/ai-insights/insights/1/take-action/',
          actionRequest
        );
        expect(result).toEqual(mockInsight);
      });
    });

    describe('dismissInsight', () => {
      it('should dismiss insight with reason', async () => {
        const mockInsight: AIInsight = {
          id: '1',
          type: 'opportunity',
          priority: 'low',
          status: 'dismissed',
          title: 'Minor opportunity',
          description: 'Small growth opportunity',
          user_feedback: 'Not applicable currently',
          created_at: '2023-01-01T00:00:00Z',
        };

        mockApiClient.post.mockResolvedValue(mockInsight);

        const result = await aiInsightsService.dismissInsight(
          '1',
          'Not applicable currently'
        );

        expect(mockApiClient.post).toHaveBeenCalledWith(
          '/ai-insights/insights/1/dismiss/',
          { reason: 'Not applicable currently' }
        );
        expect(result).toEqual(mockInsight);
      });

      it('should dismiss insight without reason', async () => {
        const mockInsight: AIInsight = {
          id: '1',
          type: 'trend',
          priority: 'low',
          status: 'dismissed',
          title: 'Market trend',
          description: 'Minor market trend',
          created_at: '2023-01-01T00:00:00Z',
        };

        mockApiClient.post.mockResolvedValue(mockInsight);

        const result = await aiInsightsService.dismissInsight('1');

        expect(mockApiClient.post).toHaveBeenCalledWith(
          '/ai-insights/insights/1/dismiss/',
          { reason: undefined }
        );
        expect(result).toEqual(mockInsight);
      });
    });
  });

  describe('Analysis endpoints', () => {
    describe('quickAnalysis', () => {
      it('should perform quick analysis', async () => {
        const mockResponse = {
          analysis: 'Your expenses have increased by 15% this month',
          insights: [],
          charts: [{ type: 'pie', data: [] }],
          credits_used: 3,
        };

        mockApiClient.post.mockResolvedValue(mockResponse);

        const result = await aiInsightsService.quickAnalysis({
          query: 'Analyze my monthly expenses',
          type: 'expense_analysis',
        });

        expect(mockApiClient.post).toHaveBeenCalledWith(
          '/ai-insights/analysis/quick/',
          { query: 'Analyze my monthly expenses', type: 'expense_analysis' }
        );
        expect(result).toEqual(mockResponse);
      });
    });

    describe('generateReport', () => {
      it('should generate comprehensive report', async () => {
        const mockResponse = {
          report_id: 'report-123',
          title: 'Monthly Financial Report',
          content: 'Comprehensive financial analysis...',
          charts: [{ type: 'line', data: [] }],
          insights: [],
          credits_used: 10,
        };

        mockApiClient.post.mockResolvedValue(mockResponse);

        const result = await aiInsightsService.generateReport({
          type: 'monthly',
          start_date: '2023-01-01',
          end_date: '2023-01-31',
          include_sections: ['overview', 'expenses', 'revenue'],
        });

        expect(mockApiClient.post).toHaveBeenCalledWith(
          '/ai-insights/analysis/report/',
          {
            type: 'monthly',
            start_date: '2023-01-01',
            end_date: '2023-01-31',
            include_sections: ['overview', 'expenses', 'revenue'],
          }
        );
        expect(result).toEqual(mockResponse);
      });
    });

    describe('getForecast', () => {
      it('should get financial forecast', async () => {
        const mockResponse = {
          forecast: { revenue: [45000, 48000, 52000] },
          confidence: 0.85,
          insights: [],
          credits_used: 7,
        };

        mockApiClient.post.mockResolvedValue(mockResponse);

        const result = await aiInsightsService.getForecast({
          period: 90,
          metrics: ['revenue', 'expenses'],
        });

        expect(mockApiClient.post).toHaveBeenCalledWith(
          '/ai-insights/analysis/forecast/',
          { period: 90, metrics: ['revenue', 'expenses'] }
        );
        expect(result).toEqual(mockResponse);
      });
    });

    describe('getBenchmark', () => {
      it('should get industry benchmark', async () => {
        const mockResponse = {
          comparison: { revenue_per_employee: 75000, industry_avg: 80000 },
          position: 'below_average',
          insights: [],
          credits_used: 5,
        };

        mockApiClient.post.mockResolvedValue(mockResponse);

        const result = await aiInsightsService.getBenchmark({
          metrics: ['revenue_per_employee'],
          industry: 'technology',
        });

        expect(mockApiClient.post).toHaveBeenCalledWith(
          '/ai-insights/analysis/benchmark/',
          { metrics: ['revenue_per_employee'], industry: 'technology' }
        );
        expect(result).toEqual(mockResponse);
      });
    });
  });

  describe('Error handling', () => {
    it('should propagate API client errors', async () => {
      const apiError = new Error('Network error');
      mockApiClient.get.mockRejectedValue(apiError);

      await expect(aiInsightsService.getCredits()).rejects.toThrow('Network error');
    });

    it('should handle empty responses gracefully', async () => {
      mockApiClient.get.mockResolvedValue(null);

      const result = await aiInsightsService.getInsights();

      expect(result).toEqual([]);
    });
  });
});