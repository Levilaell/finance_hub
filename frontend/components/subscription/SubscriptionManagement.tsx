'use client';

import { useState, useEffect } from 'react';
import { CreditCard, Calendar, AlertCircle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { LoadingSpinner } from '@/components/ui/loading-spinner';
import { subscriptionService, SubscriptionStatus } from '@/services/subscription.service';
import { toast } from 'sonner';

export function SubscriptionManagement() {
  const [loading, setLoading] = useState(true);
  const [subscription, setSubscription] = useState<SubscriptionStatus | null>(null);
  const [redirecting, setRedirecting] = useState(false);

  useEffect(() => {
    fetchSubscription();
  }, []);

  const fetchSubscription = async () => {
    try {
      const data = await subscriptionService.getStatus();
      setSubscription(data);
    } catch (error) {
      console.error('Error fetching subscription:', error);
      toast.error('Erro ao carregar assinatura');
    } finally {
      setLoading(false);
    }
  };

  const handleManageSubscription = async () => {
    setRedirecting(true);
    try {
      const response = await subscriptionService.createPortalSession();
      if (response.url) {
        window.location.href = response.url;
      }
    } catch (error) {
      console.error('Error creating portal session:', error);
      toast.error('Erro ao abrir portal de gerenciamento');
      setRedirecting(false);
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center py-8">
        <LoadingSpinner />
      </div>
    );
  }

  if (!subscription || subscription.status === 'none') {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Sem Assinatura Ativa</CardTitle>
          <CardDescription>
            Você não possui uma assinatura ativa no momento
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Button onClick={() => window.location.href = '/register'}>
            Ver Planos
          </Button>
        </CardContent>
      </Card>
    );
  }

  const getStatusBadge = () => {
    switch (subscription.status) {
      case 'trialing':
        return <Badge className="bg-blue-500">Trial Ativo</Badge>;
      case 'active':
        return <Badge className="bg-green-500">Ativo</Badge>;
      case 'past_due':
        return <Badge variant="destructive">Pagamento Pendente</Badge>;
      case 'canceled':
        return <Badge variant="secondary">Cancelado</Badge>;
      default:
        return <Badge variant="secondary">{subscription.status}</Badge>;
    }
  };

  return (
    <div className="space-y-6">
      {/* Status Card */}
      <Card>
        <CardHeader>
          <div className="flex justify-between items-start">
            <div>
              <CardTitle>Plano Pro</CardTitle>
              <CardDescription className="mt-2">
                {getStatusBadge()}
              </CardDescription>
            </div>
            <div className="text-right">
              <p className="text-3xl font-bold">
                {subscription.currency === 'BRL' ? 'R$' : '$'} {subscription.amount?.toFixed(2)}
              </p>
              <p className="text-sm text-muted-foreground">por mês</p>
            </div>
          </div>
        </CardHeader>

        <CardContent className="space-y-6">
          {/* Trial Info */}
          {subscription.status === 'trialing' && subscription.trial_end && (
            <Alert className="border-blue-500/50 bg-blue-500/10">
              <AlertCircle className="h-4 w-4 text-blue-500" />
              <AlertDescription>
                <strong>Trial ativo!</strong> {subscription.days_until_renewal} dias restantes.
                Seu cartão será cobrado em{' '}
                {new Date(subscription.trial_end).toLocaleDateString('pt-BR')}.
              </AlertDescription>
            </Alert>
          )}

          {/* Past Due Warning */}
          {subscription.status === 'past_due' && (
            <Alert variant="destructive">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>
                Detectamos um problema com seu pagamento. Atualize seu método de pagamento
                para continuar usando o CaixaHub.
              </AlertDescription>
            </Alert>
          )}

          {/* Subscription Details */}
          <div className="grid gap-4">
            {subscription.status === 'active' && subscription.current_period_end && (
              <div className="flex items-center justify-between py-2 border-b">
                <div className="flex items-center gap-2">
                  <Calendar className="h-4 w-4 text-muted-foreground" />
                  <span className="text-sm">Próxima cobrança</span>
                </div>
                <span className="text-sm font-medium">
                  {new Date(subscription.current_period_end).toLocaleDateString('pt-BR')}
                </span>
              </div>
            )}

            {subscription.payment_method && (
              <div className="flex items-center justify-between py-2 border-b">
                <div className="flex items-center gap-2">
                  <CreditCard className="h-4 w-4 text-muted-foreground" />
                  <span className="text-sm">Forma de pagamento</span>
                </div>
                <span className="text-sm font-medium">
                  {subscription.payment_method.brand?.toUpperCase()} ••••{' '}
                  {subscription.payment_method.last4}
                </span>
              </div>
            )}

            {subscription.cancel_at_period_end && (
              <Alert>
                <AlertDescription>
                  Sua assinatura será cancelada em{' '}
                  {subscription.current_period_end &&
                    new Date(subscription.current_period_end).toLocaleDateString('pt-BR')}
                </AlertDescription>
              </Alert>
            )}
          </div>

          {/* Actions */}
          <div className="flex gap-3 pt-4">
            <Button
              onClick={handleManageSubscription}
              disabled={redirecting}
              className="flex-1"
            >
              {redirecting ? (
                <>
                  <LoadingSpinner className="mr-2" />
                  Redirecionando...
                </>
              ) : (
                'Gerenciar Assinatura'
              )}
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Benefits */}
      <Card>
        <CardHeader>
          <CardTitle>Recursos Incluídos</CardTitle>
        </CardHeader>
        <CardContent>
          <ul className="space-y-2">
            <li className="flex items-center gap-2">
              <div className="h-2 w-2 rounded-full bg-green-500" />
              <span className="text-sm">Conexão ilimitada com bancos</span>
            </li>
            <li className="flex items-center gap-2">
              <div className="h-2 w-2 rounded-full bg-green-500" />
              <span className="text-sm">Transações ilimitadas</span>
            </li>
            <li className="flex items-center gap-2">
              <div className="h-2 w-2 rounded-full bg-green-500" />
              <span className="text-sm">Categorização automática por IA</span>
            </li>
            <li className="flex items-center gap-2">
              <div className="h-2 w-2 rounded-full bg-green-500" />
              <span className="text-sm">Relatórios ilimitados</span>
            </li>
            <li className="flex items-center gap-2">
              <div className="h-2 w-2 rounded-full bg-green-500" />
              <span className="text-sm">Suporte via WhatsApp</span>
            </li>
          </ul>
        </CardContent>
      </Card>
    </div>
  );
}
