// frontend/services/reports.service.ts

import apiClient from '@/lib/api-client';
import {
  Report,
  ReportParameters,
  ScheduledReport,
  AIInsights
} from '@/types';

export interface GenerateReportParams {
  report_type: string;
  title: string;
  description?: string;
  period_start: string;
  period_end: string;
  file_format: 'pdf' | 'xlsx' | 'csv' | 'json';
  parameters?: Record<string, any>;
  filters?: Record<string, any>;
}

export interface CreateScheduledReportData {
  name: string;
  report_type: string;
  frequency: string;
  email_recipients: string[];
  file_format: string;
  send_email?: boolean;
  parameters?: Record<string, any>;
  filters?: Record<string, any>;
}

export const reportsService = {
  // Get all reports
  async getReports(params?: {
    page?: number;
    limit?: number;
    report_type?: string;
    is_generated?: boolean;
  }) {
    try {
      const response = await apiClient.get<any>('/api/reports/reports/', { params });
      return response;
    } catch (error: any) {
      console.error('❌ Erro em reportsService.getReports:', {
        message: error.message,
        status: error.response?.status,
        data: error.response?.data,
        url: error.config?.url,
        timestamp: new Date().toISOString()
      });
      throw error;
    }
  },

  // Generate a new report
  async generateReport(type: string, parameters: ReportParameters, format: 'pdf' | 'xlsx' | 'csv' | 'json' = 'pdf') {
    const reportData: GenerateReportParams = {
      report_type: type,
      title: parameters.title || `${type} - ${parameters.start_date} to ${parameters.end_date}`,
      description: parameters.description || '',
      period_start: parameters.start_date!,
      period_end: parameters.end_date!,
      file_format: format,
      parameters: {
        account_ids: parameters.account_ids || [],
        category_ids: parameters.category_ids || [],
        include_charts: true,
        detailed_breakdown: true,
      },
      filters: parameters.filters || { generated_via: 'frontend_service' },
    };

    try {
      const response = await apiClient.post<any>('/api/reports/reports/', reportData);
      return response.data;
    } catch (error: any) {
      console.error('❌ Erro na requisição POST:', error);
      throw error;
    }
  },

  // Get report status
  async getReportStatus(reportId: string): Promise<Report> {
    const response = await apiClient.get<any>(`/api/reports/reports/${reportId}/`);
    return response.data;
  },

  // Download report file directly
  async downloadReport(reportId: string): Promise<Blob> {
    try {
      const token = localStorage.getItem('access_token');

      if (!token) {
        throw new Error('Token de autenticação não encontrado');
      }

      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/reports/reports/${reportId}/download/`, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        const errorData = await response.text();
        throw new Error(`HTTP error! status: ${response.status}, message: ${errorData}`);
      }

      const blob = await response.blob();
      return blob;
    } catch (error: any) {
      console.error('❌ Download error:', error);
      throw error;
    }
  },

  // AI Insights with enhanced error handling
  async getAIInsights(params: {
    start_date: Date;
    end_date: Date;
    force_refresh?: boolean;
    type?: 'comprehensive' | 'quick' | 'custom';
    context?: any;
  }): Promise<AIInsights | null> {
    try {
      const queryParams: any = {
        start_date: params.start_date.toISOString().split('T')[0],
        end_date: params.end_date.toISOString().split('T')[0],
        force_refresh: params.force_refresh || false,
        type: params.type || 'comprehensive',
      };

      if (params.context) {
        queryParams.context = JSON.stringify(params.context);
      }

      const response = await apiClient.get<any>('/api/reports/ai-insights/', {
        params: queryParams,
        timeout: 30000,
      });
      return response.data;
    } catch (error: any) {
      if (error.response?.status === 403) {
        return null;
      }

      console.error('AI Insights error:', error);

      return {
        insights: [],
        predictions: {
          next_month_income: 0,
          next_month_expenses: 0,
          projected_savings: 0,
        },
        recommendations: [],
        key_metrics: {
          health_score: 0,
          efficiency_score: 0,
          growth_potential: 0,
        },
        ai_generated: false,
        fallback_mode: true,
        error: error.message,
      };
    }
  },

  // Analytics methods
  async getCashFlowData(params: {
    start_date: Date;
    end_date: Date;
  }) {
    const queryParams = {
      start_date: params.start_date.toISOString().split('T')[0],
      end_date: params.end_date.toISOString().split('T')[0],
    };
    const data = await apiClient.get<any>('/api/reports/dashboard/cash-flow/', queryParams);
    return data;
  },

  async getCategorySpending(params: {
    start_date: Date;
    end_date: Date;
    type?: 'expense' | 'income';
  }) {
    const queryParams = {
      start_date: params.start_date.toISOString().split('T')[0],
      end_date: params.end_date.toISOString().split('T')[0],
      type: params.type || 'expense',
    };
    const data = await apiClient.get<any>('/api/reports/dashboard/category-spending/', queryParams);
    return data;
  },

  async getIncomeVsExpenses(params: {
    start_date: Date;
    end_date: Date;
  }) {
    const queryParams = {
      start_date: params.start_date.toISOString().split('T')[0],
      end_date: params.end_date.toISOString().split('T')[0],
    };
    const data = await apiClient.get<any>('/api/reports/dashboard/income-vs-expenses/', queryParams);
    return data;
  },

  async getAnalytics(period: number = 30) {
    const response = await apiClient.get<any>('/api/reports/analytics/', {
      params: { period }
    });
    return response.data;
  },

  async getReportTemplates() {
    const response = await apiClient.get<any>('/api/reports/templates/');
    if (response.data && typeof response.data === 'object' && 'results' in response.data) {
      return response.data.results || [];
    }
    return response.data || [];
  },

  // Utility function to validate report parameters
  validateReportParameters(params: ReportParameters): string[] {
    const errors: string[] = [];

    if (!params.start_date) {
      errors.push('Data inicial é obrigatória');
    }

    if (!params.end_date) {
      errors.push('Data final é obrigatória');
    }

    if (params.start_date && params.end_date) {
      try {
        const start = new Date(params.start_date);
        const end = new Date(params.end_date);

        if (isNaN(start.getTime()) || isNaN(end.getTime())) {
          errors.push('Formato de data inválido');
        } else {
          if (start > end) {
            errors.push('Data inicial deve ser anterior à data final');
          }

          if (end > new Date()) {
            errors.push('Data final não pode ser no futuro');
          }

          const diffTime = Math.abs(end.getTime() - start.getTime());
          const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
          if (diffDays > 365) {
            errors.push('Período máximo permitido é de 1 ano');
          }
        }
      } catch (e) {
        errors.push('Erro ao validar datas');
      }
    }

    return errors;
  }
};