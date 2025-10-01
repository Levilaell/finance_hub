'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { BanknotesIcon, CreditCardIcon } from '@heroicons/react/24/outline';
import Link from 'next/link';
import { useAuthStore } from '@/store/auth-store';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { LoadingSpinner } from '@/components/ui/loading-spinner';
import { subscriptionService } from '@/services/subscription.service';
import { toast } from 'sonner';

export default function CheckoutPage() {
  const router = useRouter();
  const { user, isAuthenticated } = useAuthStore();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!isAuthenticated) {
      router.push('/login?redirect=/checkout');
    }
  }, [isAuthenticated, router]);

  const handleStartCheckout = async () => {
    setLoading(true);
    setError(null);

    try {
      const result = await subscriptionService.createCheckoutSession();

      if (result.checkout_url) {
        // Redireciona para Stripe Checkout hospedado
        window.location.href = result.checkout_url;
      } else {
        throw new Error('URL de checkout não recebida');
      }
    } catch (err: any) {
      console.error('Checkout error:', err);
      setError(err.response?.data?.error || err.message || 'Erro ao iniciar checkout');
      toast.error('Erro ao iniciar checkout', {
        description: err.response?.data?.error || err.message,
      });
      setLoading(false);
    }
  };

  if (!isAuthenticated) {
    return null;
  }

  return (
    <div className="min-h-screen bg-background flex items-center justify-center p-4">
      <div className="w-full max-w-lg space-y-6">
        {/* Header */}
        <div className="text-center">
          <Link href="/dashboard" className="inline-flex items-center space-x-2 mb-8">
            <div className="h-10 w-10 rounded-full bg-white/10 border border-white/20 flex items-center justify-center">
              <BanknotesIcon className="h-6 w-6 text-white" />
            </div>
            <span className="text-2xl font-bold text-white">CaixaHub</span>
          </Link>

          <h1 className="text-3xl font-bold text-white mt-8 mb-2">
            Ative seu Trial de 7 Dias
          </h1>
          <p className="text-muted-foreground">
            Olá, {user?.first_name}! Complete o checkout para começar a usar o CaixaHub
          </p>
        </div>

        {/* Checkout Card */}
        <Card>
          <CardHeader className="text-center">
            <div className="mx-auto mb-4 w-16 h-16 rounded-full bg-primary/10 flex items-center justify-center">
              <CreditCardIcon className="h-8 w-8 text-primary" />
            </div>
            <CardTitle className="text-2xl">Plano Pro</CardTitle>
            <CardDescription>
              Acesso completo a todos os recursos
            </CardDescription>
          </CardHeader>

          <CardContent className="space-y-6">
            {/* Pricing */}
            <div className="text-center py-4 border-y">
              <div className="text-4xl font-bold text-white mb-2">
                R$ 97,00
              </div>
              <p className="text-sm text-muted-foreground">
                por mês após o trial
              </p>
            </div>

            {/* Trial Notice */}
            <Alert>
              <AlertDescription className="space-y-2">
                <p>
                  <strong>7 dias de trial grátis</strong>
                </p>
                <p className="text-sm">
                  Você não será cobrado durante os 7 dias de trial. Cancele a qualquer momento sem custos.
                </p>
              </AlertDescription>
            </Alert>

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
              </ul>
            </div>

            {error && (
              <Alert variant="destructive">
                <AlertDescription>{error}</AlertDescription>
              </Alert>
            )}

            {/* Checkout Button */}
            <Button
              onClick={handleStartCheckout}
              disabled={loading}
              className="w-full"
              size="lg"
            >
              {loading ? (
                <>
                  <LoadingSpinner className="mr-2" />
                  Redirecionando para checkout...
                </>
              ) : (
                <>
                  <CreditCardIcon className="mr-2 h-5 w-5" />
                  Continuar para Pagamento Seguro
                </>
              )}
            </Button>

            <p className="text-xs text-center text-muted-foreground">
              Você será redirecionado para o checkout seguro da Stripe
            </p>
          </CardContent>
        </Card>

        {/* Security Notice */}
        <div className="text-center text-sm text-muted-foreground space-y-1">
          <p>🔒 Pagamento 100% seguro processado pela Stripe</p>
          <p>Seus dados são protegidos com criptografia de nível bancário</p>
        </div>
      </div>
    </div>
  );
}
