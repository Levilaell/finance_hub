/**
 * AI Insights Service
 */
import apiClient from '@/lib/api-client';

export interface AIInsightConfig {
  is_enabled: boolean;
  enabled_at: string | null;
  last_generated_at: string | null;
  next_scheduled_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface AIInsight {
  id: string;
  health_score: number;
  health_status: 'excellent' | 'good' | 'regular' | 'poor';
  summary: string;
  period_start: string;
  period_end: string;
  alerts: InsightItem[];
  opportunities: InsightItem[];
  predictions: Predictions;
  recommendations: string[];
  generated_at: string;
  tokens_used: number;
  model_version: string;
  score_change: number | null;
  is_recent: boolean;
  has_error: boolean;
  error_message?: string;
}

export interface InsightItem {
  type: string;
  severity: 'high' | 'medium' | 'low';
  title: string;
  description: string;
  recommendation: string;
}

export interface Predictions {
  next_month_cash_flow?: number;
  confidence?: 'high' | 'medium' | 'low';
  reasoning?: string;
}

export interface ScoreEvolution {
  date: string;
  score: number;
  status: string;
}

export interface EnableAIInsightsRequest {
  company_type: string;
  business_sector: string;
}

export interface ComparisonData {
  insight1: AIInsight;
  insight2: AIInsight;
  comparison: {
    score_change: number;
    score_change_percentage: number;
    status_changed: boolean;
    period1: { start: string; end: string };
    period2: { start: string; end: string };
    improvements: string[];
    deteriorations: string[];
  };
}

class AIInsightsService {
  /**
   * Get AI insights configuration
   */
  async getConfig(): Promise<AIInsightConfig> {
    return apiClient.get<AIInsightConfig>('/api/ai-insights/insights/config/');
  }

  /**
   * Check if user can enable AI insights
   */
  async canEnable(): Promise<{
    can_enable: boolean;
    has_company: boolean;
    has_company_type: boolean;
    has_business_sector: boolean;
    message: string;
  }> {
    return apiClient.get('/api/ai-insights/insights/can_enable/');
  }

  /**
   * Enable AI insights
   */
  async enable(data: EnableAIInsightsRequest): Promise<{
    message: string;
    config: AIInsightConfig;
  }> {
    return apiClient.post('/api/ai-insights/insights/enable/', data);
  }

  /**
   * Disable AI insights
   */
  async disable(): Promise<{ message: string }> {
    return apiClient.post('/api/ai-insights/insights/disable/');
  }

  /**
   * Force regenerate insight
   */
  async regenerate(): Promise<{ message: string }> {
    return apiClient.post('/api/ai-insights/insights/regenerate/');
  }

  /**
   * Get latest insight
   */
  async getLatest(): Promise<AIInsight> {
    return apiClient.get<AIInsight>('/api/ai-insights/insights/latest/');
  }

  /**
   * Get all insights
   */
  async getAll(): Promise<AIInsight[]> {
    const response = await apiClient.get<{ results: AIInsight[] }>('/api/ai-insights/insights/');
    return response.results;
  }

  /**
   * Get insight by ID
   */
  async getById(id: string): Promise<AIInsight> {
    return apiClient.get<AIInsight>(`/api/ai-insights/insights/${id}/`);
  }

  /**
   * Get insight history (paginated)
   */
  async getHistory(): Promise<AIInsight[]> {
    const response = await apiClient.get<{ results: AIInsight[] }>('/api/ai-insights/insights/history/');
    return response.results;
  }

  /**
   * Get score evolution over time
   */
  async getScoreEvolution(): Promise<ScoreEvolution[]> {
    const response = await apiClient.get<{ evolution: ScoreEvolution[] }>('/api/ai-insights/insights/score_evolution/');
    return response.evolution;
  }

  /**
   * Compare two insights
   */
  async compare(insightId: string, compareWithId?: string): Promise<ComparisonData> {
    const params = compareWithId ? { with: compareWithId } : {};
    return apiClient.get<ComparisonData>(`/api/ai-insights/insights/${insightId}/compare/`, params);
  }

  /**
   * Get health status label
   */
  getHealthStatusLabel(status: string): string {
    const labels: Record<string, string> = {
      excellent: 'Excelente',
      good: 'Bom',
      regular: 'Regular',
      poor: 'Ruim'
    };
    return labels[status] || status;
  }

  /**
   * Get health status color
   */
  getHealthStatusColor(status: string): string {
    const colors: Record<string, string> = {
      excellent: 'text-green-600',
      good: 'text-blue-600',
      regular: 'text-yellow-600',
      poor: 'text-red-600'
    };
    return colors[status] || 'text-gray-600';
  }

  /**
   * Get health status background color
   */
  getHealthStatusBgColor(status: string): string {
    const colors: Record<string, string> = {
      excellent: 'bg-green-100',
      good: 'bg-blue-100',
      regular: 'bg-yellow-100',
      poor: 'bg-red-100'
    };
    return colors[status] || 'bg-gray-100';
  }

  /**
   * Get severity icon
   */
  getSeverityIcon(severity: string): string {
    const icons: Record<string, string> = {
      high: '🔴',
      medium: '🟡',
      low: '🟢'
    };
    return icons[severity] || '⚪';
  }

  /**
   * Get severity color
   */
  getSeverityColor(severity: string): string {
    const colors: Record<string, string> = {
      high: 'text-red-600',
      medium: 'text-yellow-600',
      low: 'text-green-600'
    };
    return colors[severity] || 'text-gray-600';
  }
}

export const aiInsightsService = new AIInsightsService();
