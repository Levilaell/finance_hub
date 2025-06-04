'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '@/store/auth-store';
import { useBankingStore } from '@/store/banking-store';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { LoadingSpinner } from '@/components/ui/loading-spinner';
import { ErrorMessage } from '@/components/ui/error-message';
import { formatCurrency } from '@/lib/utils';
import { 
  PlusIcon, 
  ArrowLeftIcon,
  CurrencyDollarIcon,
  BanknotesIcon
} from '@heroicons/react/24/outline';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { toast } from 'sonner';

interface TransactionForm {
  account_id: string;
  amount: string;
  description: string;
  transaction_type: 'credit' | 'debit';
  category_id?: string;
  date: string;
}

export default function NewTransactionPage() {
  const router = useRouter();
  const { isAuthenticated } = useAuthStore();
  const { accounts, fetchAccounts, loading } = useBankingStore();
  
  const [form, setForm] = useState<TransactionForm>({
    account_id: '',
    amount: '',
    description: '',
    transaction_type: 'debit',
    category_id: '',
    date: ''
  });

  // Set current date on client-side after hydration
  useEffect(() => {
    setForm(prev => ({
      ...prev,
      date: new Date().toISOString().split('T')[0]
    }));
  }, []);
  
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [categories, setCategories] = useState<any[]>([]);

  useEffect(() => {
    if (!isAuthenticated) {
      router.push('/login');
      return;
    }

    fetchAccounts();
    fetchCategories();
  }, [isAuthenticated]);

  const fetchCategories = async () => {
    try {
      const token = typeof window !== 'undefined' ? localStorage.getItem('access_token') : null;
      if (!token) return;

      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/categories/`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });
      
      if (response.ok) {
        const data = await response.json();
        setCategories(data);
      }
    } catch (error) {
      console.error('Error fetching categories:', error);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!form.account_id || !form.amount || !form.description) {
      toast.error('Preencha todos os campos obrigatórios');
      return;
    }

    setIsSubmitting(true);
    
    try {
      const token = typeof window !== 'undefined' ? localStorage.getItem('access_token') : null;
      if (!token) {
        toast.error('Token de autenticação não encontrado');
        return;
      }

      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/banking/transactions/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({
          account: form.account_id,
          amount: parseFloat(form.amount),
          description: form.description,
          transaction_type: form.transaction_type,
          category: form.category_id || null,
          transaction_date: form.date,
        }),
      });

      if (response.ok) {
        toast.success('Transação adicionada com sucesso!');
        router.push('/transactions');
      } else {
        const error = await response.json();
        toast.error(error.detail || 'Erro ao adicionar transação');
      }
    } catch (error) {
      console.error('Error creating transaction:', error);
      toast.error('Erro ao adicionar transação');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleInputChange = (field: keyof TransactionForm, value: string) => {
    setForm(prev => ({ ...prev, [field]: value }));
  };

  if (loading && accounts.length === 0) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <LoadingSpinner />
      </div>
    );
  }

  return (
    <div className="space-y-6">
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
          <h1 className="text-3xl font-bold text-gray-900">Nova Transação</h1>
          <p className="text-gray-600 mt-1">
            Adicione uma nova transação manual
          </p>
        </div>
      </div>

      {/* Form */}
      <Card className="max-w-2xl">
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <PlusIcon className="h-5 w-5" />
            <span>Detalhes da Transação</span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Account Selection */}
            <div>
              <Label htmlFor="account">Conta *</Label>
              <Select value={form.account_id} onValueChange={(value) => handleInputChange('account_id', value)}>
                <SelectTrigger>
                  <SelectValue placeholder="Selecione uma conta" />
                </SelectTrigger>
                <SelectContent>
                  {(accounts || []).map((account) => (
                    <SelectItem key={account.id} value={account.id.toString()}>
                      <div className="flex items-center space-x-2">
                        <BanknotesIcon className="h-4 w-4" />
                        <span>{account.display_name || account.nickname}</span>
                        <span className="text-gray-500">
                          ({account.bank_provider?.name})
                        </span>
                      </div>
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {/* Transaction Type */}
            <div>
              <Label htmlFor="type">Tipo *</Label>
              <Select value={form.transaction_type} onValueChange={(value: 'credit' | 'debit') => handleInputChange('transaction_type', value)}>
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
                  id="amount"
                  type="number"
                  step="0.01"
                  placeholder="0.00"
                  value={form.amount}
                  onChange={(e) => handleInputChange('amount', e.target.value)}
                  className="pl-10"
                  required
                />
              </div>
            </div>

            {/* Description */}
            <div>
              <Label htmlFor="description">Descrição *</Label>
              <Input
                id="description"
                placeholder="Ex: Pagamento da conta de luz"
                value={form.description}
                onChange={(e) => handleInputChange('description', e.target.value)}
                required
              />
            </div>

            {/* Category */}
            <div>
              <Label htmlFor="category">Categoria</Label>
              <Select value={form.category_id} onValueChange={(value) => handleInputChange('category_id', value)}>
                <SelectTrigger>
                  <SelectValue placeholder="Selecione uma categoria (opcional)" />
                </SelectTrigger>
                <SelectContent>
                  {categories.map((category) => (
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
              <Label htmlFor="date">Data *</Label>
              <Input
                id="date"
                type="date"
                value={form.date}
                onChange={(e) => handleInputChange('date', e.target.value)}
                required
              />
            </div>

            {/* Submit Buttons */}
            <div className="flex space-x-3 pt-6">
              <Button
                type="button"
                variant="outline"
                onClick={() => router.back()}
                className="flex-1"
              >
                Cancelar
              </Button>
              <Button
                type="submit"
                disabled={isSubmitting}
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
          </form>
        </CardContent>
      </Card>
    </div>
  );
}