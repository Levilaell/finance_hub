'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { AlertCircle, CreditCard, ArrowLeft } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { LoadingSpinner } from '@/components/ui/loading-spinner';
import apiClient from '@/lib/api-client';

export default function TrialUsedPage() {
  const router = useRouter();
  const [redirecting, setRedirecting] = useState(false);

  const handleSubscribe = async () => {
    setRedirecting(true);
    try {
      const response = await apiClient.post<{ checkout_url: string }>('/api/subscriptions/checkout/', {
        success_url: `${window.location.origin}/checkout/success?session_id={CHECKOUT_SESSION_ID}`,
        cancel_url: `${window.location.origin}/subscription/trial-used`
      });

      if (response.checkout_url) {
        window.location.href = response.checkout_url;
      }
    } catch (error) {
      console.error('Error creating checkout session:', error);
      setRedirecting(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-background p-4">
      <Card className="max-w-md w-full">
        <CardHeader className="text-center">
          <div className="mx-auto mb-4 w-12 h-12 rounded-full bg-amber-500/10 flex items-center justify-center">
            <AlertCircle className="h-6 w-6 text-amber-500" />
          </div>
          <CardTitle className="text-2xl">
            Trial Já Utilizado
          </CardTitle>
          <CardDescription>
            Você já utilizou seu período de teste gratuito
          </CardDescription>
        </CardHeader>

        <CardContent className="space-y-6">
          <Alert>
            <AlertDescription>
              <p className="mb-2">
                Nossos registros indicam que você já utilizou o período de teste de 7 dias do CaixaHub.
              </p>
              <p className="text-sm text-muted-foreground">
                Para continuar aproveitando todos os recursos da plataforma, assine nosso plano Pro.
              </p>
            </AlertDescription>
          </Alert>

          {/* Pricing Info */}
          <div className="bg-muted/50 rounded-lg p-4 text-center">
            <p className="text-sm text-muted-foreground mb-2">Plano Pro</p>
            <div className="text-3xl font-bold mb-1">R$ 97,00</div>
            <p className="text-sm text-muted-foreground">por mês</p>
          </div>

          {/* Features */}
          <div className="space-y-2">
            <p className="text-sm font-semibold">Incluído no plano:</p>
            <ul className="space-y-1 text-sm text-muted-foreground">
              <li className="flex items-center gap-2">
                <div className="h-1.5 w-1.5 rounded-full bg-green-500" />
                Conexão ilimitada com bancos
              </li>
              <li className="flex items-center gap-2">
                <div className="h-1.5 w-1.5 rounded-full bg-green-500" />
                Transações ilimitadas
              </li>
              <li className="flex items-center gap-2">
                <div className="h-1.5 w-1.5 rounded-full bg-green-500" />
                Categorização automática por IA
              </li>
              <li className="flex items-center gap-2">
                <div className="h-1.5 w-1.5 rounded-full bg-green-500" />
                Relatórios ilimitados
              </li>
              <li className="flex items-center gap-2">
                <div className="h-1.5 w-1.5 rounded-full bg-green-500" />
                Suporte prioritário
              </li>
            </ul>
          </div>

          {/* Actions */}
          <div className="space-y-3">
            <Button
              onClick={handleSubscribe}
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
                  Assinar Plano Pro
                </>
              )}
            </Button>

            <Button
              onClick={() => router.push('/')}
              variant="outline"
              className="w-full"
              size="lg"
            >
              <ArrowLeft className="mr-2 h-4 w-4" />
              Voltar para Home
            </Button>
          </div>

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
