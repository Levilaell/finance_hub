'use client';

import { useState, useCallback, useMemo, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { LoadingSpinner } from '@/components/ui/loading-spinner';
import { ErrorMessage } from '@/components/ui/error-message';
import { EmptyState } from '@/components/ui/empty-state';
import { DataTable } from '@/components/ui/data-table';
import { bankingService } from '@/services/banking.service';
import { categoriesService } from '@/services/categories.service';
import { BankTransaction, TransactionFilter, Category } from '@/types';
import { formatCurrency, formatDate, cn } from '@/lib/utils';
import { HydrationBoundary } from '@/components/hydration-boundary';
import { useClientOnly } from '@/hooks/use-client-only';
import { 
  BanknotesIcon,
  FunnelIcon,
  ArrowDownTrayIcon,
  TagIcon,
  ArrowTrendingUpIcon,
  ArrowTrendingDownIcon,
  MagnifyingGlassIcon,
  SparklesIcon,
  XMarkIcon,
  CheckIcon,
  DocumentArrowDownIcon,
  TableCellsIcon,
  InformationCircleIcon,
  PencilIcon,
  ChevronLeftIcon,
  ChevronRightIcon,
  CurrencyDollarIcon,
  ArrowPathIcon
} from '@heroicons/react/24/outline';
import {
  SparklesIcon as SparklesSolidIcon
} from '@heroicons/react/24/solid';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from '@/components/ui/popover';
import { DatePicker } from '@/components/ui/date-picker';
import { useDebounce } from '@/hooks/use-debounce';
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from '@/components/ui/tabs';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';

interface TransactionWithTags extends BankTransaction {
  tags?: string[];
  ai_categorized?: boolean;
  ai_confidence?: number;
  notes?: string;
  category_detail?: {
    id: string;
    name: string;
    color?: string;
    icon?: string;
  } | null;
}

export default function TransactionsPage() {
  const queryClient = useQueryClient();
  const isClient = useClientOnly();
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);
  const [filters, setFilters] = useState<TransactionFilter>({});
  const [selectedTransactions, setSelectedTransactions] = useState<string[]>([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [showFilters, setShowFilters] = useState(false);
  const [editingNote, setEditingNote] = useState<string | null>(null);
  const [noteText, setNoteText] = useState('');
  
  const debouncedSearch = useDebounce(searchTerm, 500);

  // Queries
  const { data: transactions, isLoading, error, refetch } = useQuery({
    queryKey: ['bank-transactions', { ...filters, search: debouncedSearch, page, page_size: pageSize }],
    queryFn: () => bankingService.getTransactions({ 
      ...filters, 
      search: debouncedSearch,
      page,
      page_size: pageSize 
    }),
  });

  const { data: accounts } = useQuery({
    queryKey: ['bank-accounts'],
    queryFn: () => bankingService.getBankAccounts(),
  });

  const { data: categories = [] } = useQuery({
    queryKey: ['categories'],
    queryFn: () => categoriesService.getCategories(),
  });

  // Safe date parsing for hydration
  const startDate = useMemo(() => {
    if (!filters.start_date) return undefined;
    return new Date(filters.start_date + 'T00:00:00.000Z');
  }, [filters.start_date]);

  const endDate = useMemo(() => {
    if (!filters.end_date) return undefined;
    return new Date(filters.end_date + 'T00:00:00.000Z');
  }, [filters.end_date]);

  // Calculate totals
  const totals = useMemo(() => {
    if (!transactions?.results) return { income: 0, expenses: 0, balance: 0 };
    
    return transactions.results.reduce((acc, transaction) => {
      const amount = Math.abs(transaction.amount);
      if (transaction.transaction_type === 'credit') {
        acc.income += amount;
      } else {
        acc.expenses += amount;
      }
      return acc;
    }, { income: 0, expenses: 0, balance: 0 });
  }, [transactions]);

  totals.balance = totals.income - totals.expenses;

  // Mutations
  const updateCategoryMutation = useMutation({
    mutationFn: ({ id, categoryId }: { id: string; categoryId: string }) =>
      bankingService.updateTransaction(id, { category_id: categoryId }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['bank-transactions'] });
      toast.success('Category updated successfully');
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to update category');
    },
  });

  const updateNoteMutation = useMutation({
    mutationFn: ({ id, notes }: { id: string; notes: string }) =>
      bankingService.updateTransaction(id, { notes }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['bank-transactions'] });
      setEditingNote(null);
      setNoteText('');
      toast.success('Note updated successfully');
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to update note');
    },
  });

  const bulkUpdateCategoryMutation = useMutation({
    mutationFn: ({ transactionIds, categoryId }: { transactionIds: string[]; categoryId: string }) =>
      bankingService.bulkCategorize({ transaction_ids: transactionIds, category_id: categoryId }),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['bank-transactions'] });
      setSelectedTransactions([]);
      toast.success(`${data.updated} transactions categorized successfully`);
    },
    onError: (error: any) => {
      toast.error('Failed to update categories');
    },
  });

  const exportTransactionsMutation = useMutation({
    mutationFn: (format: 'csv' | 'excel') => bankingService.exportTransactions(filters),
    onSuccess: (data, format) => {
      if (typeof window !== 'undefined') {
        // Generate consistent timestamp
        const timestamp = new Date().toISOString().split('T')[0]; // YYYY-MM-DD format
        const url = window.URL.createObjectURL(new Blob([data]));
        const link = document.createElement('a');
        link.href = url;
        const fileExtension = format === 'excel' ? 'xlsx' : 'csv';
        link.setAttribute('download', `transactions_${timestamp}.${fileExtension}`);
        document.body.appendChild(link);
        link.click();
        link.remove();
        window.URL.revokeObjectURL(url);
      }
      toast.success('Transactions exported successfully');
    },
    onError: (error: any) => {
      toast.error('Failed to export transactions');
    },
  });

  const handleSelectAll = useCallback(() => {
    if (selectedTransactions.length === transactions?.results?.length) {
      setSelectedTransactions([]);
    } else {
      setSelectedTransactions(transactions?.results?.map(t => t.id) || []);
    }
  }, [selectedTransactions, transactions]);

  const handleSelectTransaction = useCallback((id: string) => {
    setSelectedTransactions(prev => 
      prev.includes(id) 
        ? prev.filter(t => t !== id)
        : [...prev, id]
    );
  }, []);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <LoadingSpinner />
      </div>
    );
  }

  if (error) {
    return <ErrorMessage message="Failed to load transactions" />;
  }

  const columns = [
    {
      key: 'select',
      header: () => (
        <input
          type="checkbox"
          checked={selectedTransactions.length === transactions?.results?.length && transactions?.results?.length > 0}
          onChange={handleSelectAll}
          className="rounded border-gray-300"
        />
      ),
      cell: (transaction: TransactionWithTags) => (
        <input
          type="checkbox"
          checked={selectedTransactions.includes(transaction.id)}
          onChange={() => handleSelectTransaction(transaction.id)}
          className="rounded border-gray-300"
        />
      ),
    },
    {
      key: 'date',
      header: 'Date',
      cell: (transaction: TransactionWithTags) => (
        <HydrationBoundary fallback={
          <div className="whitespace-nowrap">
            <div className="h-4 bg-gray-200 rounded animate-pulse mb-1"></div>
            <div className="h-3 bg-gray-100 rounded animate-pulse"></div>
          </div>
        }>
          <div className="whitespace-nowrap">
            <p className="font-medium text-sm">{formatDate(transaction.transaction_date)}</p>
            <p className="text-xs text-gray-500">{formatDate(transaction.posted_date)}</p>
          </div>
        </HydrationBoundary>
      ),
    },
    {
      key: 'description',
      header: 'Description',
      cell: (transaction: TransactionWithTags) => (
        <div className="max-w-xs">
          <p className="font-medium text-sm truncate">{transaction.description}</p>
          {transaction.merchant_name && (
            <p className="text-xs text-gray-600 truncate">{transaction.merchant_name}</p>
          )}
          {transaction.notes && (
            <div className="flex items-center mt-1 text-xs text-gray-500">
              <InformationCircleIcon className="h-3 w-3 mr-1" />
              <span className="truncate">{transaction.notes}</span>
            </div>
          )}
          {transaction.tags && transaction.tags.length > 0 && (
            <div className="flex flex-wrap gap-1 mt-1">
              {transaction.tags.map((tag, idx) => (
                <span key={idx} className="inline-flex items-center px-2 py-0.5 rounded text-xs bg-gray-100 text-gray-600">
                  {tag}
                </span>
              ))}
            </div>
          )}
        </div>
      ),
    },
    {
      key: 'category',
      header: 'Category',
      cell: (transaction: TransactionWithTags) => (
        <div className="min-w-[180px]">
          <Select
            value={transaction.category_detail?.id || 'uncategorized'}
            onValueChange={(value) =>
              updateCategoryMutation.mutate({ 
                id: transaction.id, 
                categoryId: value === 'uncategorized' ? '' : value 
              })
            }
          >
            <SelectTrigger className="w-full h-8 text-sm">
              <div className="flex items-center w-full">
                {transaction.ai_categorized && (
                  <SparklesSolidIcon className="h-3 w-3 mr-1 text-purple-500" title="AI Categorized" />
                )}
                {transaction.category_detail ? (
                  <>
                    <span
                      className="w-2 h-2 rounded-full mr-2 flex-shrink-0"
                      style={{ backgroundColor: transaction.category_detail.color || '#gray' }}
                    />
                    <span className="truncate">{transaction.category_detail.name}</span>
                  </>
                ) : (
                  <span className="text-gray-400">Uncategorized</span>
                )}
              </div>
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="uncategorized">
                <span className="text-gray-400">Uncategorized</span>
              </SelectItem>
              {categories.map((category) => (
                <SelectItem key={category.id} value={category.id}>
                  <div className="flex items-center">
                    <span
                      className="w-3 h-3 rounded-full mr-2"
                      style={{ backgroundColor: category.color || '#gray' }}
                    />
                    {category.name}
                  </div>
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          {transaction.ai_categorized && transaction.ai_confidence && (
            <div className="flex items-center mt-1 text-xs text-purple-600">
              <SparklesIcon className="h-3 w-3 mr-1" />
              <span>AI: {Math.round(transaction.ai_confidence * 100)}% confident</span>
            </div>
          )}
        </div>
      ),
    },
    {
      key: 'amount',
      header: 'Amount',
      cell: (transaction: TransactionWithTags) => (
        <div className={cn(
          "font-semibold text-right whitespace-nowrap",
          transaction.transaction_type === 'credit' ? 'text-green-600' : 'text-red-600'
        )}>
          <div className="flex items-center justify-end">
            {transaction.transaction_type === 'credit' ? (
              <ArrowTrendingUpIcon className="h-4 w-4 mr-1" />
            ) : (
              <ArrowTrendingDownIcon className="h-4 w-4 mr-1" />
            )}
            {formatCurrency(Math.abs(transaction.amount))}
          </div>
        </div>
      ),
    },
    {
      key: 'account',
      header: 'Account',
      cell: (transaction: TransactionWithTags) => {
        const account = accounts?.results?.find(
          (acc) => acc.id === transaction.bank_account
        );
        return (
          <p className="text-sm text-gray-600 truncate max-w-[120px]">
            {account?.account_name || 'Unknown'}
          </p>
        );
      },
    },
    {
      key: 'actions',
      header: '',
      cell: (transaction: TransactionWithTags) => (
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" size="sm" className="h-8 w-8 p-0">
              <span className="sr-only">Open menu</span>
              <PencilIcon className="h-4 w-4" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            <DropdownMenuItem onClick={() => {
              setEditingNote(transaction.id);
              setNoteText(transaction.notes || '');
            }}>
              Add/Edit Note
            </DropdownMenuItem>
            <DropdownMenuItem>Add Tags</DropdownMenuItem>
            <DropdownMenuSeparator />
            <DropdownMenuItem className="text-red-600">
              Report Issue
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      ),
    },
  ];

  const totalPages = Math.ceil((transactions?.count || 0) / pageSize);

  return (
    <div className="space-y-4 md:space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:justify-between md:items-center gap-4">
        <div>
          <h1 className="text-2xl md:text-3xl font-bold">Transactions</h1>
          <p className="text-sm md:text-base text-gray-600">View and categorize your transactions</p>
        </div>
        
        {/* Mobile Actions */}
        <div className="flex flex-col sm:flex-row gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => setShowFilters(!showFilters)}
            className="md:hidden"
          >
            <FunnelIcon className="h-4 w-4 mr-2" />
            Filters {Object.keys(filters).length > 0 && `(${Object.keys(filters).length})`}
          </Button>
          
          <div className="flex gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => refetch()}
              disabled={isLoading}
            >
              <ArrowPathIcon className={cn("h-4 w-4", isLoading && "animate-spin")} />
              <span className="hidden sm:inline ml-2">Refresh</span>
            </Button>
            
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="outline" size="sm">
                  <ArrowDownTrayIcon className="h-4 w-4" />
                  <span className="hidden sm:inline ml-2">Export</span>
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent>
                <DropdownMenuItem onClick={() => exportTransactionsMutation.mutate('csv')}>
                  <DocumentArrowDownIcon className="h-4 w-4 mr-2" />
                  Export as CSV
                </DropdownMenuItem>
                <DropdownMenuItem onClick={() => exportTransactionsMutation.mutate('excel')}>
                  <TableCellsIcon className="h-4 w-4 mr-2" />
                  Export as Excel
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </div>
      </div>

      {/* Totals Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 md:gap-4">
        <Card>
          <CardContent className="p-4 md:p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs md:text-sm text-gray-600">Income</p>
                <p className="text-lg md:text-2xl font-bold text-green-600">
                  {formatCurrency(totals.income)}
                </p>
              </div>
              <ArrowTrendingUpIcon className="h-6 w-6 md:h-8 md:w-8 text-green-500" />
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="p-4 md:p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs md:text-sm text-gray-600">Expenses</p>
                <p className="text-lg md:text-2xl font-bold text-red-600">
                  {formatCurrency(totals.expenses)}
                </p>
              </div>
              <ArrowTrendingDownIcon className="h-6 w-6 md:h-8 md:w-8 text-red-500" />
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="p-4 md:p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs md:text-sm text-gray-600">Balance</p>
                <p className={cn(
                  "text-lg md:text-2xl font-bold",
                  totals.balance >= 0 ? "text-green-600" : "text-red-600"
                )}>
                  {formatCurrency(totals.balance)}
                </p>
              </div>
              <CurrencyDollarIcon className="h-6 w-6 md:h-8 md:w-8 text-gray-500" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Search and Filters */}
      <div className="space-y-3">
        <div className="flex flex-col md:flex-row gap-3">
          {/* Search */}
          <div className="relative flex-1">
            <MagnifyingGlassIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
            <Input
              type="text"
              placeholder="Search transactions..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-10 w-full"
            />
            {searchTerm && (
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setSearchTerm('')}
                className="absolute right-1 top-1/2 transform -translate-y-1/2"
              >
                <XMarkIcon className="h-4 w-4" />
              </Button>
            )}
          </div>

          {/* Desktop Filters */}
          <div className="hidden md:block">
            <Popover>
              <PopoverTrigger asChild>
                <Button variant="outline">
                  <FunnelIcon className="h-4 w-4 mr-2" />
                  Filters {Object.keys(filters).length > 0 && `(${Object.keys(filters).length})`}
                </Button>
              </PopoverTrigger>
              <PopoverContent className="w-80">
                <FiltersContent 
                  filters={filters}
                  setFilters={setFilters}
                  accounts={accounts}
                  categories={categories}
                />
              </PopoverContent>
            </Popover>
          </div>
        </div>

        {/* Mobile Filters */}
        {showFilters && (
          <Card className="md:hidden">
            <CardContent className="p-4">
              <FiltersContent 
                filters={filters}
                setFilters={setFilters}
                accounts={accounts}
                categories={categories}
              />
            </CardContent>
          </Card>
        )}
      </div>

      {/* Bulk Actions */}
      {selectedTransactions.length > 0 && (
        <Card>
          <CardContent className="py-3 px-4">
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
              <p className="text-sm text-gray-600">
                {selectedTransactions.length} transaction(s) selected
              </p>
              <div className="flex flex-wrap items-center gap-2">
                <Select
                  onValueChange={(value) => {
                    if (value) {
                      bulkUpdateCategoryMutation.mutate({ 
                        transactionIds: selectedTransactions,
                        categoryId: value 
                      });
                    }
                  }}
                >
                  <SelectTrigger className="w-[180px] h-8">
                    <SelectValue placeholder="Bulk categorize" />
                  </SelectTrigger>
                  <SelectContent>
                    {categories.map((category) => (
                      <SelectItem key={category.id} value={category.id}>
                        <div className="flex items-center">
                          <span
                            className="w-3 h-3 rounded-full mr-2"
                            style={{ backgroundColor: category.color || '#gray' }}
                          />
                          {category.name}
                        </div>
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                <Button variant="outline" size="sm">
                  <TagIcon className="h-4 w-4 mr-2" />
                  Add Tags
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setSelectedTransactions([])}
                >
                  Clear Selection
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Transactions Table */}
      {transactions?.results && transactions.results.length > 0 ? (
        <>
          <Card className="overflow-hidden">
            <CardContent className="p-0">
              <div className="overflow-x-auto">
                <DataTable
                  columns={columns}
                  data={transactions.results}
                />
              </div>
            </CardContent>
          </Card>

          {/* Pagination */}
          <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
            <div className="flex items-center gap-2">
              <Label className="text-sm">Rows per page:</Label>
              <Select
                value={pageSize.toString()}
                onValueChange={(value) => {
                  setPageSize(parseInt(value));
                  setPage(1);
                }}
              >
                <SelectTrigger className="w-[70px] h-8">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="10">10</SelectItem>
                  <SelectItem value="20">20</SelectItem>
                  <SelectItem value="50">50</SelectItem>
                  <SelectItem value="100">100</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="flex items-center gap-2">
              <p className="text-sm text-gray-600">
                Page {page} of {totalPages} ({transactions.count} total)
              </p>
              <div className="flex gap-1">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setPage(page - 1)}
                  disabled={page === 1}
                >
                  <ChevronLeftIcon className="h-4 w-4" />
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setPage(page + 1)}
                  disabled={page === totalPages}
                >
                  <ChevronRightIcon className="h-4 w-4" />
                </Button>
              </div>
            </div>
          </div>
        </>
      ) : (
        <EmptyState
          icon={BanknotesIcon}
          title="No transactions found"
          description={searchTerm || Object.keys(filters).length > 0 
            ? "Try adjusting your search or filters" 
            : "Connect a bank account to start seeing your transactions"}
          action={
            searchTerm || Object.keys(filters).length > 0 ? (
              <Button onClick={() => {
                setSearchTerm('');
                setFilters({});
              }}>
                Clear Filters
              </Button>
            ) : (
              <HydrationBoundary>
                <Button onClick={() => {
                  // Safe navigation only on client
                  if (typeof window !== 'undefined') {
                    window.location.href = '/accounts';
                  }
                }}>
                  Connect Bank Account
                </Button>
              </HydrationBoundary>
            )
          }
        />
      )}

      {/* Note Edit Dialog */}
      {editingNote && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <Card className="w-full max-w-md">
            <CardHeader>
              <CardTitle>Edit Note</CardTitle>
            </CardHeader>
            <CardContent>
              <textarea
                value={noteText}
                onChange={(e) => setNoteText(e.target.value)}
                className="w-full h-24 p-2 border rounded-md"
                placeholder="Add a note..."
              />
              <div className="flex justify-end gap-2 mt-4">
                <Button
                  variant="outline"
                  onClick={() => {
                    setEditingNote(null);
                    setNoteText('');
                  }}
                >
                  Cancel
                </Button>
                <Button
                  onClick={() => {
                    updateNoteMutation.mutate({ id: editingNote, notes: noteText });
                  }}
                >
                  Save
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}

// Filters Component
function FiltersContent({ filters, setFilters, accounts, categories }: any) {
  return (
    <div className="space-y-4">
      <h4 className="font-medium">Filter Transactions</h4>
      
      <div>
        <Label>Account</Label>
        <Select
          value={filters.account_id || 'all'}
          onValueChange={(value) =>
            setFilters({ ...filters, account_id: value === 'all' ? undefined : value })
          }
        >
          <SelectTrigger>
            <SelectValue placeholder="All accounts" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All accounts</SelectItem>
            {accounts?.results?.map((account: any) => (
              <SelectItem key={account.id} value={account.id}>
                {account.account_name}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      <div>
        <Label>Category</Label>
        <Select
          value={filters.category_id || 'all'}
          onValueChange={(value) =>
            setFilters({ ...filters, category_id: value === 'all' ? undefined : value })
          }
        >
          <SelectTrigger>
            <SelectValue placeholder="All categories" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All categories</SelectItem>
            <SelectItem value="uncategorized">Uncategorized</SelectItem>
            {categories.map((category: any) => (
              <SelectItem key={category.id} value={category.id}>
                <div className="flex items-center">
                  <span
                    className="w-3 h-3 rounded-full mr-2"
                    style={{ backgroundColor: category.color || '#gray' }}
                  />
                  {category.name}
                </div>
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      <div>
        <Label>Transaction Type</Label>
        <Select
          value={filters.transaction_type || 'all'}
          onValueChange={(value) =>
            setFilters({
              ...filters,
              transaction_type: value === 'all' ? undefined : (value as 'debit' | 'credit'),
            })
          }
        >
          <SelectTrigger>
            <SelectValue placeholder="All types" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All types</SelectItem>
            <SelectItem value="credit">Income</SelectItem>
            <SelectItem value="debit">Expense</SelectItem>
          </SelectContent>
        </Select>
      </div>

      <div className="grid grid-cols-2 gap-2">
        <div>
          <Label>From Date</Label>
          <HydrationBoundary fallback={<div className="h-10 bg-gray-100 rounded animate-pulse" />}>
            <DatePicker
              date={filters.start_date ? new Date(filters.start_date) : undefined}
              onDateChange={(date) =>
                setFilters({
                  ...filters,
                  start_date: date?.toISOString().split('T')[0],
                })
              }
            />
          </HydrationBoundary>
        </div>
        <div>
          <Label>To Date</Label>
          <HydrationBoundary fallback={<div className="h-10 bg-gray-100 rounded animate-pulse" />}>
            <DatePicker
              date={filters.end_date ? new Date(filters.end_date) : undefined}
              onDateChange={(date) =>
                setFilters({
                  ...filters,
                  end_date: date?.toISOString().split('T')[0],
                })
              }
            />
          </HydrationBoundary>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-2">
        <div>
          <Label>Min Amount</Label>
          <Input
            type="number"
            placeholder="0.00"
            value={filters.min_amount || ''}
            onChange={(e) =>
              setFilters({
                ...filters,
                min_amount: e.target.value ? parseFloat(e.target.value) : undefined,
              })
            }
          />
        </div>
        <div>
          <Label>Max Amount</Label>
          <Input
            type="number"
            placeholder="0.00"
            value={filters.max_amount || ''}
            onChange={(e) =>
              setFilters({
                ...filters,
                max_amount: e.target.value ? parseFloat(e.target.value) : undefined,
              })
            }
          />
        </div>
      </div>

      <Button
        variant="outline"
        className="w-full"
        onClick={() => setFilters({})}
      >
        Clear Filters
      </Button>
    </div>
  );
}