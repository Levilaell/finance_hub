'use client';

import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { EmptyState } from '@/components/ui/empty-state';
import { Badge } from '@/components/ui/badge';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { 
  BanknotesIcon,
  FunnelIcon,
  ArrowDownTrayIcon,
  MagnifyingGlassIcon,
  XMarkIcon,
} from '@heroicons/react/24/outline';
import { toast } from 'sonner';

export default function TransactionsPage() {
  const [searchTerm, setSearchTerm] = useState('');
  const [showFilters, setShowFilters] = useState(false);
  const [filters, setFilters] = useState({
    account_id: undefined as string | undefined,
    category_id: undefined as string | undefined,
    type: undefined as string | undefined,
  });

  // Mock empty data
  const accounts: any[] = [];
  const categories: any[] = [];
  const transactions = { results: [], count: 0 };

  const handleSearchChange = (value: string) => {
    setSearchTerm(value);
  };

  const handleSearch = () => {
    toast.info('Banking logic removed - no search performed');
  };

  const handleExport = () => {
    toast.info('Banking logic removed - no export performed');
  };

  const clearFilters = () => {
    setFilters({
      account_id: undefined,
      category_id: undefined,
      type: undefined,
    });
    setSearchTerm('');
    toast.info('Banking logic removed - filters cleared');
  };

  const activeFiltersCount = Object.values(filters).filter(value => value !== undefined).length;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-white">
            Transações
          </h1>
          <p className="text-muted-foreground mt-1">
            Gerencie e categorize suas transações
          </p>
        </div>
        <div className="flex gap-2">
          <Button 
            variant="outline" 
            onClick={handleExport}
            disabled
            className="bg-white/10 hover:bg-white/20 border-white/20 transition-all duration-300"
          >
            <ArrowDownTrayIcon className="h-4 w-4 mr-2" />
            Exportar
          </Button>
        </div>
      </div>

      {/* Search and Filters */}
      <Card className="shadow-md">
        <CardContent className="pt-6">
          <div className="flex gap-2 mb-4">
            <div className="flex-1 relative">
              <Input
                placeholder="Buscar transações..."
                value={searchTerm}
                onChange={(e) => handleSearchChange(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
                className="pr-10"
              />
              {searchTerm && (
                <button
                  onClick={() => handleSearchChange('')}
                  className="absolute right-2 top-1/2 -translate-y-1/2 p-1 hover:bg-gray-100 rounded"
                >
                  <XMarkIcon className="h-4 w-4 text-gray-400" />
                </button>
              )}
            </div>
            <Button 
              onClick={handleSearch}
              className="bg-white text-black hover:bg-white/90 transition-all duration-300"
            >
              <MagnifyingGlassIcon className="h-4 w-4 mr-2" />
              Buscar
            </Button>
            <Button
              variant="outline"
              onClick={() => setShowFilters(!showFilters)}
              className="bg-white/10 hover:bg-white/20 border-white/20 transition-all duration-300"
            >
              <FunnelIcon className="h-4 w-4 mr-2" />
              Filtros
              {activeFiltersCount > 0 && (
                <Badge className="ml-2 bg-blue-500 text-white">
                  {activeFiltersCount}
                </Badge>
              )}
            </Button>
            {activeFiltersCount > 0 && (
              <Button
                variant="ghost"
                onClick={clearFilters}
                className="text-red-500 hover:text-red-600 hover:bg-red-50"
              >
                <XMarkIcon className="h-4 w-4 mr-1" />
                Limpar
              </Button>
            )}
          </div>

          {showFilters && (
            <div className="space-y-4 mt-4 pt-4 border-t">
              {activeFiltersCount > 0 && (
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm text-muted-foreground">
                    {activeFiltersCount} {activeFiltersCount === 1 ? 'filtro ativo' : 'filtros ativos'}
                  </span>
                  <Button
                    variant="link"
                    size="sm"
                    onClick={clearFilters}
                    className="text-red-500 hover:text-red-600"
                  >
                    Limpar todos
                  </Button>
                </div>
              )}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                  <Label>Conta</Label>
                  <Select
                    value={filters.account_id || 'all'}
                    onValueChange={(value) =>
                      setFilters({
                        ...filters,
                        account_id: value === 'all' ? undefined : value,
                      })
                    }
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Todas as contas" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">Todas as contas</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div>
                  <Label>Categoria</Label>
                  <Select
                    value={filters.category_id || 'all'}
                    onValueChange={(value) =>
                      setFilters({
                        ...filters,
                        category_id: value === 'all' ? undefined : value,
                      })
                    }
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Todas as categorias" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">Todas as categorias</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div>
                  <Label>Tipo</Label>
                  <Select
                    value={filters.type || 'all'}
                    onValueChange={(value) =>
                      setFilters({
                        ...filters,
                        type: value === 'all' ? undefined : value,
                      })
                    }
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Todos os tipos" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">Todos os tipos</SelectItem>
                      <SelectItem value="CREDIT">Receita</SelectItem>
                      <SelectItem value="DEBIT">Despesa</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Transactions List */}
      <Card className="shadow-md">
        <CardContent className="p-0">
          <EmptyState
            icon={BanknotesIcon}
            title="Nenhuma transação encontrada"
            description="Conecte uma conta bancária para ver suas transações"
          />
        </CardContent>
      </Card>
    </div>
  );
}