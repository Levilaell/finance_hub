'use client';

import { useEffect, useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { LoadingSpinner } from '@/components/ui/loading-spinner';
import { CheckCircleIcon, XCircleIcon, ClockIcon } from '@heroicons/react/24/outline';
import { paymentService } from '@/services/payment.service';
import { toast } from 'sonner';
import { useAuthStore } from '@/store/auth-store';

export default function PaymentSuccessPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const queryClient = useQueryClient();
  const { fetchUser } = useAuthStore();
  const [paymentStatus, setPaymentStatus] = useState<'checking' | 'success' | 'pending' | 'failed'>('checking');
  
  const validatePaymentMutation = useMutation({
    mutationFn: async () => {
      const sessionId = searchParams.get('session_id');
      const paymentId = searchParams.get('payment_id');
      
      if (!sessionId && !paymentId) {
        throw new Error('No payment information found');
      }
      
      return paymentService.validatePayment({
        session_id: sessionId || undefined,
        payment_id: paymentId || undefined,
      });
    },
    onSuccess: async (data) => {
      setPaymentStatus(data.status);
      
      if (data.status === 'success') {
        toast.success('Pagamento confirmado! Sua assinatura está ativa.');
        
        // Clear all caches and force refresh user data
        try {
          // Clear localStorage and sessionStorage
          localStorage.clear();
          sessionStorage.clear();
          
          // Clear React Query cache
          queryClient.clear();
          
          // Force fetch fresh user data
          await fetchUser();
          
          // Dispatch event to notify all components
          window.dispatchEvent(new CustomEvent('subscription-updated'));
          
          // Force reload to ensure all components are refreshed
          setTimeout(() => {
            window.location.href = '/dashboard';
          }, 2000);
        } catch (error) {
          console.error('Error refreshing data:', error);
          // Still redirect even if refresh fails
          window.location.href = '/dashboard';
        }
      } else if (data.status === 'pending') {
        toast.info('Pagamento pendente. Você receberá uma confirmação por email.');
      } else {
        toast.error('Falha no pagamento. Tente novamente.');
      }
    },
    onError: (error: any) => {
      setPaymentStatus('failed');
      toast.error('Erro ao verificar pagamento');
    },
  });
  
  useEffect(() => {
    validatePaymentMutation.mutate();
  }, [validatePaymentMutation]);
  
  const getStatusContent = () => {
    switch (paymentStatus) {
      case 'checking':
        return {
          icon: <LoadingSpinner className="h-16 w-16" />,
          title: 'Verificando pagamento...',
          description: 'Por favor, aguarde enquanto confirmamos seu pagamento.',
          showButton: false,
        };
      case 'success':
        return {
          icon: <CheckCircleIcon className="h-16 w-16 text-green-500" />,
          title: 'Pagamento confirmado!',
          description: 'Sua assinatura está ativa. Você será redirecionado em instantes...',
          showButton: true,
        };
      case 'pending':
        return {
          icon: <ClockIcon className="h-16 w-16 text-yellow-500" />,
          title: 'Pagamento pendente',
          description: 'Seu pagamento está sendo processado. Você receberá uma confirmação por email assim que for aprovado.',
          showButton: true,
        };
      case 'failed':
        return {
          icon: <XCircleIcon className="h-16 w-16 text-red-500" />,
          title: 'Pagamento não processado',
          description: 'Não conseguimos processar seu pagamento. Por favor, tente novamente.',
          showButton: true,
        };
    }
  };
  
  const content = getStatusContent();
  
  return (
    <div className="min-h-screen flex items-center justify-center p-4">
      <Card className="max-w-md w-full">
        <CardHeader className="text-center">
          <div className="flex justify-center mb-4">
            {content.icon}
          </div>
          <CardTitle className="text-2xl">{content.title}</CardTitle>
          <CardDescription className="mt-2">
            {content.description}
          </CardDescription>
        </CardHeader>
        
        {content.showButton && (
          <CardContent className="text-center">
            <Button
              onClick={() => router.push('/dashboard')}
              className="w-full sm:w-auto"
            >
              Ir para o Dashboard
            </Button>
            
            {paymentStatus === 'failed' && (
              <Button
                variant="outline"
                onClick={() => router.push('/dashboard/subscription/upgrade')}
                className="w-full sm:w-auto mt-2"
              >
                Tentar Novamente
              </Button>
            )}
          </CardContent>
        )}
      </Card>
    </div>
  );
}