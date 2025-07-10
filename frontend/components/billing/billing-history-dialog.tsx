'use client';

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { LoadingSpinner } from '@/components/ui/loading-spinner';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { formatCurrency, formatDate } from '@/utils/billing.utils';
import { 
  CalendarIcon, 
  DocumentTextIcon, 
  CreditCardIcon,
  FunnelIcon,
  ArrowDownTrayIcon
} from '@heroicons/react/24/outline';

interface BillingTransaction {
  id: string;
  date: string;
  description: string;
  amount: number;
  status: 'paid' | 'pending' | 'failed' | 'refunded';
  payment_method: string;
  invoice_url?: string;
  plan_name?: string;
}

interface BillingHistoryDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function BillingHistoryDialog({
  open,
  onOpenChange
}: BillingHistoryDialogProps) {
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');

  // Mock data - substituir pela API real
  const mockTransactions: BillingTransaction[] = [
    {
      id: '1',
      date: '2024-01-15T10:30:00Z',
      description: 'Assinatura mensal - Plano Profissional',
      amount: 99.90,
      status: 'paid',
      payment_method: 'Cartão •••• 4532',
      invoice_url: '#',
      plan_name: 'Profissional'
    },
    {
      id: '2',
      date: '2023-12-15T10:30:00Z',
      description: 'Assinatura mensal - Plano Profissional',
      amount: 99.90,
      status: 'paid',
      payment_method: 'Cartão •••• 4532',
      invoice_url: '#',
      plan_name: 'Profissional'
    },
    {
      id: '3',
      date: '2023-11-15T10:30:00Z',
      description: 'Upgrade para Plano Profissional',
      amount: 79.90,
      status: 'paid',
      payment_method: 'PIX',
      invoice_url: '#',
      plan_name: 'Profissional'
    },
    {
      id: '4',
      date: '2023-10-15T10:30:00Z',
      description: 'Assinatura mensal - Plano Starter',
      amount: 49.90,
      status: 'failed',
      payment_method: 'Cartão •••• 1234',
      plan_name: 'Starter'
    }
  ];

  // Simulate API call
  const { data: transactions, isLoading } = useQuery({
    queryKey: ['billing-history'],
    queryFn: async () => {
      // Simulate API delay
      await new Promise(resolve => setTimeout(resolve, 1000));
      return mockTransactions;
    },
    enabled: open,
  });

  const getStatusInfo = (status: string) => {
    const statusMap = {
      paid: {
        label: 'Pago',
        color: 'bg-green-100 text-green-800',
      },
      pending: {
        label: 'Pendente',
        color: 'bg-yellow-100 text-yellow-800',
      },
      failed: {
        label: 'Falhou',
        color: 'bg-red-100 text-red-800',
      },
      refunded: {
        label: 'Reembolsado',
        color: 'bg-gray-100 text-gray-800',
      }
    };
    return statusMap[status as keyof typeof statusMap] || statusMap.pending;
  };

  const filteredTransactions = transactions?.filter(transaction => {
    const matchesSearch = transaction.description.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         transaction.plan_name?.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesStatus = statusFilter === 'all' || transaction.status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  const handleDownloadInvoice = (transaction: BillingTransaction) => {
    if (transaction.invoice_url) {
      // Simulate download
      window.open(transaction.invoice_url, '_blank');
    }
  };

  const handleExportHistory = () => {
    // Simulate export
    const csvData = filteredTransactions?.map(t => 
      `${t.date},${t.description},${t.amount},${t.status},${t.payment_method}`
    ).join('\n');
    
    const csvContent = `data:text/csv;charset=utf-8,Data,Descrição,Valor,Status,Método de Pagamento\n${csvData}`;
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement('a');
    link.setAttribute('href', encodedUri);
    link.setAttribute('download', 'historico-cobranca.csv');
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center">
            <DocumentTextIcon className="h-5 w-5 mr-2" />
            Histórico de Cobrança
          </DialogTitle>
          <DialogDescription>
            Visualize todas as suas transações e faturas anteriores.
          </DialogDescription>
        </DialogHeader>

        {isLoading ? (
          <div className="flex justify-center py-8">
            <LoadingSpinner />
          </div>
        ) : (
          <div className="space-y-4">
            {/* Filters */}
            <div className="flex flex-col sm:flex-row gap-4">
              <div className="flex-1">
                <Label htmlFor="search">Buscar transações</Label>
                <Input
                  id="search"
                  placeholder="Buscar por descrição ou plano..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                />
              </div>
              
              <div className="sm:w-48">
                <Label htmlFor="status">Filtrar por status</Label>
                <select
                  id="status"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  value={statusFilter}
                  onChange={(e) => setStatusFilter(e.target.value)}
                >
                  <option value="all">Todos</option>
                  <option value="paid">Pago</option>
                  <option value="pending">Pendente</option>
                  <option value="failed">Falhou</option>
                  <option value="refunded">Reembolsado</option>
                </select>
              </div>

              <div className="flex items-end">
                <Button
                  variant="outline"
                  onClick={handleExportHistory}
                  className="flex items-center"
                >
                  <ArrowDownTrayIcon className="h-4 w-4 mr-2" />
                  Exportar
                </Button>
              </div>
            </div>

            {/* Transaction List */}
            <div className="space-y-3">
              {filteredTransactions?.length === 0 ? (
                <div className="text-center py-8 text-gray-500">
                  <DocumentTextIcon className="h-12 w-12 mx-auto mb-4 opacity-30" />
                  <p>Nenhuma transação encontrada</p>
                </div>
              ) : (
                filteredTransactions?.map((transaction) => {
                  const statusInfo = getStatusInfo(transaction.status);
                  
                  return (
                    <Card key={transaction.id} className="hover:shadow-md transition-shadow">
                      <CardContent className="p-4">
                        <div className="flex items-center justify-between">
                          <div className="flex-1">
                            <div className="flex items-center space-x-3">
                              <div className="p-2 bg-blue-50 rounded-lg">
                                <CreditCardIcon className="h-5 w-5 text-blue-600" />
                              </div>
                              
                              <div className="flex-1">
                                <h4 className="font-medium text-gray-900">
                                  {transaction.description}
                                </h4>
                                <div className="flex items-center space-x-4 text-sm text-gray-600 mt-1">
                                  <span className="flex items-center">
                                    <CalendarIcon className="h-4 w-4 mr-1" />
                                    {formatDate(transaction.date)}
                                  </span>
                                  <span>
                                    {transaction.payment_method}
                                  </span>
                                </div>
                              </div>
                            </div>
                          </div>

                          <div className="flex items-center space-x-4">
                            <div className="text-right">
                              <div className="font-semibold text-lg">
                                {formatCurrency(transaction.amount)}
                              </div>
                              <Badge className={statusInfo.color}>
                                {statusInfo.label}
                              </Badge>
                            </div>

                            {transaction.invoice_url && transaction.status === 'paid' && (
                              <Button
                                variant="outline"
                                size="sm"
                                onClick={() => handleDownloadInvoice(transaction)}
                              >
                                <ArrowDownTrayIcon className="h-4 w-4 mr-1" />
                                Fatura
                              </Button>
                            )}
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  );
                })
              )}
            </div>

            {/* Summary */}
            {filteredTransactions && filteredTransactions.length > 0 && (
              <div className="bg-gray-50 p-4 rounded-lg">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-center">
                  <div>
                    <p className="text-sm text-gray-600">Total de Transações</p>
                    <p className="text-lg font-semibold">{filteredTransactions.length}</p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-600">Total Pago</p>
                    <p className="text-lg font-semibold text-green-600">
                      {formatCurrency(
                        filteredTransactions
                          .filter(t => t.status === 'paid')
                          .reduce((sum, t) => sum + t.amount, 0)
                      )}
                    </p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-600">Próxima Cobrança</p>
                    <p className="text-lg font-semibold">15/02/2024</p>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}