'use client';

import { useState } from 'react';
import { Category, CategoryRequest } from '@/types/banking';
import { bankingService } from '@/services/banking.service';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { LoadingSpinner } from '@/components/ui/loading-spinner';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import {
  PlusIcon,
  PencilIcon,
  TrashIcon,
  CheckIcon,
  XMarkIcon,
} from '@heroicons/react/24/outline';
import { toast } from 'sonner';
import { PRESET_COLORS, PRESET_ICONS, DEFAULT_CATEGORY_COLOR, DEFAULT_CATEGORY_ICON } from '@/lib/category-constants';

interface CategoryPopoverContentProps {
  categories: Category[];
  transactionType: 'CREDIT' | 'DEBIT';
  selectedCategoryId?: string | null;
  onSelectCategory: (categoryId: string | null) => void;
  onCategoriesChange: () => void;
  disabled?: boolean;
}

export function CategoryPopoverContent({
  categories,
  transactionType,
  selectedCategoryId,
  onSelectCategory,
  onCategoriesChange,
  disabled = false,
}: CategoryPopoverContentProps) {
  // Dialog states
  const [isCreateEditDialogOpen, setIsCreateEditDialogOpen] = useState(false);
  const [isDeleteDialogOpen, setIsDeleteDialogOpen] = useState(false);

  // Data states
  const [editingCategory, setEditingCategory] = useState<Category | null>(null);
  const [deletingCategory, setDeletingCategory] = useState<Category | null>(null);
  const [parentForNewSub, setParentForNewSub] = useState<Category | null>(null);

  // Loading states
  const [isSaving, setIsSaving] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);

  // Form state
  const [formData, setFormData] = useState<CategoryRequest>({
    name: '',
    type: transactionType === 'CREDIT' ? 'income' : 'expense',
    color: DEFAULT_CATEGORY_COLOR,
    icon: DEFAULT_CATEGORY_ICON,
    parent: null,
  });

  // Filter categories by transaction type
  const categoryType = transactionType === 'CREDIT' ? 'income' : 'expense';
  const filteredCategories = categories.filter((c) => c.type === categoryType);

  // Flatten categories for finding by ID
  const findCategoryById = (id: string): Category | undefined => {
    for (const cat of categories) {
      if (cat.id === id) return cat;
      if (cat.subcategories) {
        const sub = cat.subcategories.find((s) => s.id === id);
        if (sub) return sub;
      }
    }
    return undefined;
  };

  const selectedCategory = selectedCategoryId ? findCategoryById(selectedCategoryId) : null;

  // Open dialog for creating new parent category
  const handleOpenCreateDialog = () => {
    setEditingCategory(null);
    setParentForNewSub(null);
    setFormData({
      name: '',
      type: categoryType,
      color: DEFAULT_CATEGORY_COLOR,
      icon: DEFAULT_CATEGORY_ICON,
      parent: null,
    });
    setIsCreateEditDialogOpen(true);
  };

  // Open dialog for creating subcategory
  const handleOpenCreateSubDialog = (parentCategory: Category) => {
    setEditingCategory(null);
    setParentForNewSub(parentCategory);
    setFormData({
      name: '',
      type: parentCategory.type,
      color: DEFAULT_CATEGORY_COLOR,
      icon: DEFAULT_CATEGORY_ICON,
      parent: parentCategory.id,
    });
    setIsCreateEditDialogOpen(true);
  };

  // Open dialog for editing category
  const handleOpenEditDialog = (category: Category) => {
    setEditingCategory(category);
    setParentForNewSub(null);
    setFormData({
      name: category.name,
      type: category.type,
      color: category.color,
      icon: category.icon,
      parent: category.parent || null,
    });
    setIsCreateEditDialogOpen(true);
  };

  // Open delete confirmation dialog
  const handleOpenDeleteDialog = (category: Category) => {
    setDeletingCategory(category);
    setIsDeleteDialogOpen(true);
  };

  // Close create/edit dialog
  const handleCloseCreateEditDialog = () => {
    setIsCreateEditDialogOpen(false);
    setEditingCategory(null);
    setParentForNewSub(null);
  };

  // Save category (create or update)
  const handleSave = async () => {
    if (!formData.name.trim()) {
      toast.error('Nome é obrigatório');
      return;
    }

    setIsSaving(true);
    try {
      if (editingCategory) {
        await bankingService.updateCategory(editingCategory.id, formData);
        toast.success('Categoria atualizada!');
      } else {
        await bankingService.createCategory(formData);
        toast.success(formData.parent ? 'Subcategoria criada!' : 'Categoria criada!');
      }
      handleCloseCreateEditDialog();
      onCategoriesChange();
    } catch (error: any) {
      console.error('Error saving category:', error);
      const errorMessage =
        error.response?.data?.name?.[0] ||
        error.response?.data?.parent?.[0] ||
        error.response?.data?.detail ||
        'Erro ao salvar categoria';
      toast.error(errorMessage);
    } finally {
      setIsSaving(false);
    }
  };

  // Delete category
  const handleDelete = async () => {
    if (!deletingCategory) return;

    setIsDeleting(true);
    try {
      await bankingService.deleteCategory(deletingCategory.id);
      toast.success('Categoria excluída!');
      setIsDeleteDialogOpen(false);
      setDeletingCategory(null);
      onCategoriesChange();
    } catch (error: any) {
      console.error('Error deleting category:', error);
      const errorMessage =
        error.response?.data?.error ||
        error.response?.data?.detail ||
        'Erro ao excluir categoria';
      toast.error(errorMessage);
    } finally {
      setIsDeleting(false);
    }
  };

  // Check if form is for subcategory
  const isSubcategory = formData.parent !== null && formData.parent !== undefined;

  // Render category item
  const CategoryItem = ({
    category,
    isChild = false,
  }: {
    category: Category;
    isChild?: boolean;
  }) => {
    const isSelected = selectedCategoryId === category.id;

    return (
      <div
        className={`group flex items-center justify-between py-2 px-3 rounded-md cursor-pointer transition-colors ${
          isChild ? 'ml-6' : ''
        } ${isSelected ? 'bg-primary/20' : 'hover:bg-white/5'}`}
      >
        {/* Clickable area for selection */}
        <div
          className="flex items-center gap-2 flex-1 min-w-0"
          onClick={() => !disabled && onSelectCategory(category.id)}
        >
          {isChild ? (
            <div
              className="w-4 h-4 rounded shrink-0"
              style={{ backgroundColor: category.color }}
            />
          ) : (
            <div
              className="w-6 h-6 rounded flex items-center justify-center text-sm shrink-0"
              style={{ backgroundColor: category.color }}
            >
              {category.icon}
            </div>
          )}
          <span className={`truncate ${isChild ? 'text-sm' : ''} ${isSelected ? 'text-primary font-medium' : 'text-white'}`}>
            {category.name}
          </span>
          {isSelected && <CheckIcon className="h-4 w-4 text-primary shrink-0" />}
        </div>

        {/* Action buttons - visible on hover */}
        <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
          {!isChild && (
            <Button
              variant="ghost"
              size="sm"
              className="h-6 w-6 p-0"
              onClick={(e) => {
                e.stopPropagation();
                handleOpenCreateSubDialog(category);
              }}
              title="Adicionar subcategoria"
            >
              <PlusIcon className="h-3 w-3" />
            </Button>
          )}
          <Button
            variant="ghost"
            size="sm"
            className="h-6 w-6 p-0"
            onClick={(e) => {
              e.stopPropagation();
              handleOpenEditDialog(category);
            }}
            title="Editar"
          >
            <PencilIcon className="h-3 w-3" />
          </Button>
          {!category.is_system && (
            <Button
              variant="ghost"
              size="sm"
              className="h-6 w-6 p-0 text-red-500 hover:text-red-400"
              onClick={(e) => {
                e.stopPropagation();
                handleOpenDeleteDialog(category);
              }}
              title="Excluir"
            >
              <TrashIcon className="h-3 w-3" />
            </Button>
          )}
        </div>
      </div>
    );
  };

  return (
    <>
      {/* Popover Content */}
      <div className="p-2 max-h-80 overflow-y-auto">
        {/* Header with title and add button */}
        <div className="flex items-center justify-between px-2 py-1 mb-2">
          <span className="text-xs font-medium text-muted-foreground uppercase">
            {categoryType === 'income' ? 'Receitas' : 'Despesas'}
          </span>
          <Button
            variant="ghost"
            size="sm"
            className="h-6 px-2 text-xs"
            onClick={handleOpenCreateDialog}
          >
            <PlusIcon className="h-3 w-3 mr-1" />
            Nova
          </Button>
        </div>

        {/* Remove category option */}
        <div
          className={`flex items-center gap-2 py-2 px-3 rounded-md cursor-pointer transition-colors mb-1 ${
            !selectedCategoryId ? 'bg-primary/20' : 'hover:bg-white/5'
          }`}
          onClick={() => !disabled && onSelectCategory(null)}
        >
          <XMarkIcon className="h-4 w-4 text-muted-foreground" />
          <span className="text-sm text-muted-foreground">Remover categoria</span>
          {!selectedCategoryId && <CheckIcon className="h-4 w-4 text-primary ml-auto" />}
        </div>

        <div className="border-t border-white/10 my-2" />

        {/* Categories list */}
        {filteredCategories.length > 0 ? (
          <div className="space-y-1">
            {filteredCategories.map((category) => (
              <div key={category.id}>
                <CategoryItem category={category} />
                {category.subcategories && category.subcategories.length > 0 && (
                  <div className="space-y-1">
                    {category.subcategories.map((sub) => (
                      <CategoryItem key={sub.id} category={sub} isChild />
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-4 text-sm text-muted-foreground">
            Nenhuma categoria encontrada
          </div>
        )}
      </div>

      {/* Create/Edit Dialog */}
      <Dialog open={isCreateEditDialogOpen} onOpenChange={setIsCreateEditDialogOpen}>
        <DialogContent className="bg-card border-border sm:max-w-md">
          <DialogHeader>
            <DialogTitle className="text-white">
              {editingCategory
                ? 'Editar Categoria'
                : isSubcategory
                ? 'Nova Subcategoria'
                : 'Nova Categoria'}
            </DialogTitle>
            <DialogDescription className="text-muted-foreground">
              {editingCategory
                ? 'Altere os dados da categoria'
                : isSubcategory
                ? `Subcategoria de "${parentForNewSub?.name}"`
                : 'Crie uma nova categoria'}
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4">
            {/* Name input */}
            <div>
              <Label htmlFor="cat-name" className="text-white">
                Nome
              </Label>
              <Input
                id="cat-name"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                placeholder={isSubcategory ? 'Ex: Restaurantes' : 'Ex: Alimentação'}
                className="mt-1"
              />
            </div>

            {/* Color picker */}
            <div>
              <Label className="text-white">Cor</Label>
              <div className="grid grid-cols-8 gap-2 mt-2">
                {PRESET_COLORS.map((color) => (
                  <button
                    key={color}
                    type="button"
                    onClick={() => setFormData({ ...formData, color })}
                    className={`w-7 h-7 rounded-lg transition-all ${
                      formData.color === color
                        ? 'ring-2 ring-white ring-offset-2 ring-offset-gray-900'
                        : 'hover:scale-110'
                    }`}
                    style={{ backgroundColor: color }}
                  />
                ))}
              </div>
            </div>

            {/* Icon picker - only for parent categories */}
            {!isSubcategory && (
              <div>
                <Label className="text-white">Ícone</Label>
                <div className="grid grid-cols-8 gap-2 mt-2">
                  {PRESET_ICONS.map((icon) => (
                    <button
                      key={icon}
                      type="button"
                      onClick={() => setFormData({ ...formData, icon })}
                      className={`w-7 h-7 rounded-lg flex items-center justify-center text-base transition-all ${
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
            )}

            {/* Preview */}
            <div className="flex items-center gap-3 p-3 rounded-lg bg-white/5">
              {isSubcategory ? (
                <div
                  className="w-6 h-6 rounded"
                  style={{ backgroundColor: formData.color }}
                />
              ) : (
                <div
                  className="w-8 h-8 rounded flex items-center justify-center text-lg"
                  style={{ backgroundColor: formData.color }}
                >
                  {formData.icon}
                </div>
              )}
              <div>
                <div className="font-medium text-white text-sm">
                  {formData.name || 'Nome da categoria'}
                </div>
                <div className="text-xs text-muted-foreground">
                  {formData.type === 'income' ? 'Receita' : 'Despesa'}
                  {isSubcategory && ' (subcategoria)'}
                </div>
              </div>
            </div>
          </div>

          <DialogFooter>
            <Button
              variant="outline"
              onClick={handleCloseCreateEditDialog}
              disabled={isSaving}
            >
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
        <DialogContent className="bg-card border-border sm:max-w-md">
          <DialogHeader>
            <DialogTitle className="text-white">Excluir Categoria</DialogTitle>
            <DialogDescription className="text-muted-foreground">
              {deletingCategory && (
                <>
                  Deseja excluir a categoria{' '}
                  <span className="font-semibold text-white">
                    {deletingCategory.name}
                  </span>
                  ?
                  {deletingCategory.subcategories &&
                    deletingCategory.subcategories.length > 0 && (
                      <>
                        <br />
                        <br />
                        <span className="text-yellow-500 font-medium">
                          Esta categoria possui{' '}
                          {deletingCategory.subcategories.length} subcategoria(s)
                          que também serão excluídas.
                        </span>
                      </>
                    )}
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
    </>
  );
}
