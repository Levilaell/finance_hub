'use client';

import { useEffect, useState } from 'react';
import { billsService } from '@/services/bills.service';
import { Bill, PartialPaymentSuggestion } from '@/types/banking';
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
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { LoadingSpinner } from '@/components/ui/loading-spinner';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { formatCurrency } from '@/lib/utils';
import {
  LinkIcon,
  BanknotesIcon,
  CalendarIcon,
  BuildingLibraryIcon,
  PlusIcon,
  CheckIcon,
} from '@heroicons/react/24/outline';
import { toast } from 'sonner';

interface LinkPartialPaymentDialogProps {
  bill: Bill | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onPaymentAdded: () => void;
}

export function LinkPartialPaymentDialog({
  bill,
  open,
  onOpenChange,
  onPaymentAdded,
}: LinkPartialPaymentDialogProps) {
  const [suggestions, setSuggestions] = useState<PartialPaymentSuggestion[]>([]);
  const [remainingAmount, setRemainingAmount] = useState<number>(0);
  const [isLoading, setIsLoading] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<string>('transaction');

  // Manual payment form
  const [manualAmount, setManualAmount] = useState<string>('');
  const [manualNotes, setManualNotes] = useState<string>('');

  useEffect(() => {
    if (open && bill) {
      fetchSuggestions();
      setManualAmount(bill.amount_remaining?.toString() || '0');
      setManualNotes('');
    }
  }, [open, bill]);

  const fetchSuggestions = async () => {
    if (!bill) return;

    setIsLoading(true);
    try {
      const response = await billsService.getSuggestedTransactionsPartial(bill.id);
      setSuggestions(response.transactions);
      setRemainingAmount(parseFloat(response.remaining_amount));
    } catch (error) {
      console.error('Error fetching suggestions:', error);
      toast.error('Erro ao buscar transações');
    } finally {
      setIsLoading(false);
    }
  };

  const handleLinkTransaction = async (transactionId: string, amount: number) => {
    if (!bill) return;

    setIsSubmitting(transactionId);
    try {
      await billsService.addPayment(bill.id, {
        amount,
        transaction_id: transactionId,
        notes: ''
      });
      toast.success('Pagamento vinculado com sucesso!');
      onPaymentAdded();

      // Refresh suggestions if bill not complete
      if (amount < remainingAmount) {
        fetchSuggestions();
      } else {
        onOpenChange(false);
      }
    } catch (error: any) {
      console.error('Error linking payment:', error);
      toast.error(error?.response?.data?.error || 'Erro ao vincular pagamento');
    } finally {
      setIsSubmitting(null);
    }
  };

  const handleManualPayment = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!bill) return;

    const amount = parseFloat(manualAmount);
    if (isNaN(amount) || amount <= 0) {
      toast.error('Valor inválido');
      return;
    }

    if (amount > remainingAmount) {
      toast.error(`Valor excede o restante (${formatCurrency(remainingAmount)})`);
      return;
    }

    setIsSubmitting('manual');
    try {
      await billsService.addPayment(bill.id, {
        amount,
        notes: manualNotes
      });
      toast.success('Pagamento registrado com sucesso!');
      onPaymentAdded();

      if (amount < remainingAmount) {
        setManualAmount((remainingAmount - amount).toString());
        setManualNotes('');
        fetchSuggestions();
      } else {
        onOpenChange(false);
      }
    } catch (error: any) {
      console.error('Error adding payment:', error);
      toast.error(error?.response?.data?.error || 'Erro ao registrar pagamento');
    } finally {
      setIsSubmitting(null);
    }
  };

  const getRelevanceColor = (score: number) => {
    if (score >= 80) return 'bg-green-500';
    if (score >= 60) return 'bg-yellow-500';
    if (score >= 40) return 'bg-orange-500';
    return 'bg-red-500';
  };

  if (!bill) return null;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <PlusIcon className="h-5 w-5" />
            Adicionar Pagamento
          </DialogTitle>
          <DialogDescription>
            Adicione um pagamento para: <strong>{bill.description}</strong>
          </DialogDescription>
        </DialogHeader>

        {/* Bill Summary */}
        <div className="bg-muted/50 rounded-lg p-4 mb-4">
          <div className="grid grid-cols-3 gap-4 text-sm">
            <div>
              <p className="text-muted-foreground">Valor Total</p>
              <p className="font-semibold">{formatCurrency(bill.amount)}</p>
            </div>
            <div>
              <p className="text-muted-foreground">Já Pago</p>
              <p className="font-semibold text-green-600">{formatCurrency(bill.amount_paid)}</p>
            </div>
            <div>
              <p className="text-muted-foreground">Restante</p>
              <p className="font-semibold text-orange-600">{formatCurrency(remainingAmount)}</p>
            </div>
          </div>
          <div className="mt-3">
            <div className="flex items-center justify-between text-xs text-muted-foreground mb-1">
              <span>Progresso</span>
              <span>{bill.payment_percentage?.toFixed(0) || 0}%</span>
            </div>
            <Progress value={bill.payment_percentage || 0} className="h-2" />
          </div>
        </div>

        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList className="grid w-full grid-cols-2">
            <TabsTrigger value="transaction">
              <LinkIcon className="h-4 w-4 mr-2" />
              Vincular Transação
            </TabsTrigger>
            <TabsTrigger value="manual">
              <BanknotesIcon className="h-4 w-4 mr-2" />
              Pagamento Manual
            </TabsTrigger>
          </TabsList>

          {/* Tab: Link Transaction */}
          <TabsContent value="transaction" className="mt-4">
            {isLoading ? (
              <div className="flex items-center justify-center py-8">
                <LoadingSpinner />
                <span className="ml-2">Buscando transações...</span>
              </div>
            ) : suggestions.length === 0 ? (
              <div className="text-center py-8 text-muted-foreground">
                <BanknotesIcon className="h-12 w-12 mx-auto mb-2 opacity-50" />
                <p>Nenhuma transação encontrada</p>
                <p className="text-sm">Tente registrar um pagamento manual</p>
              </div>
            ) : (
              <div className="space-y-3 max-h-[400px] overflow-y-auto">
                {suggestions.map((tx) => (
                  <div
                    key={tx.id}
                    className="flex items-center justify-between p-3 border rounded-lg hover:bg-muted/50 transition-colors"
                  >
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <p className="font-medium">{tx.description}</p>
                        {tx.would_complete_bill && (
                          <Badge className="bg-green-100 text-green-800 text-xs">
                            <CheckIcon className="h-3 w-3 mr-1" />
                            Completa
                          </Badge>
                        )}
                      </div>
                      <div className="flex items-center gap-4 text-sm text-muted-foreground mt-1">
                        <span className="flex items-center gap-1">
                          <BanknotesIcon className="h-4 w-4" />
                          {formatCurrency(tx.amount)}
                        </span>
                        <span className="flex items-center gap-1">
                          <CalendarIcon className="h-4 w-4" />
                          {format(new Date(tx.date), 'dd/MM/yyyy', { locale: ptBR })}
                        </span>
                        <span className="flex items-center gap-1">
                          <BuildingLibraryIcon className="h-4 w-4" />
                          {tx.account_name}
                        </span>
                      </div>
                      <div className="flex items-center gap-2 mt-2">
                        <div className={`w-2 h-2 rounded-full ${getRelevanceColor(tx.relevance_score)}`} />
                        <span className="text-xs text-muted-foreground">
                          Relevância: {tx.relevance_score}%
                        </span>
                      </div>
                    </div>
                    <Button
                      size="sm"
                      onClick={() => handleLinkTransaction(tx.id, tx.amount)}
                      disabled={isSubmitting !== null}
                    >
                      {isSubmitting === tx.id ? (
                        <LoadingSpinner className="h-4 w-4" />
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
            )}
          </TabsContent>

          {/* Tab: Manual Payment */}
          <TabsContent value="manual" className="mt-4">
            <form onSubmit={handleManualPayment} className="space-y-4">
              <div>
                <Label>Valor do Pagamento</Label>
                <div className="relative">
                  <span className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground">
                    R$
                  </span>
                  <Input
                    type="number"
                    step="0.01"
                    min="0.01"
                    max={remainingAmount}
                    value={manualAmount}
                    onChange={(e) => setManualAmount(e.target.value)}
                    className="pl-10"
                    placeholder="0,00"
                  />
                </div>
                <p className="text-xs text-muted-foreground mt-1">
                  Máximo: {formatCurrency(remainingAmount)}
                </p>
              </div>

              <div>
                <Label>Observações (opcional)</Label>
                <Textarea
                  value={manualNotes}
                  onChange={(e) => setManualNotes(e.target.value)}
                  placeholder="Detalhes do pagamento..."
                  rows={3}
                />
              </div>

              <div className="flex justify-end gap-2">
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => onOpenChange(false)}
                >
                  Cancelar
                </Button>
                <Button type="submit" disabled={isSubmitting !== null}>
                  {isSubmitting === 'manual' ? (
                    <LoadingSpinner className="h-4 w-4 mr-2" />
                  ) : (
                    <PlusIcon className="h-4 w-4 mr-2" />
                  )}
                  Registrar Pagamento
                </Button>
              </div>
            </form>
          </TabsContent>
        </Tabs>
      </DialogContent>
    </Dialog>
  );
}
