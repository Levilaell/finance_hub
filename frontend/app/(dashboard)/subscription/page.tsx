'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { useSubscription } from '@/hooks/useSubscription';
import { useUsageLimits } from '@/hooks/useUsageLimits';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { subscriptionService, CreatePaymentMethodRequest } from '@/services/unified-subscription.service';
import { SubscriptionCard } from '@/components/payment/SubscriptionCard';
import { UsageIndicator } from '@/components/payment/UsageIndicator';
import PaymentErrorBoundary, { usePaymentErrorHandler } from '@/components/error-boundaries/PaymentErrorBoundary';
import { CreditCard, Receipt, AlertCircle, Plus, Trash2, Check } from 'lucide-react';
import { format } from 'date-fns';
import { toast } from 'sonner';

export default function SubscriptionPage() {
  const router = useRouter();
  const queryClient = useQueryClient();
  const { subscription, cancelSubscription, isActive, isTrial } = useSubscription();
  const { usageLimits } = useUsageLimits();
  const { handleError } = usePaymentErrorHandler();
  const [showCancelDialog, setShowCancelDialog] = useState(false);
  const [showAddPaymentMethod, setShowAddPaymentMethod] = useState(false);

  // Payment methods - Now enabled with proper error handling
  const { data: paymentMethods, refetch: refetchPaymentMethods, isLoading: loadingPaymentMethods, error: paymentMethodsError } = useQuery({
    queryKey: ['payment-methods'],
    queryFn: subscriptionService.getPaymentMethods,
    retry: 2,
    staleTime: 1000 * 60 * 5, // 5 minutes
  });

  // Payment history - Now enabled with proper error handling
  const { data: payments, isLoading: loadingPayments, error: paymentsError } = useQuery({
    queryKey: ['payment-history'],
    queryFn: subscriptionService.getPaymentHistory,
    retry: 2,
    staleTime: 1000 * 60 * 5, // 5 minutes
  });

  // Payment method mutations - Now functional
  const addPaymentMethod = useMutation({
    mutationFn: (data: CreatePaymentMethodRequest) => subscriptionService.createPaymentMethod(data),
    onSuccess: () => {
      toast.success('Payment method has been successfully added.');
      refetchPaymentMethods();
      setShowAddPaymentMethod(false);
    },
    onError: (error: Error) => {
      const message = handleError(error, 'add payment method');
      toast.error(message || 'Failed to add payment method');
    },
  });

  const updatePaymentMethod = useMutation({
    mutationFn: ({ id, data }: { id: number; data: any }) => subscriptionService.updatePaymentMethod(id, data),
    onSuccess: () => {
      toast.success('Payment method has been successfully updated.');
      refetchPaymentMethods();
    },
    onError: (error: Error) => {
      const message = handleError(error, 'update payment method');
      toast.error(message || 'Failed to update payment method');
    },
  });

  const deletePaymentMethod = useMutation({
    mutationFn: (id: number) => subscriptionService.deletePaymentMethod(id),
    onSuccess: () => {
      toast.success('Payment method has been successfully removed.');
      refetchPaymentMethods();
    },
    onError: (error: Error) => {
      const message = handleError(error, 'delete payment method');
      toast.error(message || 'Failed to remove payment method');
    },
  });

  const handleCancelSubscription = () => {
    cancelSubscription.mutate();
    setShowCancelDialog(false);
  };

  return (
    <PaymentErrorBoundary>
      <div className="container mx-auto py-8 space-y-8">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Subscription & Billing</h1>
        <p className="text-muted-foreground">
          Manage your subscription plan, payment methods, and billing history
        </p>
      </div>

      <div className="grid gap-8 md:grid-cols-3">
        <div className="md:col-span-2 space-y-8">
          <Tabs defaultValue="overview" className="space-y-4">
            <TabsList>
              <TabsTrigger value="overview">Overview</TabsTrigger>
              <TabsTrigger value="payment-methods">Payment Methods</TabsTrigger>
              <TabsTrigger value="billing-history">Billing History</TabsTrigger>
            </TabsList>

            <TabsContent value="overview" className="space-y-4">
              <SubscriptionCard />

              {usageLimits && (
                <Card>
                  <CardHeader>
                    <CardTitle>Usage Details</CardTitle>
                    <CardDescription>
                      Track your usage for the current billing period
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <UsageIndicator
                      type="transaction"
                      current={usageLimits.transactions.used}
                      limit={usageLimits.transactions.limit}
                      percentage={usageLimits.transactions.percentage}
                    />
                    <UsageIndicator
                      type="bank_account"
                      current={usageLimits.bank_accounts.used}
                      limit={usageLimits.bank_accounts.limit}
                      percentage={usageLimits.bank_accounts.percentage}
                    />
                    {/* Requisições IA será implementado em breve */}
                    {/* <UsageIndicator
                      type="ai_request"
                      current={usageLimits.ai_requests.used}
                      limit={usageLimits.ai_requests.limit}
                      percentage={usageLimits.ai_requests.percentage}
                    /> */}
                  </CardContent>
                </Card>
              )}
            </TabsContent>

            <TabsContent value="payment-methods" className="space-y-4">
              <Card>
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <div>
                      <CardTitle>Payment Methods</CardTitle>
                      <CardDescription>
                        Manage your payment methods for automatic billing
                      </CardDescription>
                    </div>
                    <Button onClick={() => setShowAddPaymentMethod(true)}>
                      <Plus className="mr-2 h-4 w-4" />
                      Add Payment Method
                    </Button>
                  </div>
                </CardHeader>
                <CardContent>
                  {loadingPaymentMethods ? (
                    <div className="text-center py-8">
                      <div className="animate-pulse space-y-4">
                        <div className="h-16 bg-gray-200 rounded"></div>
                        <div className="h-16 bg-gray-200 rounded"></div>
                      </div>
                    </div>
                  ) : paymentMethodsError ? (
                    <div className="text-center py-8">
                      <AlertCircle className="h-12 w-12 text-red-500 mx-auto mb-4" />
                      <p className="text-red-600 mb-4">Failed to load payment methods</p>
                      <Button variant="outline" onClick={() => refetchPaymentMethods()}>
                        Try Again
                      </Button>
                    </div>
                  ) : paymentMethods && paymentMethods.length > 0 ? (
                    <div className="space-y-3">
                      {paymentMethods.map((method) => (
                        <div
                          key={method.id}
                          className="flex items-center justify-between p-4 border rounded-lg"
                        >
                          <div className="flex items-center space-x-4">
                            <CreditCard className="h-6 w-6 text-muted-foreground" />
                            <div>
                              <p className="font-medium">{method.display_name}</p>
                              {method.exp_month && method.exp_year && (
                                <p className="text-sm text-muted-foreground">
                                  Expires {method.exp_month}/{method.exp_year}
                                </p>
                              )}
                            </div>
                            {method.is_default && (
                              <Badge variant="secondary">Default</Badge>
                            )}
                          </div>
                          <div className="flex items-center space-x-2">
                            {!method.is_default && (
                              <Button
                                variant="ghost"
                                size="sm"
                                disabled={updatePaymentMethod.isPending}
                                onClick={() => updatePaymentMethod.mutate({
                                  id: method.id,
                                  data: { is_default: true }
                                })}
                              >
                                {updatePaymentMethod.isPending ? 'Setting...' : 'Set as Default'}
                              </Button>
                            )}
                            <Button
                              variant="ghost"
                              size="icon"
                              disabled={deletePaymentMethod.isPending}
                              onClick={() => deletePaymentMethod.mutate(method.id)}
                            >
                              <Trash2 className="h-4 w-4" />
                            </Button>
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="text-center py-8">
                      <CreditCard className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
                      <p className="text-muted-foreground">No payment methods added yet</p>
                      <Button
                        variant="outline"
                        className="mt-4"
                        onClick={() => setShowAddPaymentMethod(true)}
                      >
                        Add Your First Payment Method
                      </Button>
                    </div>
                  )}
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="billing-history">
              <Card>
                <CardHeader>
                  <CardTitle>Billing History</CardTitle>
                  <CardDescription>
                    View your past payments and download invoices
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  {loadingPayments ? (
                    <div className="text-center py-8">
                      <div className="animate-pulse space-y-4">
                        <div className="h-16 bg-gray-200 rounded"></div>
                        <div className="h-16 bg-gray-200 rounded"></div>
                        <div className="h-16 bg-gray-200 rounded"></div>
                      </div>
                    </div>
                  ) : paymentsError ? (
                    <div className="text-center py-8">
                      <AlertCircle className="h-12 w-12 text-red-500 mx-auto mb-4" />
                      <p className="text-red-600 mb-4">Failed to load payment history</p>
                      <Button variant="outline" onClick={() => window.location.reload()}>
                        Try Again
                      </Button>
                    </div>
                  ) : payments && payments.length > 0 ? (
                    <div className="space-y-3">
                      {payments.map((payment) => (
                        <div
                          key={payment.id}
                          className="flex items-center justify-between p-4 border rounded-lg"
                        >
                          <div className="flex items-center space-x-4">
                            <Receipt className="h-5 w-5 text-muted-foreground" />
                            <div>
                              <p className="font-medium">{payment.description}</p>
                              <p className="text-sm text-muted-foreground">
                                {format(new Date(payment.created_at), 'MMM d, yyyy')}
                              </p>
                            </div>
                          </div>
                          <div className="flex items-center space-x-4">
                            <span className="font-medium">
                              {payment.currency} {payment.amount}
                            </span>
                            <Check className="h-5 w-5 text-green-500" />
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="text-center py-8">
                      <Receipt className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
                      <p className="text-muted-foreground">No payments yet</p>
                    </div>
                  )}
                </CardContent>
              </Card>
            </TabsContent>
          </Tabs>
        </div>

        <div className="space-y-4">
          {subscription?.subscription_status === 'active' && (
            <Card>
              <CardHeader>
                <CardTitle>Manage Plan</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <Button 
                  className="w-full" 
                  onClick={() => router.push('/subscription/upgrade')}
                >
                  Change Plan
                </Button>
                <Button
                  variant="outline"
                  className="w-full"
                  onClick={() => setShowCancelDialog(true)}
                >
                  Cancel Subscription
                </Button>
              </CardContent>
            </Card>
          )}

          <Alert>
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>
              Need help with billing? Contact our support team at support@financehub.com
            </AlertDescription>
          </Alert>
        </div>
      </div>

      {/* Cancel Subscription Dialog */}
      <Dialog open={showCancelDialog} onOpenChange={setShowCancelDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Cancel Subscription</DialogTitle>
            <DialogDescription>
              Are you sure you want to cancel your subscription? You&apos;ll continue to have access
              until the end of your current billing period.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowCancelDialog(false)}>
              Keep Subscription
            </Button>
            <Button variant="destructive" onClick={handleCancelSubscription}>
              Yes, Cancel Subscription
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Add Payment Method Dialog */}
      <Dialog open={showAddPaymentMethod} onOpenChange={setShowAddPaymentMethod}>
        <DialogContent className="sm:max-w-[500px]">
          <DialogHeader>
            <DialogTitle>Add Payment Method</DialogTitle>
            <DialogDescription>
              Add a new payment method for automatic billing
            </DialogDescription>
          </DialogHeader>

        </DialogContent>
      </Dialog>
      </div>
    </PaymentErrorBoundary>
  );
}