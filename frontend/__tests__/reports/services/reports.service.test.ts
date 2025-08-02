/**
 * @jest-environment jsdom
 */
import { jest } from '@jest/globals';
import { reportsService } from '@/services/reports.service';
import { api } from '@/lib/api';
import type { ReportParameters } from '@/types';

// Mock the api client
jest.mock('@/lib/api', () => ({
  api: {
    get: jest.fn(),
    post: jest.fn(),
    put: jest.fn(),
    patch: jest.fn(),
    delete: jest.fn(),
  }
}));
const mockApi = require('@/lib/api').api as jest.Mocked<typeof import('@/lib/api').api>;

// Mock console.error to avoid noise in tests
const originalConsoleError = console.error;
beforeAll(() => {
  console.error = jest.fn();
});

afterAll(() => {
  console.error = originalConsoleError;
});

describe('reportsService', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('getReports', () => {
    const mockReportsResponse = {
      count: 2,
      results: [
        {
          id: '1',
          title: 'Monthly Report',
          report_type: 'monthly_summary',
          is_generated: true,
          created_at: '2024-01-15T10:30:00Z'
        },
        {
          id: '2',
          title: 'Cash Flow Report',
          report_type: 'cash_flow',
          is_generated: false,
          created_at: '2024-01-16T14:20:00Z'
        }
      ]
    };

    it('fetches reports successfully', async () => {
      mockApi.get.mockResolvedValue({ data: mockReportsResponse });

      const result = await reportsService.getReports();

      expect(mockApi.get).toHaveBeenCalledWith('/api/reports/reports/', { params: undefined });
      expect(result).toEqual(mockReportsResponse);
    });

    it('fetches reports with parameters', async () => {
      mockApi.get.mockResolvedValue({ data: mockReportsResponse });

      const params = {
        page: 2,
        limit: 10,
        report_type: 'monthly_summary',
        is_generated: true
      };

      const result = await reportsService.getReports(params);

      expect(mockApi.get).toHaveBeenCalledWith('/api/reports/reports/', { params });
      expect(result).toEqual(mockReportsResponse);
    });

    it('handles API errors', async () => {
      const error = new Error('Network error');
      mockApi.get.mockRejectedValue(error);

      await expect(reportsService.getReports()).rejects.toThrow('Network error');
    });
  });

  describe('generateReport', () => {
    const mockReportResponse = {
      id: 'new-report-id',
      title: 'Generated Report',
      report_type: 'monthly_summary',
      is_generated: false,
      status: 'processing'
    };

    it('generates report successfully with valid parameters', async () => {
      mockApi.post.mockResolvedValue({ data: mockReportResponse });

      const parameters: ReportParameters = {
        start_date: '2024-01-01',
        end_date: '2024-01-31',
        title: 'Test Monthly Report',
        account_ids: ['1', '2'],
        category_ids: ['3', '4']
      };

      const result = await reportsService.generateReport('monthly_summary', parameters, 'pdf');

      expect(mockApi.post).toHaveBeenCalledWith('/api/reports/reports/', {
        report_type: 'monthly_summary',
        title: 'Test Monthly Report',
        description: '',
        period_start: '2024-01-01',
        period_end: '2024-01-31',
        file_format: 'pdf',
        parameters: {
          account_ids: ['1', '2'],
          category_ids: ['3', '4'],
          include_charts: true,
          detailed_breakdown: true
        },
        filters: {}
      });

      expect(result).toEqual(mockReportResponse);
    });

    it('generates report with default title when not provided', async () => {
      mockApi.post.mockResolvedValue({ data: mockReportResponse });

      const parameters: ReportParameters = {
        start_date: '2024-01-01',
        end_date: '2024-01-31'
      };

      await reportsService.generateReport('cash_flow', parameters, 'xlsx');

      expect(mockApi.post).toHaveBeenCalledWith('/api/reports/reports/', 
        expect.objectContaining({
          title: 'cash_flow - 2024-01-01 to 2024-01-31'
        })
      );
    });

    it('validates parameters before sending request', async () => {
      const invalidParameters: ReportParameters = {
        start_date: '2024-02-01',
        end_date: '2024-01-01' // End before start
      };

      await expect(
        reportsService.generateReport('monthly_summary', invalidParameters)
      ).rejects.toThrow('Data inicial deve ser anterior à data final');

      expect(mockApi.post).not.toHaveBeenCalled();
    });

    it('handles API error with detailed logging', async () => {
      const apiError = {
        response: {
          data: {
            detail: 'Insufficient data for report generation',
            errors: ['No transactions found in period']
          }
        }
      };
      mockApi.post.mockRejectedValue(apiError);

      const parameters: ReportParameters = {
        start_date: '2024-01-01',
        end_date: '2024-01-31'
      };

      await expect(
        reportsService.generateReport('monthly_summary', parameters)
      ).rejects.toEqual(apiError);

      expect(console.error).toHaveBeenCalledWith('Generate report error:', apiError.response.data);
    });
  });

  describe('getReportStatus', () => {
    const mockStatusResponse = {
      id: 'report-123',
      is_generated: true,
      error_message: null,
      status: 'completed'
    };

    it('fetches report status successfully', async () => {
      mockApi.get.mockResolvedValue({ data: mockStatusResponse });

      const result = await reportsService.getReportStatus('report-123');

      expect(mockApi.get).toHaveBeenCalledWith('/api/reports/reports/report-123/');
      expect(result).toEqual(mockStatusResponse);
    });

    it('handles non-existent report', async () => {
      const error = { response: { status: 404 } };
      mockApi.get.mockRejectedValue(error);

      await expect(reportsService.getReportStatus('non-existent')).rejects.toEqual(error);
    });
  });

  describe('downloadReport', () => {
    const mockDownloadUrlResponse = {
      download_url: '/api/reports/secure-download/signed-url-123/'
    };

    const mockBlobData = new Blob(['PDF content'], { type: 'application/pdf' });

    it('downloads report successfully using signed URL', async () => {
      mockApi.get
        .mockResolvedValueOnce({ data: mockDownloadUrlResponse })
        .mockResolvedValueOnce({ data: mockBlobData });

      const result = await reportsService.downloadReport('report-123');

      expect(mockApi.get).toHaveBeenCalledTimes(2);
      expect(mockApi.get).toHaveBeenNthCalledWith(1, '/api/reports/reports/report-123/download/');
      expect(mockApi.get).toHaveBeenNthCalledWith(2, mockDownloadUrlResponse.download_url, {
        responseType: 'blob'
      });
      expect(result).toEqual(mockBlobData);
    });

    it('handles download URL generation failure', async () => {
      const error = { response: { status: 400, data: { detail: 'Report not ready' } } };
      mockApi.get.mockRejectedValue(error);

      await expect(reportsService.downloadReport('report-123')).rejects.toEqual(error);
    });
  });

  describe('regenerateReport', () => {
    const mockRegenerateResponse = {
      message: 'Report regeneration started',
      report_id: 123
    };

    it('regenerates report successfully', async () => {
      mockApi.post.mockResolvedValue({ data: mockRegenerateResponse });

      const result = await reportsService.regenerateReport('report-123');

      expect(mockApi.post).toHaveBeenCalledWith('/api/reports/reports/report-123/regenerate/');
      expect(result).toEqual(mockRegenerateResponse);
    });

    it('handles regeneration conflicts', async () => {
      const error = { response: { status: 409, data: { detail: 'Report already generating' } } };
      mockApi.post.mockRejectedValue(error);

      await expect(reportsService.regenerateReport('report-123')).rejects.toEqual(error);
    });
  });

  describe('pollReportStatus', () => {
    it('polls until report is generated', async () => {
      const progressCallback = jest.fn();
      
      // Mock progressive status updates
      mockApi.get
        .mockResolvedValueOnce({ data: { id: 'report-123', is_generated: false, status: 'processing' } })
        .mockResolvedValueOnce({ data: { id: 'report-123', is_generated: false, status: 'generating' } })
        .mockResolvedValueOnce({ data: { id: 'report-123', is_generated: true, status: 'completed' } });

      const result = await reportsService.pollReportStatus(
        'report-123',
        progressCallback,
        3, // maxAttempts
        100 // interval
      );

      expect(mockApi.get).toHaveBeenCalledTimes(3);
      expect(progressCallback).toHaveBeenCalledTimes(3);
      expect(progressCallback).toHaveBeenNthCalledWith(1, 'processing');
      expect(progressCallback).toHaveBeenNthCalledWith(2, 'generating');
      expect(progressCallback).toHaveBeenNthCalledWith(3, 'completed');
      expect(result.is_generated).toBe(true);
    });

    it('throws error when report has error message', async () => {
      mockApi.get.mockResolvedValue({ 
        data: { 
          id: 'report-123', 
          is_generated: false, 
          error_message: 'Generation failed due to data issues' 
        } 
      });

      await expect(
        reportsService.pollReportStatus('report-123', undefined, 1, 100)
      ).rejects.toThrow('Generation failed due to data issues');
    });

    it('throws timeout error when max attempts reached', async () => {
      mockApi.get.mockResolvedValue({ 
        data: { 
          id: 'report-123', 
          is_generated: false, 
          status: 'processing' 
        } 
      });

      await expect(
        reportsService.pollReportStatus('report-123', undefined, 2, 50)
      ).rejects.toThrow('Report generation timed out');

      expect(mockApi.get).toHaveBeenCalledTimes(2);
    });
  });

  describe('getReportSummary', () => {
    const mockSummaryResponse = {
      total_reports: 10,
      reports_generated: 8,
      reports_pending: 2,
      reports_failed: 0
    };

    it('fetches report summary successfully', async () => {
      mockApi.get.mockResolvedValue({ data: mockSummaryResponse });

      const result = await reportsService.getReportSummary();

      expect(mockApi.get).toHaveBeenCalledWith('/api/reports/reports/summary/');
      expect(result).toEqual(mockSummaryResponse);
    });
  });

  describe('Scheduled Reports', () => {
    const mockScheduledReportsResponse = {
      count: 2,
      results: [
        {
          id: '1',
          name: 'Weekly Revenue',
          report_type: 'weekly_summary',
          frequency: 'weekly',
          is_active: true
        },
        {
          id: '2',
          name: 'Monthly Analysis',
          report_type: 'monthly_summary',
          frequency: 'monthly',
          is_active: false
        }
      ]
    };

    it('fetches scheduled reports', async () => {
      mockApi.get.mockResolvedValue({ data: mockScheduledReportsResponse });

      const result = await reportsService.getScheduledReports();

      expect(mockApi.get).toHaveBeenCalledWith('/api/reports/schedules/', { params: undefined });
      expect(result).toEqual(mockScheduledReportsResponse);
    });

    it('fetches scheduled reports with filters', async () => {
      mockApi.get.mockResolvedValue({ data: mockScheduledReportsResponse });

      const params = {
        is_active: true,
        report_type: 'weekly_summary',
        frequency: 'weekly'
      };

      const result = await reportsService.getScheduledReports(params);

      expect(mockApi.get).toHaveBeenCalledWith('/api/reports/schedules/', { params });
      expect(result).toEqual(mockScheduledReportsResponse);
    });

    it('creates scheduled report', async () => {
      const mockCreateResponse = {
        id: 'new-schedule-id',
        name: 'Daily Revenue',
        report_type: 'daily_summary',
        frequency: 'daily'
      };

      mockApi.post.mockResolvedValue({ data: mockCreateResponse });

      const data = {
        name: 'Daily Revenue',
        report_type: 'daily_summary',
        frequency: 'daily',
        email_recipients: ['manager@company.com'],
        file_format: 'pdf'
      };

      const result = await reportsService.createScheduledReport(data);

      expect(mockApi.post).toHaveBeenCalledWith('/api/reports/schedules/', data);
      expect(result).toEqual(mockCreateResponse);
    });

    it('handles scheduled report creation error', async () => {
      const apiError = {
        response: {
          data: {
            detail: 'Invalid frequency',
            errors: { frequency: ['Invalid choice'] }
          }
        }
      };
      mockApi.post.mockRejectedValue(apiError);

      const data = {
        name: 'Invalid Schedule',
        report_type: 'monthly_summary',
        frequency: 'invalid_frequency',
        email_recipients: ['test@company.com'],
        file_format: 'pdf'
      };

      await expect(reportsService.createScheduledReport(data)).rejects.toEqual(apiError);
      expect(console.error).toHaveBeenCalledWith('Create scheduled report error:', apiError.response.data);
    });

    it('toggles scheduled report status', async () => {
      const mockToggleResponse = {
        id: 'schedule-123',
        is_active: false
      };

      mockApi.post.mockResolvedValue({ data: mockToggleResponse });

      const result = await reportsService.toggleScheduledReport('schedule-123');

      expect(mockApi.post).toHaveBeenCalledWith('/api/reports/schedules/schedule-123/toggle_active/');
      expect(result).toEqual(mockToggleResponse);
    });

    it('runs scheduled report now', async () => {
      const mockRunResponse = {
        message: 'Report generation started',
        task_id: 'task-456'
      };

      mockApi.post.mockResolvedValue({ data: mockRunResponse });

      const result = await reportsService.runScheduledReportNow('schedule-123');

      expect(mockApi.post).toHaveBeenCalledWith('/api/reports/schedules/schedule-123/run_now/');
      expect(result).toEqual(mockRunResponse);
    });
  });

  describe('Analytics and Dashboard', () => {
    const mockAnalyticsResponse = {
      total_income: 8000.00,
      total_expenses: 3000.00,
      net_result: 5000.00,
      transaction_count: 45
    };

    it('fetches analytics data', async () => {
      mockApi.get.mockResolvedValue({ data: mockAnalyticsResponse });

      const result = await reportsService.getAnalytics(30);

      expect(mockApi.get).toHaveBeenCalledWith('/api/reports/analytics/', {
        params: { period: 30 }
      });
      expect(result).toEqual(mockAnalyticsResponse);
    });

    it('fetches dashboard stats', async () => {
      const mockStatsResponse = {
        total_balance: 15000.00,
        income_this_month: 5000.00,
        expenses_this_month: 2000.00,
        net_income: 3000.00
      };

      mockApi.get.mockResolvedValue({ data: mockStatsResponse });

      const result = await reportsService.getDashboardStats();

      expect(mockApi.get).toHaveBeenCalledWith('/api/reports/dashboard/stats/');
      expect(result).toEqual(mockStatsResponse);
    });

    it('fetches cash flow data with date parameters', async () => {
      const mockCashFlowResponse = {
        data: [
          { date: '2024-01-01', income: 1000, expenses: 500 },
          { date: '2024-01-02', income: 1200, expenses: 600 }
        ]
      };

      mockApi.get.mockResolvedValue({ data: mockCashFlowResponse });

      const params = {
        start_date: new Date('2024-01-01'),
        end_date: new Date('2024-01-31')
      };

      const result = await reportsService.getCashFlowData(params);

      expect(mockApi.get).toHaveBeenCalledWith('/api/reports/dashboard/cash-flow/', {
        params: {
          start_date: '2024-01-01',
          end_date: '2024-01-31'
        }
      });
      expect(result).toEqual(mockCashFlowResponse);
    });

    it('fetches category spending data', async () => {
      const mockCategoryResponse = {
        data: [
          { category: 'Food', amount: 800, count: 15 },
          { category: 'Transport', amount: 400, count: 8 }
        ]
      };

      mockApi.get.mockResolvedValue({ data: mockCategoryResponse });

      const params = {
        start_date: new Date('2024-01-01'),
        end_date: new Date('2024-01-31'),
        type: 'expense' as const
      };

      const result = await reportsService.getCategorySpending(params);

      expect(mockApi.get).toHaveBeenCalledWith('/api/reports/dashboard/category-spending/', {
        params: {
          start_date: '2024-01-01',
          end_date: '2024-01-31',
          type: 'expense'
        }
      });
      expect(result).toEqual(mockCategoryResponse);
    });
  });

  describe('AI Insights', () => {
    const mockAIInsightsResponse = {
      insights: [
        {
          type: 'success',
          title: 'Strong Financial Health',
          description: 'Your expenses are well controlled.'
        }
      ],
      predictions: {
        next_month_income: 5000,
        next_month_expenses: 2800,
        projected_savings: 2200
      },
      recommendations: [
        {
          title: 'Optimize Food Spending',
          description: 'Consider meal planning to reduce costs.',
          impact: 'medium'
        }
      ],
      key_metrics: {
        health_score: 85,
        efficiency_score: 78,
        growth_potential: 90
      },
      ai_generated: true
    };

    it('fetches AI insights successfully', async () => {
      mockApi.get.mockResolvedValue({ data: mockAIInsightsResponse });

      const params = {
        start_date: new Date('2024-01-01'),
        end_date: new Date('2024-01-31'),
        force_refresh: true,
        type: 'comprehensive' as const,
        context: { focus_area: 'expenses' }
      };

      const result = await reportsService.getAIInsights(params);

      expect(mockApi.get).toHaveBeenCalledWith('/api/reports/ai-insights/', {
        params: {
          start_date: '2024-01-01',
          end_date: '2024-01-31',
          force_refresh: true,
          type: 'comprehensive',
          context: JSON.stringify({ focus_area: 'expenses' })
        },
        timeout: 30000
      });
      expect(result).toEqual(mockAIInsightsResponse);
    });

    it('handles AI insights 403 error gracefully', async () => {
      const error = { response: { status: 403 } };
      mockApi.get.mockRejectedValue(error);

      const params = {
        start_date: new Date('2024-01-01'),
        end_date: new Date('2024-01-31')
      };

      const result = await reportsService.getAIInsights(params);

      expect(result).toBeNull();
    });

    it('returns fallback data on AI service error', async () => {
      const error = new Error('AI service unavailable');
      mockApi.get.mockRejectedValue(error);

      const params = {
        start_date: new Date('2024-01-01'),
        end_date: new Date('2024-01-31')
      };

      const result = await reportsService.getAIInsights(params);

      expect(result).toEqual({
        insights: [],
        predictions: {
          next_month_income: 0,
          next_month_expenses: 0,
          projected_savings: 0
        },
        recommendations: [],
        key_metrics: {
          health_score: 0,
          efficiency_score: 0,
          growth_potential: 0
        },
        ai_generated: false,
        fallback_mode: true,
        error: 'AI service unavailable'
      });

      expect(console.error).toHaveBeenCalledWith('AI Insights error:', error);
    });

    it('asks AI questions', async () => {
      const mockAskResponse = {
        answer: 'Based on your spending patterns, I recommend...',
        confidence: 0.85,
        sources: ['transaction_data', 'category_analysis']
      };

      mockApi.post.mockResolvedValue({ data: mockAskResponse });

      const result = await reportsService.askAI(
        'How can I reduce my food expenses?',
        { current_food_spending: 800, target_reduction: 20 }
      );

      expect(mockApi.post).toHaveBeenCalledWith('/api/reports/ai-insights/ask_ai/', {
        question: 'How can I reduce my food expenses?',
        context: { current_food_spending: 800, target_reduction: 20 }
      });
      expect(result).toEqual(mockAskResponse);
    });
  });

  describe('Parameter Validation', () => {
    it('validates report parameters correctly', () => {
      // Valid parameters
      const validParams: ReportParameters = {
        start_date: '2024-01-01',
        end_date: '2024-01-31'
      };
      
      const errors = reportsService.validateReportParameters(validParams);
      expect(errors).toEqual([]);
    });

    it('validates missing dates', () => {
      const invalidParams: ReportParameters = {};
      
      const errors = reportsService.validateReportParameters(invalidParams);
      expect(errors).toContain('Data inicial é obrigatória');
      expect(errors).toContain('Data final é obrigatória');
    });

    it('validates date order', () => {
      const invalidParams: ReportParameters = {
        start_date: '2024-02-01',
        end_date: '2024-01-01'
      };
      
      const errors = reportsService.validateReportParameters(invalidParams);
      expect(errors).toContain('Data inicial deve ser anterior à data final');
    });

    it('validates future dates', () => {
      const futureDate = new Date();
      futureDate.setDate(futureDate.getDate() + 1);
      
      const invalidParams: ReportParameters = {
        start_date: '2024-01-01',
        end_date: futureDate.toISOString().split('T')[0]
      };
      
      const errors = reportsService.validateReportParameters(invalidParams);
      expect(errors).toContain('Data final não pode ser no futuro');
    });

    it('validates maximum period length', () => {
      const invalidParams: ReportParameters = {
        start_date: '2023-01-01',
        end_date: '2024-01-02' // 366+ days
      };
      
      const errors = reportsService.validateReportParameters(invalidParams);
      expect(errors).toContain('Período máximo permitido é de 1 ano');
    });

    it('validates invalid date formats', () => {
      const invalidParams: ReportParameters = {
        start_date: 'invalid-date',
        end_date: '2024-01-31'
      };
      
      const errors = reportsService.validateReportParameters(invalidParams);
      expect(errors).toContain('Formato de data inválido');
    });
  });

  describe('Data Formatting', () => {
    it('formats data for CSV export', () => {
      const data = [
        { name: 'Food', amount: 800.50, count: 15 },
        { name: 'Transport', amount: 400.25, count: 8 },
        { name: 'Entertainment,Movies', amount: 200.00, count: 5 } // Contains comma
      ];

      const result = reportsService.formatReportData(data, 'csv');

      expect(result).toEqual(
        'name,amount,count\n' +
        'Food,800.5,15\n' +
        'Transport,400.25,8\n' +
        '"Entertainment,Movies",200,5'
      );
    });

    it('formats data for JSON export', () => {
      const data = [
        { name: 'Food', amount: 800.50 },
        { name: 'Transport', amount: 400.25 }
      ];

      const result = reportsService.formatReportData(data, 'json');

      expect(JSON.parse(result as string)).toEqual(data);
    });

    it('handles empty data for CSV', () => {
      const result = reportsService.formatReportData([], 'csv');
      expect(result).toEqual('');
    });

    it('handles quotes in CSV data', () => {
      const data = [
        { description: 'Restaurant "The Golden Spoon"', amount: 45.00 }
      ];

      const result = reportsService.formatReportData(data, 'csv');

      expect(result).toEqual(
        'description,amount\n' +
        '"Restaurant ""The Golden Spoon""",45'
      );
    });
  });
});