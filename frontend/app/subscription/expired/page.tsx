'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { AlertCircle, CreditCard, RefreshCw } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { LoadingSpinner } from '@/components/ui/loading-spinner';
import apiClient from '@/lib/api-client';

export default function SubscriptionExpiredPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(true);
  const [subscriptionStatus, setSubscriptionStatus] = useState<any>(null);
  const [redirecting, setRedirecting] = useState(false);

  useEffect(() => {
    fetchSubscriptionStatus();
  }, []);

  const fetchSubscriptionStatus = async () => {
    try {
      const response = await apiClient.get('/api/subscriptions/status/');
      setSubscriptionStatus(response);
    } catch (error) {
      console.error('Error fetching subscription:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleUpdatePayment = async () => {
    setRedirecting(true);
    try {
      const response = await apiClient.post<{ url: string }>('/api/subscriptions/portal/', {
        return_url: `${window.location.origin}/settings?tab=subscription`
      });

      if (response.url) {
        window.location.href = response.url;
      }
    } catch (error) {
      console.error('Error creating portal session:', error);
      setRedirecting(false);
    }
  };

  const handleReactivate = async () => {
    setRedirecting(true);
    try {
      const response = await apiClient.post<{ checkout_url: string }>('/api/subscriptions/checkout/', {
        success_url: `${window.location.origin}/checkout/success?session_id={CHECKOUT_SESSION_ID}`,
        cancel_url: `${window.location.origin}/subscription/expired`
      });

      if (response.checkout_url) {
        window.location.href = response.checkout_url;
      }
    } catch (error) {
      console.error('Error creating checkout session:', error);
      setRedirecting(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <LoadingSpinner />
      </div>
    );
  }

  const isPastDue = subscriptionStatus?.status === 'past_due';
  const isCanceled = subscriptionStatus?.status === 'canceled';

  return (
    <div className="min-h-screen flex items-center justify-center bg-background p-4">
      <Card className="max-w-md w-full">
        <CardHeader className="text-center">
          <div className="mx-auto mb-4 w-12 h-12 rounded-full bg-destructive/10 flex items-center justify-center">
            <AlertCircle className="h-6 w-6 text-destructive" />
          </div>
          <CardTitle className="text-2xl">
            {isPastDue ? 'Problema com Pagamento' : 'Assinatura Cancelada'}
          </CardTitle>
          <CardDescription>
            {isPastDue
              ? 'Não conseguimos processar seu pagamento'
              : 'Sua assinatura foi cancelada'}
          </CardDescription>
        </CardHeader>

        <CardContent className="space-y-6">
          {isPastDue ? (
            <>
              <Alert variant="destructive">
                <AlertDescription>
                  Detectamos um problema ao cobrar seu cartão de crédito.
                  Atualize seu método de pagamento para continuar usando o CaixaHub.
                </AlertDescription>
              </Alert>

              <div className="space-y-4">
                <Button
                  onClick={handleUpdatePayment}
                  disabled={redirecting}
                  className="w-full"
                  size="lg"
                >
                  {redirecting ? (
                    <>
                      <LoadingSpinner className="mr-2" />
                      Redirecionando...
                    </>
                  ) : (
                    <>
                      <CreditCard className="mr-2 h-4 w-4" />
                      Atualizar Método de Pagamento
                    </>
                  )}
                </Button>

                {subscriptionStatus?.current_period_end && (
                  <p className="text-sm text-center text-muted-foreground">
                    Você tem até{' '}
                    {new Date(subscriptionStatus.current_period_end).toLocaleDateString('pt-BR')}
                    {' '}para atualizar o pagamento
                  </p>
                )}
              </div>
            </>
          ) : (
            <>
              <Alert>
                <AlertDescription>
                  Sua assinatura foi cancelada. Reative para continuar acessando
                  seus dados financeiros e relatórios.
                </AlertDescription>
              </Alert>

              <div className="space-y-4">
                <Button
                  onClick={handleReactivate}
                  disabled={redirecting}
                  className="w-full"
                  size="lg"
                >
                  {redirecting ? (
                    <>
                      <LoadingSpinner className="mr-2" />
                      Redirecionando...
                    </>
                  ) : (
                    <>
                      <RefreshCw className="mr-2 h-4 w-4" />
                      Reativar Assinatura
                    </>
                  )}
                </Button>
              </div>
            </>
          )}

          <div className="pt-4 border-t text-center">
            <p className="text-sm text-muted-foreground">
              Precisa de ajuda?{' '}
              <a
                href="https://wa.me/5517992679645?text=Olá%2C%20vim%20do%20CaixaHub%20e%20gostaria%20de%20falar%20com%20o%20suporte"
                target="_blank"
                rel="noopener noreferrer"
                className="text-primary hover:underline"
              >
                Entre em contato via WhatsApp
              </a>
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
