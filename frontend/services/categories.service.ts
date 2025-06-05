import apiClient from "@/lib/api-client";
import { Category, CategoryRule, CategoryForm } from "@/types";

class CategoriesService {
  // Categories
  async getCategories(): Promise<Category[]> {
    return apiClient.get<Category[]>("/api/banking/categories/");
  }

  async getCategory(id: string): Promise<Category> {
    return apiClient.get<Category>(`/api/banking/categories/${id}/`);
  }

  async createCategory(data: CategoryForm): Promise<Category> {
    return apiClient.post<Category>("/api/banking/categories/", data);
  }

  async updateCategory(id: string, data: Partial<CategoryForm>): Promise<Category> {
    return apiClient.patch<Category>(`/api/banking/categories/${id}/`, data);
  }

  async deleteCategory(id: string): Promise<void> {
    return apiClient.delete(`/api/banking/categories/${id}/`);
  }

  // Category Rules
  async getRules(): Promise<CategoryRule[] | any> {
    return apiClient.get<CategoryRule[] | any>("/api/categories/rules/");
  }

  async getRule(id: string): Promise<CategoryRule> {
    return apiClient.get<CategoryRule>(`/api/categories/rules/${id}/`);
  }

  async createRule(data: {
    category_id: string;
    rule_type: CategoryRule["rule_type"];
    field: CategoryRule["field"];
    value: string;
    priority?: number;
  }): Promise<CategoryRule> {
    return apiClient.post<CategoryRule>("/api/categories/rules/", data);
  }

  async updateRule(
    id: string,
    data: Partial<CategoryRule>
  ): Promise<CategoryRule> {
    return apiClient.patch<CategoryRule>(`/api/categories/rules/${id}/`, data);
  }

  async deleteRule(id: string): Promise<void> {
    return apiClient.delete(`/api/categories/rules/${id}/`);
  }

  async testRule(data: {
    rule_type: CategoryRule["rule_type"];
    field: CategoryRule["field"];
    value: string;
    test_string: string;
  }): Promise<{ matches: boolean }> {
    return apiClient.post("/api/categories/rules/test/", data);
  }

  async applyRules(transactionIds?: string[]): Promise<{
    categorized: number;
    errors: string[];
  }> {
    return apiClient.post("/api/categories/rules/apply/", {
      transaction_ids: transactionIds,
    });
  }
}

export const categoriesService = new CategoriesService();