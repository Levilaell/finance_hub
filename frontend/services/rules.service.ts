import { ApiResponse, PaginatedResponse } from '@/types';
import { apiClient } from './api.client';

export interface CategoryRule {
  id: number;
  name: string;
  rule_type: 'keyword' | 'amount_range' | 'counterpart' | 'pattern' | 'ai_prediction';
  conditions: Record<string, any>;
  category: number;
  category_name: string;
  priority: number;
  is_active: boolean;
  confidence_threshold: number;
  match_count: number;
  accuracy_rate: number;
  created_at: string;
  updated_at: string;
  created_by: number;
  created_by_name: string;
}

export interface CreateRuleRequest {
  name: string;
  rule_type: CategoryRule['rule_type'];
  conditions: Record<string, any>;
  category: number;
  priority?: number;
  confidence_threshold?: number;
  is_active?: boolean;
}

export interface TestRuleResponse {
  matches_found: number;
  total_tested: number;
  match_rate: number;
  matches: Array<{
    transaction_id: number;
    description: string;
    amount: number;
    current_category: string | null;
  }>;
}

export interface ApplyRuleResponse {
  status: string;
  results: {
    processed: number;
    categorized: number;
    errors: number;
  };
}

export interface RuleSuggestion {
  type: string;
  category: string;
  keywords?: string[];
  confidence: number;
  sample_transactions: number;
}

export interface RuleSuggestionsResponse {
  suggestions: RuleSuggestion[];
  total_suggestions: number;
}

class RulesService {
  private baseUrl = '/api/categories';

  async getRules(): Promise<ApiResponse<CategoryRule[]>> {
    const response = await apiClient.get(`${this.baseUrl}/rules/`);
    return response.data;
  }

  async createRule(data: CreateRuleRequest): Promise<ApiResponse<CategoryRule>> {
    const response = await apiClient.post(`${this.baseUrl}/rules/`, data);
    return response.data;
  }

  async updateRule(id: number, data: Partial<CreateRuleRequest>): Promise<ApiResponse<CategoryRule>> {
    const response = await apiClient.put(`${this.baseUrl}/rules/${id}/`, data);
    return response.data;
  }

  async deleteRule(id: number): Promise<ApiResponse<void>> {
    const response = await apiClient.delete(`${this.baseUrl}/rules/${id}/`);
    return response.data;
  }

  async testRule(id: number, limit: number = 100): Promise<ApiResponse<TestRuleResponse>> {
    const response = await apiClient.post(`${this.baseUrl}/rules/${id}/test_rule/`, { limit });
    return response.data;
  }

  async applyRuleToExisting(id: number, limit: number = 1000): Promise<ApiResponse<ApplyRuleResponse>> {
    const response = await apiClient.post(`${this.baseUrl}/rules/${id}/apply_to_existing/`, { limit });
    return response.data;
  }

  async getRuleSuggestions(): Promise<ApiResponse<RuleSuggestionsResponse>> {
    const response = await apiClient.get(`${this.baseUrl}/rule-suggestions/`);
    return response.data;
  }

  async createRuleFromSuggestion(suggestion: RuleSuggestion): Promise<ApiResponse<{ rule_id: number; message: string }>> {
    const response = await apiClient.post(`${this.baseUrl}/rule-suggestions/`, suggestion);
    return response.data;
  }

  // Helper methods for creating specific rule types
  createKeywordRule(name: string, category: number, keywords: string[], priority: number = 0) {
    return this.createRule({
      name,
      rule_type: 'keyword',
      category,
      priority,
      conditions: {
        keywords: keywords.map(k => k.toLowerCase()),
        match_type: 'contains'
      }
    });
  }

  createAmountRule(name: string, category: number, minAmount?: number, maxAmount?: number, priority: number = 0) {
    return this.createRule({
      name,
      rule_type: 'amount_range',
      category,
      priority,
      conditions: {
        min_amount: minAmount,
        max_amount: maxAmount
      }
    });
  }

  createCounterpartRule(name: string, category: number, counterparts: string[], priority: number = 0) {
    return this.createRule({
      name,
      rule_type: 'counterpart',
      category,
      priority,
      conditions: {
        counterparts: counterparts.map(c => c.toLowerCase()),
        match_type: 'exact'
      }
    });
  }

  createPatternRule(name: string, category: number, pattern: string, priority: number = 0) {
    return this.createRule({
      name,
      rule_type: 'pattern',
      category,
      priority,
      conditions: {
        regex_pattern: pattern,
        flags: 'i'
      }
    });
  }
}

export const rulesService = new RulesService();