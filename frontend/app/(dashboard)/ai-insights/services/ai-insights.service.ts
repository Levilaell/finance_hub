import apiClient from '@/lib/api-client';
import {
  AICredit,
  AICreditTransaction,
  AIConversation,
  AIMessage,
  AIInsight,
  SendMessageRequest,
  SendMessageResponse,
  PurchaseCreditsRequest,
  PurchaseCreditsResponse,
  InsightActionRequest,
} from '../types/ai-insights.types';

class AIInsightsService {
  private baseUrl = '/api/ai-insights';

  // Credits endpoints
  async getCredits(): Promise<AICredit> {
    return await apiClient.get<AICredit>(`${this.baseUrl}/credits/`);
  }

  async getCreditTransactions(params?: {
    page?: number;
    page_size?: number;
    type?: string;
  }): Promise<{ results: AICreditTransaction[]; count: number }> {
    return await apiClient.get<{ results: AICreditTransaction[]; count: number }>(`${this.baseUrl}/credits/transactions/`, params);
  }

  async purchaseCredits(data: PurchaseCreditsRequest): Promise<PurchaseCreditsResponse> {
    return await apiClient.post<PurchaseCreditsResponse>(`${this.baseUrl}/credits/purchase/`, data);
  }

  // Conversations endpoints
  async getConversations(params?: {
    status?: string;
    search?: string;
    page?: number;
    page_size?: number;
  }): Promise<{ results: AIConversation[]; count: number }> {
    return await apiClient.get<{ results: AIConversation[]; count: number }>(`${this.baseUrl}/conversations/`, params);
  }

  async getConversation(id: string): Promise<AIConversation> {
    return await apiClient.get<AIConversation>(`${this.baseUrl}/conversations/${id}/`);
  }

  async createConversation(data: { title: string }): Promise<AIConversation> {
    return await apiClient.post<AIConversation>(`${this.baseUrl}/conversations/`, data);
  }

  async updateConversation(id: string, data: Partial<AIConversation>): Promise<AIConversation> {
    return await apiClient.patch<AIConversation>(`${this.baseUrl}/conversations/${id}/`, data);
  }

  async archiveConversation(id: string): Promise<AIConversation> {
    return await apiClient.post<AIConversation>(`${this.baseUrl}/conversations/${id}/archive/`);
  }

  async deleteConversation(id: string): Promise<void> {
    await apiClient.delete(`${this.baseUrl}/conversations/${id}/`);
  }

  // Messages endpoints
  async getConversationMessages(
    conversationId: string,
    params?: { page?: number; page_size?: number }
  ): Promise<AIMessage[]> {
    const response = await apiClient.get<{ results?: AIMessage[]; data?: AIMessage[] }>(`${this.baseUrl}/conversations/${conversationId}/messages/`, params);
    return response.results || response.data || [];
  }

  async sendMessage(
    conversationId: string,
    data: SendMessageRequest
  ): Promise<SendMessageResponse> {
    return await apiClient.post<SendMessageResponse>(
      `${this.baseUrl}/conversations/${conversationId}/send_message/`,
      data
    );
  }

  async updateMessageFeedback(
    messageId: string,
    data: { helpful: boolean; feedback?: string }
  ): Promise<AIMessage> {
    return await apiClient.patch<AIMessage>(`${this.baseUrl}/messages/${messageId}/feedback/`, data);
  }

  // Insights endpoints
  async getInsights(params?: {
    priority?: string;
    status?: string;
    type?: string;
    page?: number;
    page_size?: number;
  }): Promise<AIInsight[]> {
    const response = await apiClient.get<{ results?: AIInsight[]; data?: AIInsight[] }>(`${this.baseUrl}/insights/`, params);
    return response?.results || response?.data || [];
  }

  async getInsight(id: string): Promise<AIInsight> {
    return await apiClient.get<AIInsight>(`${this.baseUrl}/insights/${id}/`);
  }

  async getDashboardInsights(): Promise<AIInsight[]> {
    const response = await apiClient.get<{ results?: AIInsight[]; data?: AIInsight[] }>(`${this.baseUrl}/insights/dashboard/`);
    return response.results || response.data || [];
  }

  async getInsightStats(): Promise<{
    total: number;
    by_priority: Record<string, number>;
    by_status: Record<string, number>;
    by_type: Record<string, number>;
    completion_rate: number;
    total_impact: number;
  }> {
    return await apiClient.get<{
      total: number;
      by_priority: Record<string, number>;
      by_status: Record<string, number>;
      by_type: Record<string, number>;
      completion_rate: number;
      total_impact: number;
    }>(`${this.baseUrl}/insights/stats/`);
  }

  async markInsightViewed(id: string): Promise<AIInsight> {
    return await apiClient.post<AIInsight>(`${this.baseUrl}/insights/${id}/mark-viewed/`);
  }

  async takeInsightAction(id: string, data: InsightActionRequest): Promise<AIInsight> {
    return await apiClient.post<AIInsight>(`${this.baseUrl}/insights/${id}/take-action/`, data);
  }

  async dismissInsight(id: string, reason?: string): Promise<AIInsight> {
    return await apiClient.post<AIInsight>(`${this.baseUrl}/insights/${id}/dismiss/`, { reason });
  }

  // Analysis endpoints
  async quickAnalysis(data: { query: string; type?: string }): Promise<{
    analysis: string;
    insights?: AIInsight[];
    charts?: any[];
    credits_used: number;
  }> {
    return await apiClient.post<{
      analysis: string;
      insights?: AIInsight[];
      charts?: any[];
      credits_used: number;
    }>(`${this.baseUrl}/analysis/quick/`, data);
  }

  async generateReport(data: {
    type: 'monthly' | 'quarterly' | 'yearly' | 'custom';
    start_date?: string;
    end_date?: string;
    include_sections?: string[];
  }): Promise<{
    report_id: string;
    title: string;
    content: string;
    charts: any[];
    insights: AIInsight[];
    credits_used: number;
  }> {
    return await apiClient.post<{
      report_id: string;
      title: string;
      content: string;
      charts: any[];
      insights: AIInsight[];
      credits_used: number;
    }>(`${this.baseUrl}/analysis/report/`, data);
  }

  async getForecast(data: {
    period: number; // days
    metrics?: string[];
  }): Promise<{
    forecast: any;
    confidence: number;
    insights: AIInsight[];
    credits_used: number;
  }> {
    return await apiClient.post<{
      forecast: any;
      confidence: number;
      insights: AIInsight[];
      credits_used: number;
    }>(`${this.baseUrl}/analysis/forecast/`, data);
  }

  async getBenchmark(data: {
    metrics?: string[];
    industry?: string;
  }): Promise<{
    comparison: any;
    position: string;
    insights: AIInsight[];
    credits_used: number;
  }> {
    return await apiClient.post<{
      comparison: any;
      position: string;
      insights: AIInsight[];
      credits_used: number;
    }>(`${this.baseUrl}/analysis/benchmark/`, data);
  }
}

export const aiInsightsService = new AIInsightsService();