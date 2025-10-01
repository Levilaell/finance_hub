'use client';

import { useEffect, useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { CheckCircleIcon } from '@heroicons/react/24/outline';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { LoadingSpinner } from '@/components/ui/loading-spinner';

export default function CheckoutSuccessPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [countdown, setCountdown] = useState(5);

  useEffect(() => {
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
  }, [router]);

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
