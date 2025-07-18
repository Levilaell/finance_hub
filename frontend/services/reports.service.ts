// frontend/services/reports.service.ts

import { api } from '@/lib/api';
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
    const response = await api.get('/api/reports/reports/', { params });
    return response.data;
  },

  // Generate a new report - CORRIGIDO
  async generateReport(type: string, parameters: ReportParameters, format: 'pdf' | 'xlsx' | 'csv' | 'json' = 'pdf') {
    // Validar parâmetros antes de enviar
    const errors = this.validateReportParameters(parameters);
    if (errors.length > 0) {
      throw new Error(errors.join(', '));
    }

    // Formatar dados corretamente para o backend
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
      filters: parameters.filters || {},
    };

    try {
      const response = await api.post('/api/reports/reports/', reportData);
      return response.data;
    } catch (error: any) {
      console.error('Generate report error:', error.response?.data);
      throw error;
    }
  },

  // Download report file
  async downloadReport(reportId: string) {
    const response = await api.get(`/api/reports/reports/${reportId}/download/`, {
      responseType: 'blob',
    });
    return response.data;
  },

  // Get report summary with statistics
  async getReportSummary() {
    const response = await api.get('/api/reports/reports/summary/');
    return response.data;
  },

  // Scheduled Reports
  async getScheduledReports(params?: {
    is_active?: boolean;
    report_type?: string;
    frequency?: string;
  }) {
    const response = await api.get('/api/reports/schedules/', { params });
    return response.data;
  },

  async createScheduledReport(data: CreateScheduledReportData) {
    try {
      const response = await api.post('/api/reports/schedules/', data);
      return response.data;
    } catch (error: any) {
      console.error('Create scheduled report error:', error.response?.data);
      throw error;
    }
  },

  async updateScheduledReport(id: string, data: Partial<CreateScheduledReportData>) {
    const response = await api.patch(`/reports/schedules/${id}/`, data);
    return response.data;
  },

  async toggleScheduledReport(id: string) {
    const response = await api.post(`/api/reports/schedules/${id}/toggle_active/`);
    return response.data;
  },

  async runScheduledReportNow(id: string) {
    const response = await api.post(`/api/reports/schedules/${id}/run_now/`);
    return response.data;
  },

  async deleteScheduledReport(id: string) {
    const response = await api.delete(`/api/reports/schedules/${id}/`);
    return response.data;
  },

  // Quick Reports
  async getQuickReports() {
    const response = await api.get('/api/reports/quick/');
    return response.data;
  },

  async generateQuickReport(reportId: string) {
    const response = await api.post('/api/reports/quick/', { report_id: reportId });
    return response.data;
  },

  // Analytics
  async getAnalytics(period: number = 30) {
    const response = await api.get('/api/reports/analytics/', {
      params: { period }
    });
    return response.data;
  },

  // Dashboard data
  async getDashboardStats() {
    const response = await api.get('/api/reports/dashboard/stats/');
    return response.data;
  },

  async getCashFlowData(params: {
    start_date: Date;
    end_date: Date;
  }) {
    const response = await api.get('/api/reports/dashboard/cash-flow/', {
      params: {
        start_date: params.start_date.toISOString().split('T')[0],
        end_date: params.end_date.toISOString().split('T')[0],
      }
    });
    return response.data;
  },

  async getCategorySpending(params: {
    start_date: Date;
    end_date: Date;
    type?: 'expense' | 'income';
  }) {
    const response = await api.get('/api/reports/dashboard/category-spending/', {
      params: {
        start_date: params.start_date.toISOString().split('T')[0],
        end_date: params.end_date.toISOString().split('T')[0],
        type: params.type || 'expense',
      }
    });
    return response.data;
  },

  async getIncomeVsExpenses(params: {
    start_date: Date;
    end_date: Date;
  }) {
    const response = await api.get('/api/reports/dashboard/income-vs-expenses/', {
      params: {
        start_date: params.start_date.toISOString().split('T')[0],
        end_date: params.end_date.toISOString().split('T')[0],
      }
    });
    return response.data;
  },

  // AI Insights with enhanced error handling
  async getAIInsights(params: {
    start_date: Date;
    end_date: Date;
    force_refresh?: boolean;
    type?: 'comprehensive' | 'quick' | 'custom';
  }): Promise<AIInsights> {
    try {
      const response = await api.get('/api/reports/ai-insights/', {
        params: {
          start_date: params.start_date.toISOString().split('T')[0],
          end_date: params.end_date.toISOString().split('T')[0],
          force_refresh: params.force_refresh || false,
          type: params.type || 'comprehensive',
        },
        timeout: 30000, // 30 seconds timeout for AI processing
      });
      return response.data;
    } catch (error: any) {
      // Se falhar, retornar insights básicos
      if (error.response?.status === 403) {
        throw new Error('AI insights not available in your plan');
      }
      
      // Log do erro mas não falhar completamente
      console.error('AI Insights error:', error);
      
      // Retornar estrutura básica para não quebrar a UI
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

  // Ask AI questions
  async askAI(question: string, context?: Record<string, any>) {
    const response = await api.post('/api/reports/ai-insights/ask_ai/', {
      question,
      context: context || {},
    });
    return response.data;
  },

  // Get AI insights history
  async getAIInsightsHistory(period: number = 30) {
    const response = await api.get('/api/reports/ai-insights/insights_history/', {
      params: { period }
    });
    return response.data;
  },

  // Report templates
  async getReportTemplates() {
    const response = await api.get('/api/reports/templates/');
    return response.data;
  },

  async createReportTemplate(data: {
    name: string;
    description?: string;
    report_type: string;
    template_config: Record<string, any>;
    charts?: any[];
    default_parameters?: Record<string, any>;
    default_filters?: Record<string, any>;
    is_public?: boolean;
  }) {
    const response = await api.post('/api/reports/templates/', data);
    return response.data;
  },

  // Utility function to validate report parameters - MELHORADO
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
          
          // Validar período máximo (1 ano)
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
  },

  // Format report data for export
  formatReportData(data: any[], format: 'csv' | 'json'): string | object {
    if (format === 'json') {
      return JSON.stringify(data, null, 2);
    }
    
    // CSV format
    if (data.length === 0) return '';
    
    const headers = Object.keys(data[0]);
    const csvContent = [
      headers.join(','),
      ...data.map(row => 
        headers.map(header => {
          const value = row[header];
          // Escape quotes and wrap in quotes if contains comma
          if (typeof value === 'string' && (value.includes(',') || value.includes('"'))) {
            return `"${value.replace(/"/g, '""')}"`;
          }
          return value;
        }).join(',')
      )
    ].join('\n');
    
    return csvContent;
  },
};