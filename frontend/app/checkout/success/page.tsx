'use client';

import { useEffect, useState, Suspense } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { CheckCircleIcon } from '@heroicons/react/24/outline';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { LoadingSpinner } from '@/components/ui/loading-spinner';

function CheckoutSuccessContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [countdown, setCountdown] = useState(5);
  const [verifying, setVerifying] = useState(true);
  const [subscriptionActive, setSubscriptionActive] = useState(false);

  useEffect(() => {
    verifySubscription();
  }, []);

  const verifySubscription = async () => {
    try {
      // Wait 2s for webhook to process
      await new Promise(resolve => setTimeout(resolve, 2000));

      const response = await fetch('/api/subscriptions/status/', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
      });

      if (response.ok) {
        const status = await response.json();
        setSubscriptionActive(
          status.status === 'trialing' || status.status === 'active'
        );
      }
    } catch (error) {
      console.error('Error verifying subscription:', error);
      // Assume success if verification fails
      setSubscriptionActive(true);
    } finally {
      setVerifying(false);
    }
  };

  useEffect(() => {
    if (!verifying && subscriptionActive) {
      // Auto redirect after 5 seconds
      const timer = setInterval(() => {
        setCountdown((prev) => {
          if (prev <= 1) {
            router.push('/dashboard');
            return 0;
          }
          return prev - 1;
        });
      }, 1000);

      return () => clearInterval(timer);
    }
  }, [router, verifying, subscriptionActive]);

  if (verifying) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center p-4">
        <Card className="max-w-md w-full text-center p-8">
          <LoadingSpinner className="mx-auto mb-4" />
          <p className="text-muted-foreground">Verificando sua assinatura...</p>
        </Card>
      </div>
    );
  }

  if (!subscriptionActive) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center p-4">
        <Card className="max-w-md w-full text-center p-8 space-y-4">
          <p className="text-muted-foreground">
            Estamos processando sua assinatura. Por favor, aguarde alguns instantes...
          </p>
          <Button onClick={() => router.push('/dashboard')} variant="outline">
            Ir para o Dashboard
          </Button>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background flex items-center justify-center p-4">
      <Card className="max-w-md w-full">
        <CardHeader className="text-center">
          <div className="mx-auto mb-4 w-16 h-16 rounded-full bg-green-500/10 flex items-center justify-center">
            <CheckCircleIcon className="h-10 w-10 text-green-500" />
          </div>
          <CardTitle className="text-2xl">Trial Ativado com Sucesso!</CardTitle>
          <CardDescription>
            Seu trial de 7 dias começou agora
          </CardDescription>
        </CardHeader>

        <CardContent className="space-y-6 text-center">
          <div className="py-4 space-y-2">
            <p className="text-muted-foreground">
              Parabéns! Você agora tem acesso completo a todos os recursos do CaixaHub.
            </p>
            <p className="text-sm text-muted-foreground">
              Seu cartão será cobrado R$ 97,00 após 7 dias. Cancele a qualquer momento sem custos.
            </p>
          </div>

          <div className="space-y-3">
            <Button
              onClick={() => router.push('/dashboard')}
              className="w-full"
              size="lg"
            >
              Ir para o Dashboard
            </Button>

            <p className="text-sm text-muted-foreground">
              Redirecionando automaticamente em {countdown}s...
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

export default function CheckoutSuccessPage() {
  return (
    <Suspense fallback={<LoadingSpinner />}>
      <CheckoutSuccessContent />
    </Suspense>
  );
}
