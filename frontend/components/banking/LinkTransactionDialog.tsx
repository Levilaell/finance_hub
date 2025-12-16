'use client';

import { useEffect, useState } from 'react';
import { billsService } from '@/services/bills.service';
import { Bill, TransactionSuggestion } from '@/types/banking';
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
  BuildingLibraryIcon,
} from '@heroicons/react/24/outline';
import { toast } from 'sonner';

interface LinkTransactionDialogProps {
  bill: Bill | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onLinked: () => void;
}

export function LinkTransactionDialog({
  bill,
  open,
  onOpenChange,
  onLinked,
}: LinkTransactionDialogProps) {
  const [suggestions, setSuggestions] = useState<TransactionSuggestion[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isLinking, setIsLinking] = useState<string | null>(null);

  useEffect(() => {
    if (open && bill) {
      fetchSuggestions();
    }
  }, [open, bill]);

  const fetchSuggestions = async () => {
    if (!bill) return;

    setIsLoading(true);
    try {
      const data = await billsService.getSuggestedTransactions(bill.id);
      setSuggestions(data);
    } catch (error) {
      console.error('Error fetching suggestions:', error);
      toast.error('Erro ao buscar transações sugeridas');
    } finally {
      setIsLoading(false);
    }
  };

  const handleLink = async (transactionId: string) => {
    if (!bill) return;

    setIsLinking(transactionId);
    try {
      await billsService.linkTransaction(bill.id, transactionId);
      toast.success('Transação vinculada com sucesso! Conta marcada como paga.');
      onLinked();
      onOpenChange(false);
    } catch (error: any) {
      console.error('Error linking transaction:', error);
      toast.error(error?.response?.data?.error || 'Erro ao vincular transação');
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
    if (score >= 60) return 'Média';
    if (score >= 40) return 'Baixa';
    return 'Muito Baixa';
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <LinkIcon className="h-5 w-5" />
            Vincular Transação
          </DialogTitle>
          <DialogDescription className="text-xs sm:text-sm">
            Selecione uma transação do extrato para vincular a esta conta.
            A conta será automaticamente marcada como paga.
          </DialogDescription>
        </DialogHeader>

        {bill && (
          <div className="bg-muted/50 rounded-lg p-3 sm:p-4 mb-4">
            <h3 className="font-semibold text-base sm:text-lg break-words">{bill.description}</h3>
            <div className="flex flex-wrap items-center gap-x-3 gap-y-1 mt-2 text-xs sm:text-sm text-muted-foreground">
              <span className="flex items-center gap-1">
                <BanknotesIcon className="h-4 w-4" />
                {formatCurrency(bill.amount)}
              </span>
              <span className="flex items-center gap-1">
                <CalendarIcon className="h-4 w-4" />
                Venc: {format(new Date(bill.due_date), 'dd/MM/yyyy', { locale: ptBR })}
              </span>
              {bill.customer_supplier && (
                <span className="truncate max-w-[150px] sm:max-w-none">• {bill.customer_supplier}</span>
              )}
            </div>
          </div>
        )}

        {isLoading ? (
          <div className="flex items-center justify-center py-12">
            <LoadingSpinner />
          </div>
        ) : suggestions.length > 0 ? (
          <div className="space-y-3">
            <p className="text-xs sm:text-sm text-muted-foreground">
              {suggestions.length} transação(ões) encontrada(s)
            </p>
            {suggestions.map((transaction) => (
              <div
                key={transaction.id}
                className="flex flex-col sm:flex-row sm:items-center sm:justify-between p-3 sm:p-4 border border-white/10 rounded-lg hover:bg-white/5 transition-colors gap-3"
              >
                <div className="flex-1 min-w-0">
                  <div className="flex flex-wrap items-start sm:items-center gap-2">
                    <h4 className="font-medium text-sm sm:text-base break-words">{transaction.description}</h4>
                    <Badge
                      className={`${getRelevanceColor(transaction.relevance_score)} text-white text-xs`}
                    >
                      {getRelevanceLabel(transaction.relevance_score)} ({transaction.relevance_score}%)
                    </Badge>
                  </div>
                  <div className="flex flex-wrap items-center gap-x-3 gap-y-1 mt-1 text-xs sm:text-sm text-muted-foreground">
                    <span className="flex items-center gap-1">
                      <BanknotesIcon className="h-3 w-3" />
                      {formatCurrency(transaction.amount)}
                    </span>
                    <span className="flex items-center gap-1">
                      <CalendarIcon className="h-3 w-3" />
                      {format(new Date(transaction.date), 'dd/MM/yyyy', { locale: ptBR })}
                    </span>
                    <span className="flex items-center gap-1 truncate max-w-[120px] sm:max-w-none">
                      <BuildingLibraryIcon className="h-3 w-3 flex-shrink-0" />
                      {transaction.account_name}
                    </span>
                  </div>
                  {transaction.merchant_name && (
                    <p className="text-xs text-muted-foreground mt-1 truncate">
                      {transaction.merchant_name}
                    </p>
                  )}
                </div>
                <Button
                  size="sm"
                  className="w-full sm:w-auto h-8 sm:h-9"
                  onClick={() => handleLink(transaction.id)}
                  disabled={isLinking !== null}
                >
                  {isLinking === transaction.id ? (
                    <LoadingSpinner className="w-4 h-4" />
                  ) : (
                    <>
                      <LinkIcon className="h-4 w-4 sm:mr-1" />
                      <span className="sm:inline">Vincular</span>
                    </>
                  )}
                </Button>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-12">
            <BanknotesIcon className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
            <p className="text-muted-foreground">
              Nenhuma transação compatível encontrada.
            </p>
            <p className="text-sm text-muted-foreground mt-2">
              As transações devem ter o mesmo valor que a conta para serem vinculadas.
            </p>
          </div>
        )}

        <div className="flex justify-end pt-4 border-t border-white/10">
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Cancelar
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}
