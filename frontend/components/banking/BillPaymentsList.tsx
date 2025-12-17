'use client';

import { useState } from 'react';
import { billsService } from '@/services/bills.service';
import { Bill, BillPayment } from '@/types/banking';
import { format } from 'date-fns';
import { ptBR } from 'date-fns/locale';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { LoadingSpinner } from '@/components/ui/loading-spinner';
import { formatCurrency } from '@/lib/utils';
import {
  BanknotesIcon,
  CalendarIcon,
  BuildingLibraryIcon,
  TrashIcon,
  LinkIcon,
  DocumentTextIcon,
} from '@heroicons/react/24/outline';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog';
import { toast } from 'sonner';

interface BillPaymentsListProps {
  bill: Bill;
  onPaymentRemoved: () => void;
}

export function BillPaymentsList({ bill, onPaymentRemoved }: BillPaymentsListProps) {
  const [isDeleting, setIsDeleting] = useState<string | null>(null);
  const [paymentToDelete, setPaymentToDelete] = useState<BillPayment | null>(null);

  const handleDeletePayment = async () => {
    if (!paymentToDelete) return;

    setIsDeleting(paymentToDelete.id);
    try {
      await billsService.removePayment(bill.id, paymentToDelete.id);
      toast.success('Pagamento removido com sucesso!');
      onPaymentRemoved();
    } catch (error: any) {
      console.error('Error removing payment:', error);
      toast.error(error?.response?.data?.error || 'Erro ao remover pagamento');
    } finally {
      setIsDeleting(null);
      setPaymentToDelete(null);
    }
  };

  if (!bill.payments || bill.payments.length === 0) {
    return (
      <div className="text-center py-6 text-muted-foreground">
        <BanknotesIcon className="h-10 w-10 mx-auto mb-2 opacity-50" />
        <p className="text-sm">Nenhum pagamento registrado</p>
      </div>
    );
  }

  return (
    <>
      <div className="space-y-3">
        {bill.payments.map((payment) => (
          <div
            key={payment.id}
            className="flex items-center justify-between p-3 border rounded-lg bg-muted/30"
          >
            <div className="flex-1">
              <div className="flex items-center gap-2">
                <span className="font-semibold text-green-600">
                  {formatCurrency(payment.amount)}
                </span>
                {payment.has_transaction ? (
                  <Badge variant="outline" className="text-xs">
                    <LinkIcon className="h-3 w-3 mr-1" />
                    Vinculado
                  </Badge>
                ) : (
                  <Badge variant="secondary" className="text-xs">
                    <BanknotesIcon className="h-3 w-3 mr-1" />
                    Manual
                  </Badge>
                )}
              </div>

              <div className="flex items-center gap-4 text-xs text-muted-foreground mt-1">
                <span className="flex items-center gap-1">
                  <CalendarIcon className="h-3 w-3" />
                  {format(new Date(payment.payment_date), 'dd/MM/yyyy', { locale: ptBR })}
                </span>
                {payment.transaction_details && (
                  <span className="flex items-center gap-1">
                    <BuildingLibraryIcon className="h-3 w-3" />
                    {payment.transaction_details.account_name}
                  </span>
                )}
              </div>

              {payment.transaction_details && (
                <p className="text-xs text-muted-foreground mt-1 truncate">
                  {payment.transaction_details.description}
                </p>
              )}

              {payment.notes && (
                <div className="flex items-start gap-1 mt-1">
                  <DocumentTextIcon className="h-3 w-3 text-muted-foreground mt-0.5" />
                  <p className="text-xs text-muted-foreground">{payment.notes}</p>
                </div>
              )}
            </div>

            <Button
              variant="ghost"
              size="icon"
              className="h-8 w-8 text-destructive hover:text-destructive hover:bg-destructive/10"
              onClick={() => setPaymentToDelete(payment)}
              disabled={isDeleting !== null}
            >
              {isDeleting === payment.id ? (
                <LoadingSpinner className="h-4 w-4" />
              ) : (
                <TrashIcon className="h-4 w-4" />
              )}
            </Button>
          </div>
        ))}
      </div>

      {/* Delete Confirmation Dialog */}
      <AlertDialog open={!!paymentToDelete} onOpenChange={(open) => !open && setPaymentToDelete(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Remover pagamento?</AlertDialogTitle>
            <AlertDialogDescription>
              {paymentToDelete && (
                <>
                  Você está prestes a remover o pagamento de{' '}
                  <strong>{formatCurrency(paymentToDelete.amount)}</strong>
                  {paymentToDelete.has_transaction && (
                    <>
                      {' '}vinculado à transação{' '}
                      <strong>{paymentToDelete.transaction_details?.description}</strong>
                    </>
                  )}
                  .{' '}
                  <span className="text-amber-400 font-medium">
                    Esta ação não pode ser desfeita.
                  </span>
                </>
              )}
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel disabled={isDeleting !== null}>Cancelar</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleDeletePayment}
              disabled={isDeleting !== null}
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
            >
              {isDeleting ? (
                <>
                  <LoadingSpinner className="h-4 w-4 mr-2" />
                  Removendo...
                </>
              ) : (
                'Remover'
              )}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  );
}
