'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useQuery, useMutation } from '@tanstack/react-query';
import { useAuthStore } from '@/store/auth-store';
import { bankingService } from '@/services/banking.service';
import { categoriesService } from '@/services/categories.service';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { LoadingSpinner } from '@/components/ui/loading-spinner';
import { formatCurrency } from '@/lib/utils';
import { 
  PlusIcon, 
  ArrowLeftIcon,
  CurrencyDollarIcon,
  BanknotesIcon,
  CalendarIcon,
  TagIcon,
  CheckCircleIcon,
  ExclamationCircleIcon,
  ExclamationTriangleIcon
} from '@heroicons/react/24/outline';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { toast } from 'sonner';
import { Textarea } from '@/components/ui/textarea';
import { z } from 'zod';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';

// Validation schema
const transactionSchema = z.object({
  bank_account: z.string().min(1, 'Selecione uma conta'),
  amount: z.string()
    .min(1, 'Valor é obrigatório')
    .refine((val) => {
      const num = parseFloat(val);
      return !isNaN(num) && num > 0;
    }, 'Valor deve ser maior que zero'),
  description: z.string().min(3, 'Descrição deve ter pelo menos 3 caracteres'),
  transaction_type: z.enum(['credit', 'debit']),
  category: z.string().optional(),
  transaction_date: z.string().min(1, 'Data é obrigatória'),
  notes: z.string().optional(),
  tags: z.string().optional(),
});

type TransactionFormData = z.infer<typeof transactionSchema>;

export default function NewTransactionPage() {
  const router = useRouter();
  const { isAuthenticated } = useAuthStore();
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Queries
  const { data: accountsData, isLoading: accountsLoading } = useQuery({
    queryKey: ['bank-accounts'],
    queryFn: () => bankingService.getBankAccounts(),
    enabled: isAuthenticated,
  });

  const { data: categoriesData, isLoading: categoriesLoading } = useQuery({
    queryKey: ['categories'],
    queryFn: () => categoriesService.getCategories(),
    enabled: isAuthenticated,
  });

  const accounts = accountsData?.results || [];
  const categories = categoriesData || [];

  // Form setup
  const {
    register,
    handleSubmit,
    watch,
    setValue,
    formState: { errors },
  } = useForm<TransactionFormData>({
    resolver: zodResolver(transactionSchema),
    defaultValues: {
      bank_account: '',
      amount: '',
      description: '',
      transaction_type: 'debit',
      category: '',
      transaction_date: new Date().toISOString().split('T')[0],
      notes: '',
      tags: '',
    },
  });

  const transactionType = watch('transaction_type');

  // Create transaction mutation
  const createMutation = useMutation({
    mutationFn: async (data: TransactionFormData) => {
      const tags = data.tags ? data.tags.split(',').map(tag => tag.trim()).filter(Boolean) : [];
      
      return bankingService.createTransaction({
        bank_account: data.bank_account,
        amount: parseFloat(data.amount),
        description: data.description,
        transaction_type: data.transaction_type,
        category: data.category || undefined,
        transaction_date: data.transaction_date,
        notes: data.notes || undefined,
        tags: tags.length > 0 ? tags : undefined,
      });
    },
    onSuccess: (data) => {
      // Check for usage warnings in the response
      if ((data as any).usage_warning) {
        const warning = (data as any).usage_warning;
        
        if (warning.upgrade_suggestion) {
          // Show upgrade suggestion for 90%+ usage
          toast.warning(warning.message, {
            description: `${warning.remaining} transações restantes este mês`,
            action: {
              label: 'Fazer Upgrade',
              onClick: () => router.push('/settings?tab=billing')
            },
            duration: 10000,
            icon: <ExclamationTriangleIcon className="h-5 w-5 text-orange-500" />,
          });
        } else {
          // Show warning for 80%+ usage
          toast.info(warning.message, {
            description: `${warning.remaining} transações restantes este mês`,
            duration: 8000,
            icon: <ExclamationCircleIcon className="h-5 w-5 text-yellow-500" />,
          });
        }
        
        // Still show success message but shorter duration
        setTimeout(() => {
          toast.success('Transação adicionada com sucesso!', {
            description: 'A transação foi registrada.',
            icon: <CheckCircleIcon className="h-5 w-5 text-green-500" />,
            duration: 3000
          });
        }, 500);
      } else {
        // No warning, show normal success
        toast.success('Transação adicionada com sucesso!', {
          description: 'A transação foi registrada e será categorizada automaticamente.',
          icon: <CheckCircleIcon className="h-5 w-5 text-green-500" />,
        });
      }
      
      router.push('/transactions');
    },
    onError: (error: any) => {
      console.error('Error creating transaction:', error);
      toast.error('Erro ao adicionar transação', {
        description: error.response?.data?.detail || 'Verifique os dados e tente novamente.',
        icon: <ExclamationCircleIcon className="h-5 w-5 text-red-500" />,
      });
    },
  });

  const onSubmit = async (data: TransactionFormData) => {
    setIsSubmitting(true);
    try {
      await createMutation.mutateAsync(data);
    } finally {
      setIsSubmitting(false);
    }
  };

  // Redirect if not authenticated
  useEffect(() => {
    if (!isAuthenticated) {
      router.push('/login');
    }
  }, [isAuthenticated, router]);

  if (accountsLoading || categoriesLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <LoadingSpinner />
      </div>
    );
  }

  // Filter categories based on transaction type
  const filteredCategories = categories.filter(cat => {
    if (transactionType === 'credit') {
      return cat.category_type === 'income';
    } else {
      return cat.category_type === 'expense';
    }
  });

  return (
    <div className="max-w-2xl mx-auto space-y-6 p-4 md:p-6">
      {/* Header */}
      <div className="flex items-center space-x-4">
        <Button 
          variant="outline" 
          onClick={() => router.back()}
          className="flex items-center space-x-2"
        >
          <ArrowLeftIcon className="h-4 w-4" />
          <span>Voltar</span>
        </Button>
        <div>
          <h1 className="text-2xl md:text-3xl font-bold text-gray-900">Nova Transação</h1>
          <p className="text-gray-600 mt-1">
            Adicione uma nova transação manual
          </p>
        </div>
      </div>

      {/* Form */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <PlusIcon className="h-5 w-5" />
            <span>Detalhes da Transação</span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
            {/* Account Selection */}
            <div>
              <Label htmlFor="bank_account">Conta *</Label>
              <Select 
                value={watch('bank_account')} 
                onValueChange={(value) => setValue('bank_account', value)}
              >
                <SelectTrigger className={errors.bank_account ? 'border-red-500' : ''}>
                  <SelectValue placeholder="Selecione uma conta" />
                </SelectTrigger>
                <SelectContent>
                  {accounts.length === 0 ? (
                    <div className="p-4 text-center text-gray-500">
                      <p className="text-sm">Nenhuma conta conectada</p>
                      <Button
                        variant="link"
                        size="sm"
                        onClick={() => router.push('/accounts')}
                        className="mt-2"
                      >
                        Conectar conta
                      </Button>
                    </div>
                  ) : (
                    accounts.map((account) => (
                      <SelectItem key={account.id} value={account.id.toString()}>
                        <div className="flex items-center space-x-2">
                          <BanknotesIcon className="h-4 w-4" />
                          <span>{account.account_name}</span>
                          <span className="text-gray-500 text-sm">
                            • {formatCurrency(account.current_balance)}
                          </span>
                        </div>
                      </SelectItem>
                    ))
                  )}
                </SelectContent>
              </Select>
              {errors.bank_account && (
                <p className="text-red-500 text-sm mt-1">{errors.bank_account.message}</p>
              )}
            </div>

            {/* Transaction Type */}
            <div>
              <Label htmlFor="transaction_type">Tipo *</Label>
              <Select 
                value={watch('transaction_type')} 
                onValueChange={(value: 'credit' | 'debit') => setValue('transaction_type', value)}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="credit">
                    <div className="flex items-center space-x-2">
                      <div className="w-3 h-3 bg-green-500 rounded-full"></div>
                      <span>Receita</span>
                    </div>
                  </SelectItem>
                  <SelectItem value="debit">
                    <div className="flex items-center space-x-2">
                      <div className="w-3 h-3 bg-red-500 rounded-full"></div>
                      <span>Despesa</span>
                    </div>
                  </SelectItem>
                </SelectContent>
              </Select>
            </div>

            {/* Amount */}
            <div>
              <Label htmlFor="amount">Valor *</Label>
              <div className="relative">
                <CurrencyDollarIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                <Input
                  {...register('amount')}
                  id="amount"
                  type="number"
                  step="0.01"
                  placeholder="0.00"
                  className={`pl-10 ${errors.amount ? 'border-red-500' : ''}`}
                />
              </div>
              {errors.amount && (
                <p className="text-red-500 text-sm mt-1">{errors.amount.message}</p>
              )}
            </div>

            {/* Description */}
            <div>
              <Label htmlFor="description">Descrição *</Label>
              <Input
                {...register('description')}
                id="description"
                placeholder="Ex: Pagamento da conta de luz"
                className={errors.description ? 'border-red-500' : ''}
              />
              {errors.description && (
                <p className="text-red-500 text-sm mt-1">{errors.description.message}</p>
              )}
            </div>

            {/* Category */}
            <div>
              <Label htmlFor="category">
                Categoria 
                <span className="text-gray-500 text-xs ml-2">(Pluggy irá categorizar automaticamente)</span>
              </Label>
              <Select 
                value={watch('category') || 'auto'} 
                onValueChange={(value) => setValue('category', value === 'auto' ? '' : value)}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Selecione uma categoria (opcional)" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="auto">
                    <span className="text-gray-500">Deixar Pluggy categorizar</span>
                  </SelectItem>
                  {filteredCategories.map((category) => (
                    <SelectItem key={category.id} value={category.id.toString()}>
                      <div className="flex items-center space-x-2">
                        <div 
                          className="w-3 h-3 rounded-full" 
                          style={{ backgroundColor: category.color || '#6B7280' }}
                        ></div>
                        <span>{category.name}</span>
                      </div>
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {/* Date */}
            <div>
              <Label htmlFor="transaction_date">Data *</Label>
              <div className="relative">
                <CalendarIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                <Input
                  {...register('transaction_date')}
                  id="transaction_date"
                  type="date"
                  className={`pl-10 ${errors.transaction_date ? 'border-red-500' : ''}`}
                />
              </div>
              {errors.transaction_date && (
                <p className="text-red-500 text-sm mt-1">{errors.transaction_date.message}</p>
              )}
            </div>

            {/* Notes */}
            <div>
              <Label htmlFor="notes">Notas (opcional)</Label>
              <Textarea
                {...register('notes')}
                id="notes"
                placeholder="Adicione observações sobre esta transação..."
                rows={3}
              />
            </div>

            {/* Tags */}
            <div>
              <Label htmlFor="tags">
                Tags 
                <span className="text-gray-500 text-xs ml-2">(separe por vírgulas)</span>
              </Label>
              <div className="relative">
                <TagIcon className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
                <Input
                  {...register('tags')}
                  id="tags"
                  placeholder="Ex: viagem, projeto-x, urgente"
                  className="pl-10"
                />
              </div>
            </div>

            {/* Submit Buttons */}
            <div className="flex space-x-3 pt-6">
              <Button
                type="button"
                variant="outline"
                onClick={() => router.back()}
                className="flex-1"
                disabled={isSubmitting}
              >
                Cancelar
              </Button>
              <Button
                type="submit"
                disabled={isSubmitting || accounts.length === 0}
                className="flex-1"
              >
                {isSubmitting ? (
                  <>
                    <LoadingSpinner className="h-4 w-4 mr-2" />
                    Adicionando...
                  </>
                ) : (
                  <>
                    <PlusIcon className="h-4 w-4 mr-2" />
                    Adicionar Transação
                  </>
                )}
              </Button>
            </div>

            {accounts.length === 0 && (
              <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 mt-4">
                <div className="flex items-start">
                  <ExclamationCircleIcon className="h-5 w-5 text-yellow-600 mt-0.5" />
                  <div className="ml-3">
                    <p className="text-sm text-yellow-800">
                      Você precisa conectar uma conta bancária antes de adicionar transações.
                    </p>
                    <Button
                      variant="link"
                      size="sm"
                      onClick={() => router.push('/accounts')}
                      className="mt-2 p-0 h-auto text-yellow-800 hover:text-yellow-900"
                    >
                      Conectar conta agora →
                    </Button>
                  </div>
                </div>
              </div>
            )}
          </form>
        </CardContent>
      </Card>
    </div>
  );
}