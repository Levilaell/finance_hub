'use client';

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { LoadingSpinner } from '@/components/ui/loading-spinner';
import { ErrorMessage } from '@/components/ui/error-message';
import { EmptyState } from '@/components/ui/empty-state';
import { categoriesService } from '@/services/categories.service';
import { Category, CategoryForm, CategoryRule } from '@/types';
import { 
  TagIcon, 
  PlusIcon, 
  TrashIcon,
  PencilIcon,
  SparklesIcon,
  ArrowTrendingUpIcon,
  ArrowTrendingDownIcon
} from '@heroicons/react/24/outline';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';

const DEFAULT_COLORS = [
  '#ef4444', '#f97316', '#f59e0b', '#eab308', '#84cc16',
  '#22c55e', '#10b981', '#14b8a6', '#06b6d4', '#0ea5e9',
  '#3b82f6', '#6366f1', '#8b5cf6', '#a855f7', '#d946ef',
  '#ec4899', '#f43f5e'
];

const ICONS = [
  '🏠', '🚗', '🛒', '🍔', '💊', '🎓', '✈️', '🎬',
  '💰', '📱', '💡', '🏥', '🎮', '👔', '🎁', '💳'
];

export default function CategoriesPage() {
  const queryClient = useQueryClient();
  const [isAddingCategory, setIsAddingCategory] = useState(false);
  const [editingCategory, setEditingCategory] = useState<Category | null>(null);
  const [selectedCategory, setSelectedCategory] = useState<Category | null>(null);
  const [selectedColor, setSelectedColor] = useState(DEFAULT_COLORS[0]);
  const [selectedIcon, setSelectedIcon] = useState(ICONS[0]);

  const { data: categories, isLoading, error } = useQuery({
    queryKey: ['categories'],
    queryFn: () => categoriesService.getCategories(),
  });

  const { data: rules } = useQuery({
    queryKey: ['category-rules'],
    queryFn: () => categoriesService.getRules(),
  });

  const createCategoryMutation = useMutation({
    mutationFn: (data: CategoryForm) => categoriesService.createCategory(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['categories'] });
      setIsAddingCategory(false);
      toast.success('Category created successfully');
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to create category');
    },
  });

  const updateCategoryMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<CategoryForm> }) =>
      categoriesService.updateCategory(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['categories'] });
      setEditingCategory(null);
      toast.success('Category updated successfully');
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to update category');
    },
  });

  const deleteCategoryMutation = useMutation({
    mutationFn: (id: string) => categoriesService.deleteCategory(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['categories'] });
      setSelectedCategory(null);
      toast.success('Category deleted successfully');
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to delete category');
    },
  });

  const autoCategorizeMutation = useMutation({
    mutationFn: () => categoriesService.applyRules(),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['bank-transactions'] });
      toast.success(`${data.categorized} transactions categorized automatically`);
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to auto-categorize');
    },
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <LoadingSpinner />
      </div>
    );
  }

  if (error) {
    return <ErrorMessage message="Falha ao carregar categorias" />;
  }

  const incomeCategories = categories?.filter(cat => cat.category_type === 'income') || [];
  const expenseCategories = categories?.filter(cat => cat.category_type === 'expense') || [];

  const CategoryCard = ({ category }: { category: Category }) => {
    // Handle both array and paginated response
    const rulesArray = Array.isArray(rules) ? rules : (rules as any)?.results || [];
    const categoryRules = rulesArray.filter((rule: any) => rule.category === category.id) || [];
    
    return (
      <Card className="hover:shadow-lg transition-shadow">
        <CardContent className="p-6">
          <div className="flex items-start justify-between mb-4">
            <div className="flex items-center space-x-3">
              <div
                className="w-12 h-12 rounded-lg flex items-center justify-center text-2xl"
                style={{ backgroundColor: category.color || '#gray' }}
              >
                {category.icon || '📁'}
              </div>
              <div>
                <h3 className="font-semibold text-lg">{category.name}</h3>
                {category.is_system && (
                  <span className="text-xs text-gray-500 bg-gray-100 px-2 py-1 rounded">
                    System
                  </span>
                )}
              </div>
            </div>
            {!category.is_system && (
              <div className="flex space-x-1">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => {
                    setEditingCategory(category);
                    setSelectedColor(category.color || DEFAULT_COLORS[0]);
                    setSelectedIcon(category.icon || ICONS[0]);
                  }}
                >
                  <PencilIcon className="h-4 w-4" />
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  className="text-red-600 hover:text-red-700"
                  onClick={() => setSelectedCategory(category)}
                >
                  <TrashIcon className="h-4 w-4" />
                </Button>
              </div>
            )}
          </div>
          {categoryRules.length > 0 && (
            <div className="space-y-2">
              <p className="text-sm text-gray-600 font-medium">Auto-categorization rules:</p>
              {categoryRules.map((rule) => (
                <div key={rule.id} className="text-xs text-gray-500 bg-gray-50 p-2 rounded">
                  {rule.field} {rule.rule_type} "{rule.value}"
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    );
  };

  const CategoryForm = ({
    category,
    onSubmit,
    onCancel,
  }: {
    category?: Category;
    onSubmit: (data: CategoryForm) => void;
    onCancel: () => void;
  }) => {
    const [formData, setFormData] = useState({
      name: category?.name || '',
      type: category?.category_type || 'expense',
    });

    return (
      <form
        onSubmit={(e) => {
          e.preventDefault();
          onSubmit({
            name: formData.name,
            category_type: formData.type as 'income' | 'expense',
            color: selectedColor,
            icon: selectedIcon,
            parent: undefined,
          });
        }}
      >
        <div className="space-y-4 py-4">
          <div>
            <Label htmlFor="name">Category Name</Label>
            <Input
              id="name"
              name="name"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              placeholder="e.g., Groceries"
              required
            />
          </div>
        <div>
          <Label htmlFor="type">Type</Label>
          <Select 
            name="type" 
            value={formData.type}
            onValueChange={(value) => setFormData({ ...formData, type: value })}
          >
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="income">
                <div className="flex items-center">
                  <ArrowTrendingUpIcon className="h-4 w-4 mr-2 text-green-600" />
                  Receita
                </div>
              </SelectItem>
              <SelectItem value="expense">
                <div className="flex items-center">
                  <ArrowTrendingDownIcon className="h-4 w-4 mr-2 text-red-600" />
                  Expense
                </div>
              </SelectItem>
            </SelectContent>
          </Select>
        </div>
        <div>
          <Label>Icon</Label>
          <div className="grid grid-cols-8 gap-2 mt-2">
            {ICONS.map((icon) => (
              <button
                key={icon}
                type="button"
                className={`p-2 text-2xl rounded-lg border-2 transition-colors ${
                  selectedIcon === icon
                    ? 'border-primary bg-primary/10'
                    : 'border-gray-200 hover:border-gray-300'
                }`}
                onClick={() => setSelectedIcon(icon)}
              >
                {icon}
              </button>
            ))}
          </div>
        </div>
        <div>
          <Label>Color</Label>
          <div className="grid grid-cols-9 gap-2 mt-2">
            {DEFAULT_COLORS.map((color) => (
              <button
                key={color}
                type="button"
                className={`w-10 h-10 rounded-lg border-2 transition-all ${
                  selectedColor === color
                    ? 'border-gray-800 scale-110'
                    : 'border-transparent hover:scale-105'
                }`}
                style={{ backgroundColor: color }}
                onClick={() => setSelectedColor(color)}
              />
            ))}
          </div>
        </div>
      </div>
      <DialogFooter>
        <Button type="button" variant="outline" onClick={onCancel}>
          Cancelar
        </Button>
        <Button type="submit">
          {category ? 'Atualizar' : 'Criar'} Categoria
        </Button>
      </DialogFooter>
    </form>
    );
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold">Categories</h1>
          <p className="text-gray-600">Organize suas transações com categorias</p>
        </div>
        <div className="flex space-x-2">

          <Button onClick={() => setIsAddingCategory(true)}>
            <PlusIcon className="h-4 w-4 mr-2" />
            Adicionar Categoria
          </Button>
        </div>
      </div>

      <Tabs defaultValue="all" className="space-y-4">
        <TabsList>
          <TabsTrigger value="all">Todas as Categorias</TabsTrigger>
          <TabsTrigger value="income">Receitas</TabsTrigger>
          <TabsTrigger value="expense">Despesas</TabsTrigger>
        </TabsList>

        <TabsContent value="all" className="space-y-4">
          {categories && categories.length > 0 ? (
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
              {categories.map((category) => (
                <CategoryCard key={category.id} category={category} />
              ))}
            </div>
          ) : (
            <EmptyState
              icon={TagIcon}
              title="Nenhuma categoria"
              description="Crie sua primeira categoria para começar a organizar as transações"
              action={
                <Button onClick={() => setIsAddingCategory(true)}>
                  <PlusIcon className="h-4 w-4 mr-2" />
                  Criar Categoria
                </Button>
              }
            />
          )}
        </TabsContent>

        <TabsContent value="income" className="space-y-4">
          {incomeCategories.length > 0 ? (
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
              {incomeCategories.map((category) => (
                <CategoryCard key={category.id} category={category} />
              ))}
            </div>
          ) : (
            <EmptyState
              icon={ArrowTrendingUpIcon}
              title="Nenhuma categoria de receita"
              description="Crie categorias para rastrear suas fontes de receita"
            />
          )}
        </TabsContent>

        <TabsContent value="expense" className="space-y-4">
          {expenseCategories.length > 0 ? (
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
              {expenseCategories.map((category) => (
                <CategoryCard key={category.id} category={category} />
              ))}
            </div>
          ) : (
            <EmptyState
              icon={ArrowTrendingDownIcon}
              title="Nenhuma categoria de despesa"
              description="Crie categorias para rastrear suas despesas"
            />
          )}
        </TabsContent>
      </Tabs>

      {/* Add Category Dialog */}
      <Dialog open={isAddingCategory} onOpenChange={setIsAddingCategory}>
        <DialogContent className="sm:max-w-[500px]">
          <DialogHeader>
            <DialogTitle>Criar Categoria</DialogTitle>
            <DialogDescription>
              Add a new category to organize your transactions
            </DialogDescription>
          </DialogHeader>
          <CategoryForm
            onSubmit={(data) => {
        // Reset the selected icon and color to default for next category
        setSelectedIcon(ICONS[0]);
        setSelectedColor(DEFAULT_COLORS[0]);
        createCategoryMutation.mutate(data);
      }}
            onCancel={() => setIsAddingCategory(false)}
          />
        </DialogContent>
      </Dialog>

      {/* Edit Category Dialog */}
      <Dialog open={!!editingCategory} onOpenChange={() => setEditingCategory(null)}>
        <DialogContent className="sm:max-w-[500px]">
          <DialogHeader>
            <DialogTitle>Editar Categoria</DialogTitle>
            <DialogDescription>
              Atualizar detalhes da categoria
            </DialogDescription>
          </DialogHeader>
          {editingCategory && (
            <CategoryForm
              category={editingCategory}
              onSubmit={(data) =>
                updateCategoryMutation.mutate({ id: editingCategory.id, data })
              }
              onCancel={() => setEditingCategory(null)}
            />
          )}
        </DialogContent>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <Dialog open={!!selectedCategory} onOpenChange={() => setSelectedCategory(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Excluir Categoria</DialogTitle>
            <DialogDescription>
              Are you sure you want to delete "{selectedCategory?.name}"? 
              Transactions in this category will become uncategorized.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setSelectedCategory(null)}
            >
              Cancelar
            </Button>
            <Button
              variant="destructive"
              onClick={() => {
                if (selectedCategory) {
                  deleteCategoryMutation.mutate(selectedCategory.id);
                }
              }}
              disabled={deleteCategoryMutation.isPending}
            >
              {deleteCategoryMutation.isPending ? <LoadingSpinner /> : 'Excluir Categoria'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}