// import { apiClient } from '@/lib/api-client';

export interface PerformanceMetrics {
  total_categories: number;
  average_accuracy: number;
  average_precision: number;
  average_recall: number;
  average_f1_score: number;
  category_breakdown: CategoryPerformanceMetric[];
  summary: {
    total_predictions: number;
    correct_predictions: number;
    false_positives: number;
    false_negatives: number;
    overall_accuracy: number;
  };
  period_days: number;
}

export interface CategoryPerformanceMetric {
  category: string;
  category_slug: string;
  category_type: string;
  total_predictions: number;
  correct_predictions: number;
  false_positives: number;
  false_negatives: number;
  accuracy: number;
  precision: number;
  recall: number;
  f1_score: number;
  needs_improvement: boolean;
}

export interface RulePerformance {
  total_rules: number;
  total_rule_applications: number;
  correct_rule_applications: number;
  rule_accuracy: number;
  rule_breakdown: RulePerformanceMetric[];
  period_days: number;
}

export interface RulePerformanceMetric {
  rule_id: number;
  rule_name: string;
  rule_type: string;
  category: string;
  total_applications: number;
  correct_applications: number;
  accuracy: number;
  match_count: number;
  priority: number;
  confidence_threshold: number;
  needs_review: boolean;
}

export interface AccuracyMetrics {
  total_categorizations: number;
  accuracy: number;
  ai_accuracy: number;
  rule_accuracy: number;
  method_breakdown: {
    [method: string]: {
      total: number;
      correct: number;
      accuracy: number;
    };
  };
  performance_summary: {
    total_predictions: number;
    correct_predictions: number;
    false_positives: number;
    false_negatives: number;
    precision: number;
    recall: number;
  };
  period_days: number;
}

export interface CategoryInsight {
  category: string;
  icon: string;
  type: string;
  transaction_count: number;
  avg_confidence: number;
  accuracy: number;
  needs_attention: boolean;
}

export interface ImprovementSuggestion {
  type: string;
  category?: string;
  current_accuracy?: number;
  transaction_count?: number;
  suggestion: string;
  priority: 'high' | 'medium' | 'low';
}

export interface CategorizationActivity {
  id: number;
  transaction: number;
  method: string;
  suggested_category: number;
  confidence_score: number;
  processing_time_ms: number;
  was_accepted: boolean;
  created_at: string;
}

export interface SummaryMetrics {
  overall_accuracy: number;
  auto_categorized: number;
  manual_reviews: number;
  total_categorizations: number;
}

export interface AnalyticsResponse {
  accuracy_metrics: AccuracyMetrics;
  ai_performance: PerformanceMetrics;
  rule_performance: RulePerformance;
  category_insights: CategoryInsight[];
  improvement_suggestions: ImprovementSuggestion[];
  recent_activity: CategorizationActivity[];
  summary_metrics: SummaryMetrics;
}

class AnalyticsService {
  // private baseUrl = '/api/categories';

  async getAnalytics(periodDays: number = 30): Promise<AnalyticsResponse> {
    // Endpoint removido - retornar dados vazios
    return {
      accuracy_metrics: {
        total_categorizations: 0,
        accuracy: 0,
        ai_accuracy: 0,
        rule_accuracy: 0,
        method_breakdown: {},
        performance_summary: {
          total_predictions: 0,
          correct_predictions: 0,
          false_positives: 0,
          false_negatives: 0,
          precision: 0,
          recall: 0
        },
        period_days: periodDays
      },
      ai_performance: {
        total_categories: 0,
        average_accuracy: 0,
        average_precision: 0,
        average_recall: 0,
        average_f1_score: 0,
        category_breakdown: [],
        summary: {
          total_predictions: 0,
          correct_predictions: 0,
          false_positives: 0,
          false_negatives: 0,
          overall_accuracy: 0
        },
        period_days: periodDays
      },
      rule_performance: {
        total_rules: 0,
        total_rule_applications: 0,
        correct_rule_applications: 0,
        rule_accuracy: 0,
        rule_breakdown: [],
        period_days: periodDays
      },
      category_insights: [],
      improvement_suggestions: [],
      recent_activity: [],
      summary_metrics: {
        overall_accuracy: 0,
        auto_categorized: 0,
        manual_reviews: 0,
        total_categorizations: 0
      }
    };
  }

  async getPerformanceMetrics(periodDays: number = 30): Promise<PerformanceMetrics> {
    const response = await this.getAnalytics(periodDays);
    return response.ai_performance;
  }

  async getRulePerformance(periodDays: number = 30): Promise<RulePerformance> {
    const response = await this.getAnalytics(periodDays);
    return response.rule_performance;
  }

  async getSummaryMetrics(periodDays: number = 30): Promise<SummaryMetrics> {
    const response = await this.getAnalytics(periodDays);
    return response.summary_metrics;
  }

  async getCategoryInsights(periodDays: number = 30): Promise<CategoryInsight[]> {
    const response = await this.getAnalytics(periodDays);
    return response.category_insights;
  }

  async getImprovementSuggestions(periodDays: number = 30): Promise<ImprovementSuggestion[]> {
    const response = await this.getAnalytics(periodDays);
    return response.improvement_suggestions;
  }

  async getRecentActivity(periodDays: number = 30): Promise<CategorizationActivity[]> {
    const response = await this.getAnalytics(periodDays);
    return response.recent_activity;
  }
}

export const analyticsService = new AnalyticsService();