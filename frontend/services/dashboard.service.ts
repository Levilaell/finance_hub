import apiClient from "@/lib/api-client";

export interface DashboardData {
  current_balance: number;
  monthly_income: number;
  monthly_expenses: number;
  monthly_net: number;
  recent_transactions: any[];
  top_categories: any[];
  accounts_count: number;
  transactions_count: number;
  active_budgets?: any[];
  budgets_summary?: any;
  active_goals?: any[];
  goals_summary?: any;
  monthly_trends?: any[];
  expense_trends?: any[];
  income_comparison?: any;
  expense_comparison?: any;
  financial_insights?: string[];
  alerts?: any[];
}

class DashboardService {
  async getDashboardData(): Promise<DashboardData> {
      // Fallback to simple dashboard
      return await apiClient.get<DashboardData>("/api/banking/dashboard/");
    
  }

  async getSimpleDashboard(): Promise<DashboardData> {
    return apiClient.get<DashboardData>("/api/banking/dashboard/");
  }


}

export const dashboardService = new DashboardService();