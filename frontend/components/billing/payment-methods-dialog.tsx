'use client';

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import { billingService, PaymentMethod } from '@/services/billing.service';
import { paymentService } from '@/services/payment.service';
import { subscriptionService } from '@/services/subscription.service';
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
import { 
  CreditCardIcon, 
  PlusIcon,
  TrashIcon,
  CheckIcon,
  StarIcon
} from '@heroicons/react/24/outline';
import { UpgradePlanDialog } from './upgrade-plan-dialog';


interface PaymentMethodsDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function PaymentMethodsDialog({
  open,
  onOpenChange
}: PaymentMethodsDialogProps) {
  const [showAddForm, setShowAddForm] = useState(false);
  const [showUpgradeDialog, setShowUpgradeDialog] = useState(false);
  const [newCardData, setNewCardData] = useState({
    number: '',
    exp_month: '',
    exp_year: '',
    cvc: '',
    name: ''
  });

  const queryClient = useQueryClient();

  // Fetch real payment methods
  const { data: paymentMethods, isLoading } = useQuery({
    queryKey: ['payment-methods'],
    queryFn: async () => {
      const response = await billingService.getPaymentMethods();
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

  const addPaymentMethodMutation = useMutation({
    mutationFn: billingService.addPaymentMethod,
    onSuccess: () => {
      toast.success('Método de pagamento adicionado com sucesso!');
      setShowAddForm(false);
      setNewCardData({ number: '', exp_month: '', exp_year: '', cvc: '', name: '' });
      queryClient.invalidateQueries({ queryKey: ['payment-methods'] });
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.error || 'Erro ao adicionar método de pagamento');
    },
  });

  const deletePaymentMethodMutation = useMutation({
    mutationFn: billingService.deletePaymentMethod,
    onSuccess: () => {
      toast.success('Método de pagamento removido');
      queryClient.invalidateQueries({ queryKey: ['payment-methods'] });
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.error || 'Erro ao remover método de pagamento');
    },
  });

  const setDefaultPaymentMethodMutation = useMutation({
    mutationFn: billingService.setDefaultPaymentMethod,
    onSuccess: () => {
      toast.success('Método de pagamento padrão atualizado');
      queryClient.invalidateQueries({ queryKey: ['payment-methods'] });
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.error || 'Erro ao definir método padrão');
    },
  });

  const getCardBrandIcon = (brand?: string) => {
    switch (brand) {
      case 'visa':
        return '💳';
      case 'mastercard':
        return '💳';
      case 'amex':
        return '💳';
      default:
        return '💳';
    }
  };

  const getPaymentMethodIcon = (method: PaymentMethod) => {
    if (method.payment_type === 'pix') {
      return '🔑';
    }
    return getCardBrandIcon(method.card_brand);
  };

  const getPaymentMethodTitle = (method: PaymentMethod) => {
    if (method.payment_type === 'pix') {
      return 'PIX';
    }
    return `${method.card_brand?.toUpperCase()} •••• ${method.last_four}`;
  };

  const getPaymentMethodSubtitle = (method: PaymentMethod) => {
    if (method.payment_type === 'pix') {
      return 'Pagamento instantâneo';
    }
    return `Expira em ${method.exp_month?.toString().padStart(2, '0')}/${method.exp_year}`;
  };

  const handleAddPaymentMethod = () => {
    if (!newCardData.number || !newCardData.exp_month || !newCardData.exp_year || !newCardData.cvc) {
      toast.error('Preencha todos os campos obrigatórios');
      return;
    }

    addPaymentMethodMutation.mutate({
      payment_type: 'credit_card',
      card_number: newCardData.number.replace(/\s/g, ''),
      exp_month: parseInt(newCardData.exp_month),
      exp_year: parseInt(newCardData.exp_year),
      cvc: newCardData.cvc,
      cardholder_name: newCardData.name,
    });
  };

  const formatCardNumber = (value: string) => {
    const v = value.replace(/\s+/g, '').replace(/[^0-9]/gi, '');
    const matches = v.match(/\d{4,16}/g);
    const match = matches && matches[0] || '';
    const parts = [];
    for (let i = 0, len = match.length; i < len; i += 4) {
      parts.push(match.substring(i, i + 4));
    }
    if (parts.length) {
      return parts.join(' ');
    } else {
      return v;
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center">
            <CreditCardIcon className="h-5 w-5 mr-2" />
            Gerenciar Métodos de Pagamento
          </DialogTitle>
          <DialogDescription>
            Adicione, remova ou altere seus métodos de pagamento.
          </DialogDescription>
        </DialogHeader>

        {isLoading ? (
          <div className="flex justify-center py-8">
            <LoadingSpinner />
          </div>
        ) : (
          <div className="space-y-4">
            {/* Add Payment Method Button */}
            {!showAddForm && (
              <Button
                onClick={() => setShowAddForm(true)}
                className="w-full flex items-center justify-center"
                variant="outline"
              >
                <PlusIcon className="h-4 w-4 mr-2" />
                Adicionar Método de Pagamento
              </Button>
            )}

            {/* Add Payment Method Form */}
            {showAddForm && (
              <Card className="border-2 border-blue-200">
                <CardContent className="p-4">
                  <h3 className="font-medium mb-4">Adicionar Cartão de Crédito</h3>
                  <div className="space-y-4">
                    <div>
                      <Label htmlFor="card-number">Número do Cartão</Label>
                      <Input
                        id="card-number"
                        placeholder="1234 5678 9012 3456"
                        value={newCardData.number}
                        onChange={(e) => setNewCardData({
                          ...newCardData,
                          number: formatCardNumber(e.target.value)
                        })}
                        maxLength={19}
                      />
                    </div>

                    <div className="grid grid-cols-3 gap-3">
                      <div>
                        <Label htmlFor="exp-month">Mês</Label>
                        <Input
                          id="exp-month"
                          placeholder="MM"
                          value={newCardData.exp_month}
                          onChange={(e) => setNewCardData({
                            ...newCardData,
                            exp_month: e.target.value.replace(/\D/g, '').slice(0, 2)
                          })}
                          maxLength={2}
                        />
                      </div>
                      <div>
                        <Label htmlFor="exp-year">Ano</Label>
                        <Input
                          id="exp-year"
                          placeholder="AAAA"
                          value={newCardData.exp_year}
                          onChange={(e) => setNewCardData({
                            ...newCardData,
                            exp_year: e.target.value.replace(/\D/g, '').slice(0, 4)
                          })}
                          maxLength={4}
                        />
                      </div>
                      <div>
                        <Label htmlFor="cvc">CVC</Label>
                        <Input
                          id="cvc"
                          placeholder="123"
                          value={newCardData.cvc}
                          onChange={(e) => setNewCardData({
                            ...newCardData,
                            cvc: e.target.value.replace(/\D/g, '').slice(0, 4)
                          })}
                          maxLength={4}
                        />
                      </div>
                    </div>

                    <div>
                      <Label htmlFor="card-name">Nome no Cartão</Label>
                      <Input
                        id="card-name"
                        placeholder="João Silva"
                        value={newCardData.name}
                        onChange={(e) => setNewCardData({
                          ...newCardData,
                          name: e.target.value
                        })}
                      />
                    </div>

                    <div className="flex space-x-3">
                      <Button
                        onClick={handleAddPaymentMethod}
                        disabled={addPaymentMethodMutation.isPending}
                        className="flex-1"
                      >
                        {addPaymentMethodMutation.isPending ? (
                          <LoadingSpinner />
                        ) : (
                          'Adicionar Cartão'
                        )}
                      </Button>
                      <Button
                        variant="outline"
                        onClick={() => setShowAddForm(false)}
                        disabled={addPaymentMethodMutation.isPending}
                      >
                        Cancelar
                      </Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Payment Methods List */}
            <div className="space-y-3">
              {paymentMethods?.map((method: any) => (
                <Card key={method.id} className="hover:shadow-md transition-shadow">
                  <CardContent className="p-4">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-3">
                        <div className="text-2xl">
                          {getPaymentMethodIcon(method)}
                        </div>
                        
                        <div className="flex-1">
                          <div className="flex items-center space-x-2">
                            <h4 className="font-medium">
                              {getPaymentMethodTitle(method)}
                            </h4>
                            {method.is_default && (
                              <Badge className="bg-blue-100 text-blue-800">
                                <StarIcon className="h-3 w-3 mr-1" />
                                Padrão
                              </Badge>
                            )}
                          </div>
                          <p className="text-sm text-gray-600">
                            {getPaymentMethodSubtitle(method)}
                          </p>
                        </div>
                      </div>

                      <div className="flex items-center space-x-2">
                        {!method.is_default && (
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => setDefaultPaymentMethodMutation.mutate(method.id)}
                            disabled={setDefaultPaymentMethodMutation.isPending}
                          >
                            <CheckIcon className="h-4 w-4 mr-1" />
                            Tornar Padrão
                          </Button>
                        )}
                        
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => deletePaymentMethodMutation.mutate(method.id)}
                          disabled={deletePaymentMethodMutation.isPending || method.is_default}
                          className="text-red-600 hover:text-red-700"
                        >
                          <TrashIcon className="h-4 w-4" />
                        </Button>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>

            {paymentMethods?.length === 0 && (
              <div className="text-center py-8 text-gray-500">
                <CreditCardIcon className="h-12 w-12 mx-auto mb-4 opacity-30" />
                <p>Nenhum método de pagamento cadastrado</p>
                <p className="text-sm">Adicione um cartão ou configure o PIX</p>
              </div>
            )}

            {/* Security Note */}
            <div className="bg-blue-50 border border-blue-200 p-3 rounded-lg">
              <p className="text-sm text-blue-800">
                🔒 <strong>Segurança:</strong> Todos os dados de pagamento são criptografados e processados de forma segura. 
                Não armazenamos informações completas do cartão.
              </p>
            </div>

            {/* Quick Action - Add card and choose plan */}
            {paymentMethods?.length === 0 && (
              <div className="mt-4 p-4 bg-gradient-to-r from-blue-50 to-purple-50 rounded-lg border border-blue-200">
                <p className="text-sm font-medium text-blue-900 mb-2">
                  Configure seu método de pagamento e escolha um plano
                </p>
                <Button 
                  onClick={() => setShowUpgradeDialog(true)}
                  className="w-full"
                  variant="default"
                >
                  Adicionar Cartão e Escolher Plano
                </Button>
              </div>
            )}
          </div>
        )}
      </DialogContent>
      
      {/* Upgrade Plan Dialog */}
      <UpgradePlanDialog
        open={showUpgradeDialog}
        onOpenChange={setShowUpgradeDialog}
      />
    </Dialog>
  );
}