'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '@/store/auth-store';
import { bankingService } from '@/services/banking.service';
import { Category, CategoryRequest } from '@/types/banking';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { LoadingSpinner } from '@/components/ui/loading-spinner';
import {
  PlusIcon,
  PencilIcon,
  TrashIcon,
  TagIcon,
} from '@heroicons/react/24/outline';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { toast } from 'sonner';

const PRESET_COLORS = [
  '#ef4444', // red
  '#f97316', // orange
  '#f59e0b', // amber
  '#eab308', // yellow
  '#84cc16', // lime
  '#22c55e', // green
  '#10b981', // emerald
  '#14b8a6', // teal
  '#06b6d4', // cyan
  '#0ea5e9', // sky
  '#3b82f6', // blue
  '#6366f1', // indigo
  '#8b5cf6', // violet
  '#a855f7', // purple
  '#d946ef', // fuchsia
  '#ec4899', // pink
];

const PRESET_ICONS = [
  '💰', '💼', '📈', '🎁', '🏠', '🚗', '🍽️', '🛒',
  '🎬', '💡', '🏥', '📚', '✈️', '💳', '📱', '🎮',
  '👕', '💅', '🐾', '🎯', '📦', '🔧', '⚡', '📁'
];

export default function CategoriesPage() {
  const router = useRouter();
  const { isAuthenticated, user } = useAuthStore();
  const [categories, setCategories] = useState<Category[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [isDeleteDialogOpen, setIsDeleteDialogOpen] = useState(false);
  const [editingCategory, setEditingCategory] = useState<Category | null>(null);
  const [deletingCategory, setDeletingCategory] = useState<Category | null>(null);
  const [isSaving, setIsSaving] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);

  // Form state
  const [formData, setFormData] = useState<CategoryRequest>({
    name: '',
    type: 'expense',
    color: '#d946ef',
    icon: '📁',
  });

  useEffect(() => {
    if (!isAuthenticated) {
      router.push('/login');
      return;
    }
    fetchCategories();
  }, [isAuthenticated, router]);

  const fetchCategories = async () => {
    setIsLoading(true);
    try {
      const data = await bankingService.getCategories();
      setCategories(data);
    } catch (error) {
      console.error('Error fetching categories:', error);
      toast.error('Erro ao carregar categorias');
    } finally {
      setIsLoading(false);
    }
  };

  const handleOpenDialog = (category?: Category) => {
    if (category) {
      setEditingCategory(category);
      setFormData({
        name: category.name,
        type: category.type,
        color: category.color,
        icon: category.icon,
      });
    } else {
      setEditingCategory(null);
      setFormData({
        name: '',
        type: 'expense',
        color: '#d946ef',
        icon: '📁',
      });
    }
    setIsDialogOpen(true);
  };

  const handleCloseDialog = () => {
    setIsDialogOpen(false);
    setEditingCategory(null);
  };

  const handleSave = async () => {
    if (!formData.name.trim()) {
      toast.error('Nome é obrigatório');
      return;
    }

    setIsSaving(true);
    try {
      if (editingCategory) {
        await bankingService.updateCategory(editingCategory.id, formData);
        toast.success('Categoria atualizada com sucesso!');
      } else {
        await bankingService.createCategory(formData);
        toast.success('Categoria criada com sucesso!');
      }
      handleCloseDialog();
      fetchCategories();
    } catch (error: any) {
      console.error('Error saving category:', error);
      const errorMessage = error.response?.data?.name?.[0] ||
                          error.response?.data?.detail ||
                          'Erro ao salvar categoria';
      toast.error(errorMessage);
    } finally {
      setIsSaving(false);
    }
  };

  const handleDelete = async () => {
    if (!deletingCategory) return;

    setIsDeleting(true);
    try {
      await bankingService.deleteCategory(deletingCategory.id);
      toast.success('Categoria excluída com sucesso!');
      setIsDeleteDialogOpen(false);
      setDeletingCategory(null);
      fetchCategories();
    } catch (error: any) {
      console.error('Error deleting category:', error);
      const errorMessage = error.response?.data?.error ||
                          error.response?.data?.detail ||
                          'Erro ao excluir categoria';
      toast.error(errorMessage);
    } finally {
      setIsDeleting(false);
    }
  };

  const openDeleteDialog = (category: Category) => {
    setDeletingCategory(category);
    setIsDeleteDialogOpen(true);
  };

  if (!isAuthenticated || !user || isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <LoadingSpinner />
      </div>
    );
  }

  const incomeCategories = categories.filter((c) => c.type === 'income');
  const expenseCategories = categories.filter((c) => c.type === 'expense');

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-start">
        <div>
          <h1 className="text-3xl font-bold text-white">Categorias</h1>
          <p className="text-white/70 mt-1">
            Gerencie suas categorias de transações
          </p>
        </div>
        <Button onClick={() => handleOpenDialog()}>
          <PlusIcon className="h-4 w-4 mr-2" />
          Nova Categoria
        </Button>
      </div>

      {/* Income Categories */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <TagIcon className="h-5 w-5 text-green-500" />
            Receitas ({incomeCategories.length})
          </CardTitle>
        </CardHeader>
        <CardContent>
          {incomeCategories.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
              {incomeCategories.map((category) => (
                <div
                  key={category.id}
                  className="flex items-center justify-between p-3 rounded-lg border border-white/10 hover:bg-white/5 transition-colors"
                >
                  <div className="flex items-center gap-3">
                    <div
                      className="w-10 h-10 rounded-lg flex items-center justify-center text-xl"
                      style={{ backgroundColor: category.color }}
                    >
                      {category.icon}
                    </div>
                    <div>
                      <div className="font-medium text-white">{category.name}</div>
                      {category.is_system && (
                        <div className="text-xs text-muted-foreground">Sistema</div>
                      )}
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleOpenDialog(category)}
                    >
                      <PencilIcon className="h-4 w-4" />
                    </Button>
                    {!category.is_system && (
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => openDeleteDialog(category)}
                      >
                        <TrashIcon className="h-4 w-4 text-red-500" />
                      </Button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-8 text-muted-foreground">
              Nenhuma categoria de receita encontrada
            </div>
          )}
        </CardContent>
      </Card>

      {/* Expense Categories */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <TagIcon className="h-5 w-5 text-red-500" />
            Despesas ({expenseCategories.length})
          </CardTitle>
        </CardHeader>
        <CardContent>
          {expenseCategories.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
              {expenseCategories.map((category) => (
                <div
                  key={category.id}
                  className="flex items-center justify-between p-3 rounded-lg border border-white/10 hover:bg-white/5 transition-colors"
                >
                  <div className="flex items-center gap-3">
                    <div
                      className="w-10 h-10 rounded-lg flex items-center justify-center text-xl"
                      style={{ backgroundColor: category.color }}
                    >
                      {category.icon}
                    </div>
                    <div>
                      <div className="font-medium text-white">{category.name}</div>
                      {category.is_system && (
                        <div className="text-xs text-muted-foreground">Sistema</div>
                      )}
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleOpenDialog(category)}
                    >
                      <PencilIcon className="h-4 w-4" />
                    </Button>
                    {!category.is_system && (
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => openDeleteDialog(category)}
                      >
                        <TrashIcon className="h-4 w-4 text-red-500" />
                      </Button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-8 text-muted-foreground">
              Nenhuma categoria de despesa encontrada
            </div>
          )}
        </CardContent>
      </Card>

      {/* Create/Edit Dialog */}
      <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
        <DialogContent className="bg-card border-border">
          <DialogHeader>
            <DialogTitle className="text-white">
              {editingCategory ? 'Editar Categoria' : 'Nova Categoria'}
            </DialogTitle>
            <DialogDescription className="text-muted-foreground">
              {editingCategory
                ? 'Altere os dados da categoria'
                : 'Crie uma nova categoria personalizada'}
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4">
            <div>
              <Label htmlFor="name" className="text-white">
                Nome
              </Label>
              <Input
                id="name"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                placeholder="Ex: Alimentação"
                className="mt-1"
              />
            </div>

            <div>
              <Label htmlFor="type" className="text-white">
                Tipo
              </Label>
              <Select
                value={formData.type}
                onValueChange={(value: 'income' | 'expense') =>
                  setFormData({ ...formData, type: value })
                }
              >
                <SelectTrigger className="mt-1">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="income">Receita</SelectItem>
                  <SelectItem value="expense">Despesa</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div>
              <Label className="text-white">Cor</Label>
              <div className="grid grid-cols-8 gap-2 mt-2">
                {PRESET_COLORS.map((color) => (
                  <button
                    key={color}
                    type="button"
                    onClick={() => setFormData({ ...formData, color })}
                    className={`w-8 h-8 rounded-lg transition-all ${
                      formData.color === color
                        ? 'ring-2 ring-white ring-offset-2 ring-offset-gray-900'
                        : 'hover:scale-110'
                    }`}
                    style={{ backgroundColor: color }}
                  />
                ))}
              </div>
            </div>

            <div>
              <Label className="text-white">Ícone</Label>
              <div className="grid grid-cols-8 gap-2 mt-2">
                {PRESET_ICONS.map((icon) => (
                  <button
                    key={icon}
                    type="button"
                    onClick={() => setFormData({ ...formData, icon })}
                    className={`w-8 h-8 rounded-lg flex items-center justify-center text-xl transition-all ${
                      formData.icon === icon
                        ? 'bg-white/20 ring-2 ring-white'
                        : 'hover:bg-white/10'
                    }`}
                  >
                    {icon}
                  </button>
                ))}
              </div>
            </div>

            <div className="flex items-center gap-3 p-3 rounded-lg bg-white/5">
              <div
                className="w-12 h-12 rounded-lg flex items-center justify-center text-2xl"
                style={{ backgroundColor: formData.color }}
              >
                {formData.icon}
              </div>
              <div>
                <div className="font-medium text-white">{formData.name || 'Nome da categoria'}</div>
                <div className="text-sm text-muted-foreground">
                  {formData.type === 'income' ? 'Receita' : 'Despesa'}
                </div>
              </div>
            </div>
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={handleCloseDialog} disabled={isSaving}>
              Cancelar
            </Button>
            <Button onClick={handleSave} disabled={isSaving}>
              {isSaving ? (
                <>
                  <LoadingSpinner className="w-4 h-4 mr-2" />
                  Salvando...
                </>
              ) : (
                'Salvar'
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <Dialog open={isDeleteDialogOpen} onOpenChange={setIsDeleteDialogOpen}>
        <DialogContent className="bg-card border-border">
          <DialogHeader>
            <DialogTitle className="text-white">Excluir Categoria</DialogTitle>
            <DialogDescription className="text-muted-foreground">
              {deletingCategory && (
                <>
                  Você tem certeza que deseja excluir a categoria{' '}
                  <span className="font-semibold text-white">{deletingCategory.name}</span>?
                  <br />
                  <br />
                  Esta ação não pode ser desfeita. As transações com esta categoria
                  voltarão a usar a categoria original do banco.
                </>
              )}
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setIsDeleteDialogOpen(false)}
              disabled={isDeleting}
            >
              Cancelar
            </Button>
            <Button
              onClick={handleDelete}
              disabled={isDeleting}
              className="bg-red-600 hover:bg-red-700"
            >
              {isDeleting ? (
                <>
                  <LoadingSpinner className="w-4 h-4 mr-2" />
                  Excluindo...
                </>
              ) : (
                'Excluir'
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
