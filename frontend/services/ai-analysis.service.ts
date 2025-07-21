import { apiClient } from '@/lib/api-client';

export interface AIAnalysis {
  id?: number;
  title: string;
  description?: string;
  analysis_type: string;
  analysis_type_display?: string;
  period_start: string;
  period_end: string;
  analysis_config?: any;
  input_parameters?: any;
  filters?: any;
  ai_response?: any;
  insights?: any[];
  recommendations?: any[];
  predictions?: any;
  summary?: any;
  confidence_score?: number;
  health_score?: number;
  risk_score?: number;
  is_processed?: boolean;
  processing_time?: number;
  error_message?: string;
  is_public?: boolean;
  is_favorite?: boolean;
  tags?: string[];
  created_at?: string;
  updated_at?: string;
  created_by_name?: string;
  days_since_created?: number;
  summary_text?: string;
}

export interface AIAnalysisTemplate {
  id?: number;
  name: string;
  description?: string;
  analysis_type: string;
  analysis_type_display?: string;
  template_config?: any;
  prompt_template?: string;
  default_parameters?: any;
  default_filters?: any;
  output_format?: any;
  visualization_config?: any[];
  is_active?: boolean;
  is_public?: boolean;
  created_at?: string;
  updated_at?: string;
  created_by_name?: string;
}

export interface SaveFromInsightsRequest {
  insights_data: any;
  period_start: string;
  period_end: string;
  title?: string;
}

class AIAnalysisService {
  private readonly baseUrl = '/api/reports/ai-analyses';
  private readonly templatesUrl = '/api/reports/ai-templates';

  // AI Analyses CRUD
  async list(params?: {
    analysis_type?: string;
    is_favorite?: boolean;
    is_processed?: boolean;
    search?: string;
    ordering?: string;
    page?: number;
    page_size?: number;
  }) {
    const response = await apiClient.get<{
      results: AIAnalysis[];
      count: number;
      next: string | null;
      previous: string | null;
    }>(`${this.baseUrl}/`, { params });
    return response;
  }

  async get(id: number) {
    const response = await apiClient.get<AIAnalysis>(`${this.baseUrl}/${id}/`);
    return response;
  }

  async create(data: Partial<AIAnalysis>) {
    const response = await apiClient.post<AIAnalysis>(`${this.baseUrl}/`, data);
    return response;
  }

  async update(id: number, data: Partial<AIAnalysis>) {
    const response = await apiClient.patch<AIAnalysis>(`${this.baseUrl}/${id}/`, data);
    return response;
  }

  async delete(id: number) {
    await apiClient.delete(`${this.baseUrl}/${id}/`);
  }

  // Special endpoints
  async saveFromInsights(data: SaveFromInsightsRequest) {
    const response = await apiClient.post<AIAnalysis>(`${this.baseUrl}/save_from_insights/`, data);
    return response;
  }

  async toggleFavorite(id: number) {
    const response = await apiClient.post<{ is_favorite: boolean }>(`${this.baseUrl}/${id}/toggle_favorite/`);
    return response;
  }

  async getFavorites() {
    const response = await apiClient.get<AIAnalysis[]>(`${this.baseUrl}/favorites/`);
    return response;
  }

  async getRecent() {
    const response = await apiClient.get<AIAnalysis[]>(`${this.baseUrl}/recent/`);
    return response;
  }

  // Templates CRUD
  async listTemplates(params?: {
    analysis_type?: string;
    is_active?: boolean;
    is_public?: boolean;
    search?: string;
  }) {
    const response = await apiClient.get<AIAnalysisTemplate[]>(`${this.templatesUrl}/`, { params });
    return response;
  }

  async getTemplate(id: number) {
    const response = await apiClient.get<AIAnalysisTemplate>(`${this.templatesUrl}/${id}/`);
    return response;
  }

  async createTemplate(data: Partial<AIAnalysisTemplate>) {
    const response = await apiClient.post<AIAnalysisTemplate>(`${this.templatesUrl}/`, data);
    return response;
  }

  async updateTemplate(id: number, data: Partial<AIAnalysisTemplate>) {
    const response = await apiClient.patch<AIAnalysisTemplate>(`${this.templatesUrl}/${id}/`, data);
    return response;
  }

  async deleteTemplate(id: number) {
    await apiClient.delete(`${this.templatesUrl}/${id}/`);
  }

  async createAnalysisFromTemplate(templateId: number, period_start: string, period_end: string) {
    const response = await apiClient.post<AIAnalysis>(`${this.templatesUrl}/${templateId}/create_analysis/`, {
      period_start,
      period_end
    });
    return response;
  }
}

export const aiAnalysisService = new AIAnalysisService();