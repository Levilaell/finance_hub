import apiClient from "@/lib/api-client";
import { Category, CategoryRule, CategoryForm } from "@/types";

class CategoriesService {
  // Categories
  async getCategories(): Promise<Category[]> {
    return apiClient.get<Category[]>("/api/banking/categories/");
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
}

export const categoriesService = new CategoriesService();