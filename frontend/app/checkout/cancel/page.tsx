'use client';

import { useRouter } from 'next/navigation';
import { XCircleIcon } from '@heroicons/react/24/outline';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';

export default function CheckoutCancelPage() {
  const router = useRouter();

  return (
    <div className="min-h-screen bg-background flex items-center justify-center p-4">
      <Card className="max-w-md w-full">
        <CardHeader className="text-center">
          <div className="mx-auto mb-4 w-16 h-16 rounded-full bg-yellow-500/10 flex items-center justify-center">
            <XCircleIcon className="h-10 w-10 text-yellow-500" />
          </div>
          <CardTitle className="text-2xl">Checkout Cancelado</CardTitle>
          <CardDescription>
            Você cancelou o processo de pagamento
          </CardDescription>
        </CardHeader>

        <CardContent className="space-y-6 text-center">
          <p className="text-muted-foreground">
            Não se preocupe! Você pode tentar novamente quando quiser.
          </p>

          <div className="space-y-3">
            <Button
              onClick={() => router.push('/checkout')}
              className="w-full"
              size="lg"
            >
              Tentar Novamente
            </Button>

            <Button
              onClick={() => router.push('/pricing')}
              variant="outline"
              className="w-full"
            >
              Ver Detalhes do Plano
            </Button>
          </div>

          <p className="text-sm text-muted-foreground">
            Precisa de ajuda?{' '}
            <a href="mailto:suporte@caixahub.com" className="text-primary hover:underline">
              Entre em contato
            </a>
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
