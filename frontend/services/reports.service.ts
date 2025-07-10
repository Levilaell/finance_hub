import apiClient from "@/lib/api-client";
import { Report, ReportResult, ReportParameters, DashboardStats, CashFlowData, CategorySpending, PaginatedResponse } from "@/types";

interface IncomeVsExpenseData {
  month: string;
  income: number;
  expenses: number;
  profit: number;
}

class ReportsService {
  // Reports
  async getReports(): Promise<PaginatedResponse<Report>> {
    return apiClient.get<PaginatedResponse<Report>>("/api/reports/reports/");
  }

  async getReport(id: string): Promise<Report> {
    return apiClient.get<Report>(`/api/reports/reports/${id}/`);
  }

  async createReport(data: {
    title: string;
    report_type: string;
    parameters: ReportParameters;
  }): Promise<Report> {
    return apiClient.post<Report>("/api/reports/reports/", data);
  }

  async updateReport(
    id: string,
    data: Partial<Report>
  ): Promise<Report> {
    return apiClient.patch<Report>(`/api/reports/reports/${id}/`, data);
  }

  async deleteReport(id: string): Promise<void> {
    return apiClient.delete(`/api/reports/reports/${id}/`);
  }

  async generateReport(type: string, parameters: ReportParameters): Promise<ReportResult> {
    return apiClient.post<ReportResult>("/api/reports/reports/", {
      report_type: type,
      title: `${type} Report`,
      period_start: parameters.start_date,
      period_end: parameters.end_date,
      parameters
    });
  }

  async getReportResults(reportId: string): Promise<ReportResult[]> {
    return apiClient.get<ReportResult[]>(`/api/reports/reports/${reportId}/results/`);
  }

  async downloadReport(resultId: string): Promise<Blob> {
    const response = await apiClient.get(`/api/reports/reports/${resultId}/download/`, {
      responseType: "blob",
    });
    return response as unknown as Blob;
  }

  // Dashboard
  async getDashboardStats(): Promise<DashboardStats> {
    return apiClient.get<DashboardStats>("/api/reports/dashboard/stats/");
  }

  async getCashFlowData(params: {
    start_date: Date;
    end_date: Date;
  }): Promise<CashFlowData[]> {
    return apiClient.get<CashFlowData[]>("/api/reports/dashboard/cash-flow/", {
      start_date: params.start_date.toISOString().split('T')[0],
      end_date: params.end_date.toISOString().split('T')[0]
    });
  }

  async getCategorySpending(params: {
    start_date: Date;
    end_date: Date;
  }): Promise<CategorySpending[]> {
    return apiClient.get<CategorySpending[]>("/api/reports/dashboard/category-spending/", {
      start_date: params.start_date.toISOString().split('T')[0],
      end_date: params.end_date.toISOString().split('T')[0],
      type: 'expense'
    });
  }

  async getIncomeVsExpenses(params: {
    start_date: Date;
    end_date: Date;
  }): Promise<IncomeVsExpenseData[]> {
    const data = await apiClient.get<any[]>("/api/reports/dashboard/income-vs-expenses/", {
      start_date: params.start_date.toISOString().split('T')[0],
      end_date: params.end_date.toISOString().split('T')[0]
    });
    
    // Transform data to include profit calculation
    return data.map(item => ({
      month: item.month,
      income: item.income || 0,
      expenses: item.expenses || 0,
      profit: (item.income || 0) - (item.expenses || 0)
    }));
  }

  // Analytics
  // Scheduled Reports
  async getScheduledReports(): Promise<any> {
    return apiClient.get("/api/reports/schedules/");
  }

  async createScheduledReport(data: {
    name: string;
    report_type: string;
    frequency: string;
    email_recipients: string[];
    file_format?: string;
    parameters?: any;
  }): Promise<any> {
    return apiClient.post("/api/reports/schedules/", data);
  }

  async updateScheduledReport(id: string, data: any): Promise<any> {
    return apiClient.patch(`/api/reports/schedules/${id}/`, data);
  }

  async deleteScheduledReport(id: string): Promise<void> {
    return apiClient.delete(`/api/reports/schedules/${id}/`);
  }

  async toggleScheduledReport(id: string): Promise<any> {
    return apiClient.post(`/api/reports/schedules/${id}/toggle_active/`);
  }

  async runScheduledReport(id: string): Promise<any> {
    return apiClient.post(`/api/reports/schedules/${id}/run_now/`);
  }

  async getIncomeStatement(params: {
    start_date: string;
    end_date: string;
    comparison_period?: "previous_period" | "previous_year";
  }): Promise<any> {
    return apiClient.get("/api/reports/analytics/income-statement/", params);
  }

  async getBalanceSheet(params: {
    as_of_date: string;
    comparison_date?: string;
  }): Promise<any> {
    return apiClient.get("/api/reports/analytics/balance-sheet/", params);
  }

  async getCashFlow(params: {
    start_date: string;
    end_date: string;
    interval: "daily" | "weekly" | "monthly";
  }): Promise<any> {
    return apiClient.get("/api/reports/analytics/cash-flow/", params);
  }

  // AI Insights
  async getAIInsights(params: {
    start_date: Date;
    end_date: Date;
  }): Promise<any> {
    return apiClient.get("/api/reports/ai-insights/", {
      start_date: params.start_date.toISOString().split('T')[0],
      end_date: params.end_date.toISOString().split('T')[0]
    });
  }
}

export const reportsService = new ReportsService();