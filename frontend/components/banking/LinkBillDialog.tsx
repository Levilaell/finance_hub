'use client';

import { useEffect, useState } from 'react';
import { bankingService } from '@/services/banking.service';
import { Transaction, BillSuggestion } from '@/types/banking';
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
  const [suggestions, setSuggestions] = useState<BillSuggestion[]>([]);
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
      const data = await bankingService.getSuggestedBills(transaction.id);
      setSuggestions(data);
    } catch (error) {
      console.error('Error fetching suggestions:', error);
      toast.error('Erro ao buscar contas sugeridas');
    } finally {
      setIsLoading(false);
    }
  };

  const handleLink = async (billId: string) => {
    if (!transaction) return;

    setIsLinking(billId);
    try {
      await bankingService.linkBill(transaction.id, billId);
      toast.success('Conta vinculada com sucesso! Marcada como paga.');
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
    if (score >= 60) return 'Média';
    if (score >= 40) return 'Baixa';
    return 'Muito Baixa';
  };

  const getTypeLabel = (type: string) => {
    return type === 'receivable' ? 'A Receber' : 'A Pagar';
  };

  const getTypeColor = (type: string) => {
    return type === 'receivable' ? 'text-green-500' : 'text-red-500';
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <LinkIcon className="h-5 w-5" />
            Vincular a Conta
          </DialogTitle>
          <DialogDescription>
            Selecione uma conta a pagar/receber para vincular a esta transação.
            A conta será automaticamente marcada como paga.
          </DialogDescription>
        </DialogHeader>

        {transaction && (
          <div className="bg-muted/50 rounded-lg p-4 mb-4">
            <h3 className="font-semibold text-lg">{transaction.description}</h3>
            <div className="flex items-center gap-4 mt-2 text-sm text-muted-foreground">
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
              <span>{transaction.account_name}</span>
            </div>
            {transaction.merchant_name && (
              <p className="text-xs text-muted-foreground mt-1">
                {transaction.merchant_name}
              </p>
            )}
          </div>
        )}

        {isLoading ? (
          <div className="flex items-center justify-center py-12">
            <LoadingSpinner />
          </div>
        ) : suggestions.length > 0 ? (
          <div className="space-y-3">
            <p className="text-sm text-muted-foreground">
              {suggestions.length} conta(s) encontrada(s)
            </p>
            {suggestions.map((bill) => (
              <div
                key={bill.id}
                className="flex items-center justify-between p-4 border border-white/10 rounded-lg hover:bg-white/5 transition-colors"
              >
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <h4 className="font-medium">{bill.description}</h4>
                    <Badge
                      variant="outline"
                      className={getTypeColor(bill.type)}
                    >
                      {getTypeLabel(bill.type)}
                    </Badge>
                    <Badge
                      className={`${getRelevanceColor(bill.relevance_score)} text-white text-xs`}
                    >
                      {getRelevanceLabel(bill.relevance_score)} ({bill.relevance_score}%)
                    </Badge>
                  </div>
                  <div className="flex items-center gap-4 mt-1 text-sm text-muted-foreground">
                    <span className="flex items-center gap-1">
                      <BanknotesIcon className="h-3 w-3" />
                      {formatCurrency(bill.amount)}
                    </span>
                    <span className="flex items-center gap-1">
                      <CalendarIcon className="h-3 w-3" />
                      Venc: {format(new Date(bill.due_date), 'dd/MM/yyyy', { locale: ptBR })}
                    </span>
                    {bill.customer_supplier && (
                      <span className="flex items-center gap-1">
                        <UserIcon className="h-3 w-3" />
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
                </div>
                <Button
                  size="sm"
                  onClick={() => handleLink(bill.id)}
                  disabled={isLinking !== null}
                >
                  {isLinking === bill.id ? (
                    <LoadingSpinner className="w-4 h-4" />
                  ) : (
                    <>
                      <LinkIcon className="h-4 w-4 mr-1" />
                      Vincular
                    </>
                  )}
                </Button>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-12">
            <DocumentTextIcon className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
            <p className="text-muted-foreground">
              Nenhuma conta compatível encontrada.
            </p>
            <p className="text-sm text-muted-foreground mt-2">
              As contas devem ter o mesmo valor e estar pendentes para serem vinculadas.
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
