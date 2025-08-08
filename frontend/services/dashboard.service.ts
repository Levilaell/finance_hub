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
    try {
      return await apiClient.get<DashboardData>("/api/banking/dashboard/");
    } catch (error: any) {
      console.error('Dashboard API error:', error);
      
      // If authentication error, throw to trigger auth flow
      if (error?.response?.status === 401) {
        throw new Error('Authentication required');
      }
      
      // For other errors, return minimal dashboard data
      return {
        current_balance: 0,
        monthly_income: 0,
        monthly_expenses: 0,
        monthly_net: 0,
        recent_transactions: [],
        top_categories: [],
        accounts_count: 0,
        transactions_count: 0,
      };
    }
  }

  async getSimpleDashboard(): Promise<DashboardData> {
    return this.getDashboardData();
  }
}

export const dashboardService = new DashboardService();