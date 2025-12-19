'use client';

import { useEffect, useState } from 'react';
import { bankingService } from '@/services/banking.service';
import { Transaction, BillSuggestionExtended } from '@/types/banking';
import { format } from 'date-fns';
import { ptBR } from 'date-fns/locale';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { LoadingSpinner } from '@/components/ui/loading-spinner';
import { Badge } from '@/components/ui/badge';
import { formatCurrency } from '@/lib/utils';
import {
  LinkIcon,
  BanknotesIcon,
  CalendarIcon,
  DocumentTextIcon,
  UserIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon,
} from '@heroicons/react/24/outline';
import { toast } from 'sonner';

interface LinkBillDialogProps {
  transaction: Transaction | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onLinked: () => void;
}

export function LinkBillDialog({
  transaction,
  open,
  onOpenChange,
  onLinked,
}: LinkBillDialogProps) {
  const [suggestions, setSuggestions] = useState<BillSuggestionExtended[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isLinking, setIsLinking] = useState<string | null>(null);

  useEffect(() => {
    if (open && transaction) {
      fetchSuggestions();
    }
  }, [open, transaction]);

  const fetchSuggestions = async () => {
    if (!transaction) return;

    setIsLoading(true);
    try {
      // Use the new endpoint that returns ALL pending bills
      const data = await bankingService.getAllPendingBills(transaction.id);
      setSuggestions(data);
    } catch (error) {
      console.error('Error fetching suggestions:', error);
      toast.error('Erro ao buscar contas');
    } finally {
      setIsLoading(false);
    }
  };

  const handleLink = async (bill: BillSuggestionExtended) => {
    if (!transaction) return;

    setIsLinking(bill.id);
    try {
      // Use the new manual link endpoint
      const result = await bankingService.linkBillManual(transaction.id, bill.id);
      toast.success(result.message);
      onLinked();
      onOpenChange(false);
    } catch (error: any) {
      console.error('Error linking bill:', error);
      toast.error(error?.response?.data?.error || 'Erro ao vincular conta');
    } finally {
      setIsLinking(null);
    }
  };

  const getRelevanceColor = (score: number) => {
    if (score >= 80) return 'bg-green-500';
    if (score >= 60) return 'bg-yellow-500';
    if (score >= 40) return 'bg-orange-500';
    return 'bg-red-500';
  };

  const getRelevanceLabel = (score: number) => {
    if (score >= 80) return 'Alta';
    if (score >= 60) return 'Media';
    if (score >= 40) return 'Baixa';
    return 'Muito Baixa';
  };

  const getTypeLabel = (type: string) => {
    return type === 'receivable' ? 'A Receber' : 'A Pagar';
  };

  const getTypeColor = (type: string) => {
    return type === 'receivable' ? 'text-green-500' : 'text-red-500';
  };

  const getAmountDiffLabel = (bill: BillSuggestionExtended) => {
    if (bill.amount_match) {
      return null; // No warning needed
    }

    const txAmount = transaction ? Math.abs(transaction.amount) : 0;
    const diff = Math.abs(bill.amount_diff);

    if (bill.would_overpay) {
      return {
        type: 'warning' as const,
        message: `Transacao R$ ${txAmount.toFixed(2)} > Conta R$ ${bill.amount_remaining.toFixed(2)}. Sera registrado R$ ${bill.amount_remaining.toFixed(2)}.`,
      };
    } else {
      return {
        type: 'info' as const,
        message: `Transacao R$ ${txAmount.toFixed(2)} < Conta R$ ${bill.amount_remaining.toFixed(2)}. Pagamento parcial de R$ ${txAmount.toFixed(2)}.`,
      };
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="w-[95vw] max-w-2xl max-h-[85vh] overflow-y-auto p-4 sm:p-6">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2 text-base sm:text-lg">
            <LinkIcon className="h-5 w-5" />
            Vincular a Conta
          </DialogTitle>
          <DialogDescription className="text-xs sm:text-sm">
            Selecione uma conta para vincular a esta transacao.
          </DialogDescription>
        </DialogHeader>

        {transaction && (
          <div className="bg-muted/50 rounded-lg p-3 sm:p-4 mb-3 sm:mb-4">
            <h3 className="font-semibold text-sm sm:text-lg line-clamp-2">{transaction.description}</h3>
            <div className="flex flex-wrap items-center gap-2 sm:gap-4 mt-2 text-xs sm:text-sm text-muted-foreground">
              <span className={`flex items-center gap-1 font-medium ${
                transaction.type === 'CREDIT' ? 'text-green-500' : 'text-red-500'
              }`}>
                <BanknotesIcon className="h-4 w-4" />
                {transaction.type === 'CREDIT' ? '+' : '-'}
                {formatCurrency(Math.abs(transaction.amount))}
              </span>
              <span className="flex items-center gap-1">
                <CalendarIcon className="h-4 w-4" />
                {format(new Date(transaction.date), 'dd/MM/yyyy', { locale: ptBR })}
              </span>
              <span className="truncate max-w-[120px] sm:max-w-none">{transaction.account_name}</span>
            </div>
            {transaction.merchant_name && (
              <p className="text-xs text-muted-foreground mt-1 truncate">
                {transaction.merchant_name}
              </p>
            )}
          </div>
        )}

        {isLoading ? (
          <div className="flex items-center justify-center py-8 sm:py-12">
            <LoadingSpinner />
          </div>
        ) : suggestions.length > 0 ? (
          <div className="space-y-2 sm:space-y-3">
            <p className="text-xs sm:text-sm text-muted-foreground">
              {suggestions.length} conta(s) encontrada(s)
            </p>
            {suggestions.map((bill) => {
              const amountInfo = getAmountDiffLabel(bill);
              return (
                <div
                  key={bill.id}
                  className="p-3 sm:p-4 border border-white/10 rounded-lg hover:bg-white/5 transition-colors"
                >
                  <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-3 sm:gap-4">
                    <div className="flex-1 min-w-0">
                      <div className="flex flex-wrap items-start gap-1.5 sm:gap-2">
                        <h4 className="font-medium text-sm sm:text-base line-clamp-2 break-words w-full sm:w-auto">{bill.description}</h4>
                        <div className="flex flex-wrap gap-1.5">
                          <Badge
                            variant="outline"
                            className={`${getTypeColor(bill.type)} text-xs`}
                          >
                            {getTypeLabel(bill.type)}
                          </Badge>
                          {bill.amount_match ? (
                            <Badge className="bg-green-500 text-white text-xs">
                              <CheckCircleIcon className="h-3 w-3 mr-1" />
                              Valor exato
                            </Badge>
                          ) : (
                            <Badge
                              className={`${getRelevanceColor(bill.relevance_score)} text-white text-xs`}
                            >
                              {getRelevanceLabel(bill.relevance_score)}
                            </Badge>
                          )}
                        </div>
                      </div>
                      <div className="flex flex-wrap items-center gap-x-3 gap-y-1 mt-2 text-xs sm:text-sm text-muted-foreground">
                        <span className="flex items-center gap-1">
                          <BanknotesIcon className="h-3 w-3 flex-shrink-0" />
                          <span>{formatCurrency(bill.amount)}</span>
                          {bill.amount_remaining !== bill.amount && (
                            <span className="text-yellow-500">
                              (resta {formatCurrency(bill.amount_remaining)})
                            </span>
                          )}
                        </span>
                        <span className="flex items-center gap-1">
                          <CalendarIcon className="h-3 w-3 flex-shrink-0" />
                          {format(new Date(bill.due_date), 'dd/MM/yy', { locale: ptBR })}
                        </span>
                        {bill.customer_supplier && (
                          <span className="flex items-center gap-1 truncate max-w-[150px] sm:max-w-none">
                            <UserIcon className="h-3 w-3 flex-shrink-0" />
                            {bill.customer_supplier}
                          </span>
                        )}
                      </div>
                      {bill.category_name && (
                        <p className="text-xs text-muted-foreground mt-1 flex items-center gap-1">
                          {bill.category_icon && <span>{bill.category_icon}</span>}
                          {bill.category_name}
                        </p>
                      )}

                      {/* Warning for different amounts */}
                      {amountInfo && (
                        <div className={`mt-2 p-2 rounded text-xs flex items-start gap-2 ${
                          amountInfo.type === 'warning'
                            ? 'bg-yellow-500/20 text-yellow-300'
                            : 'bg-blue-500/20 text-blue-300'
                        }`}>
                          <ExclamationTriangleIcon className="h-4 w-4 flex-shrink-0 mt-0.5" />
                          <span className="break-words">{amountInfo.message}</span>
                        </div>
                      )}
                    </div>
                    <Button
                      size="sm"
                      onClick={() => handleLink(bill)}
                      disabled={isLinking !== null}
                      className={`w-full sm:w-auto flex-shrink-0 ${!bill.amount_match ? 'bg-yellow-600 hover:bg-yellow-700' : ''}`}
                    >
                      {isLinking === bill.id ? (
                        <LoadingSpinner className="w-4 h-4" />
                      ) : (
                        <>
                          <LinkIcon className="h-4 w-4 mr-1" />
                          <span className="sm:hidden">{bill.amount_match ? 'Vincular' : 'Vincular'}</span>
                          <span className="hidden sm:inline">{bill.amount_match ? 'Vincular' : 'Vincular Mesmo Assim'}</span>
                        </>
                      )}
                    </Button>
                  </div>
                </div>
              );
            })}
          </div>
        ) : (
          <div className="text-center py-8 sm:py-12">
            <DocumentTextIcon className="h-10 w-10 sm:h-12 sm:w-12 mx-auto text-muted-foreground mb-3 sm:mb-4" />
            <p className="text-sm sm:text-base text-muted-foreground">
              Nenhuma conta pendente encontrada.
            </p>
            <p className="text-xs sm:text-sm text-muted-foreground mt-2">
              Crie uma conta a pagar/receber primeiro em &quot;Contas&quot;.
            </p>
          </div>
        )}

        <div className="flex justify-end pt-3 sm:pt-4 border-t border-white/10">
          <Button variant="outline" onClick={() => onOpenChange(false)} className="w-full sm:w-auto">
            Cancelar
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}
