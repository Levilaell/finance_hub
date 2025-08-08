'use client';

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { billingService, BillingTransaction } from '@/services/billing.service';
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

  // Fetch real billing data
  const { data: transactions, isLoading } = useQuery({
    queryKey: ['billing-history', statusFilter, searchTerm],
    queryFn: async () => {
      const response = await billingService.getPaymentHistory({
        status: statusFilter === 'all' ? undefined : statusFilter,
        search: searchTerm || undefined,
      });
      // Ensure we always return an array
      if (Array.isArray(response)) {
        return response;
      }
      // If response is an object with data property, return the data
      if (response && typeof response === 'object' && 'data' in response && Array.isArray((response as any).data)) {
        return (response as any).data;
      }
      return [];
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

  // Since filtering is now done server-side, we don't need client-side filtering
  const filteredTransactions = transactions;

  const handleDownloadInvoice = async (transaction: BillingTransaction) => {
    try {
      const result = await billingService.downloadInvoice(transaction.id);
      window.open(result.download_url, '_blank');
    } catch (error) {
      console.error('Error downloading invoice:', error);
    }
  };

  const handleExportHistory = () => {
    // Simulate export
    const csvData = filteredTransactions?.map((t: any) => 
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
                filteredTransactions?.map((transaction: any) => {
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
                                    {formatDate(transaction.transaction_date)}
                                  </span>
                                  <span>
                                    {transaction.payment_method_display}
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
                          .filter((t: any) => t.status === 'paid')
                          .reduce((sum: number, t: any) => sum + t.amount, 0)
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