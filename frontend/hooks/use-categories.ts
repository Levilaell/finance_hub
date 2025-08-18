import { useQuery, useMutation, useQueryClient, UseQueryOptions, UseMutationOptions } from '@tanstack/react-query';
import { categoriesService } from '@/services/categories.service';
import { bankingService } from '@/services/banking.service';
import { Category } from '@/types';
import { TransactionCategory } from '@/types/banking.types';

interface CreateCategoryData {
  name: string;
  type: 'income' | 'expense';
  color?: string;
  icon?: string;
  parent?: number;
}

interface UpdateCategoryData extends CreateCategoryData {
  id: string;
}

export function useCategories(options?: UseQueryOptions<Category[]>) {
  return useQuery({
    queryKey: ['categories'],
    queryFn: () => categoriesService.getCategories(),
    ...options,
  });
}

// Alternative for banking service categories
export function useBankingCategories(options?: UseQueryOptions<TransactionCategory[]>) {
  return useQuery({
    queryKey: ['categories'],
    queryFn: () => bankingService.getCategories(),
    ...options,
  });
}

export function useCreateCategory(options?: UseMutationOptions<Category, Error, CreateCategoryData>) {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (data: CreateCategoryData) => categoriesService.createCategory(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['categories'] });
    },
    ...options,
  });
}

export function useUpdateCategory(options?: UseMutationOptions<Category, Error, UpdateCategoryData>) {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ id, ...data }: UpdateCategoryData) => categoriesService.updateCategory(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['categories'] });
    },
    ...options,
  });
}

export function useDeleteCategory(options?: UseMutationOptions<void, Error, string>) {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (id: string) => categoriesService.deleteCategory(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['categories'] });
    },
    ...options,
  });
}