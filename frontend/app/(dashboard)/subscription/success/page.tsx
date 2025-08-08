'use client';

import { useEffect, useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { CheckCircle, XCircle, Loader2 } from 'lucide-react';
import { useSubscription } from '@/hooks/useSubscription';
import { useCheckoutWebSocket } from '@/hooks/usePaymentWebSocket';
import { useQueryClient } from '@tanstack/react-query';

export default function PaymentSuccessPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const queryClient = useQueryClient();
  const { validatePayment } = useSubscription();
  const [status, setStatus] = useState<'checking' | 'success' | 'error' | 'pending'>('checking');
  const sessionId = searchParams.get('session_id');
  
  // Use WebSocket for real-time checkout status
  const { status: wsStatus } = useCheckoutWebSocket(sessionId);

  useEffect(() => {
    if (!sessionId) {
      setStatus('error');
      return;
    }
    
    // Update status based on WebSocket events
    if (wsStatus === 'success') {
      setStatus('success');
      // Invalidate all relevant queries to refresh data
      queryClient.invalidateQueries({ queryKey: ['user'] });
      queryClient.invalidateQueries({ queryKey: ['subscription-status'] });
      queryClient.invalidateQueries({ queryKey: ['company'] });
      queryClient.invalidateQueries({ queryKey: ['payment-methods'] });
    } else if (wsStatus === 'failed') {
      setStatus('error');
    }
  }, [wsStatus, sessionId, queryClient]);

  // Fallback: validate payment if WebSocket doesn't update within 5 seconds
  useEffect(() => {
    if (!sessionId || wsStatus) return;

    const timeout = setTimeout(async () => {
      try {
        const result = await validatePayment.mutateAsync(sessionId);
        
        if (result.status === 'success') {
          setStatus('success');
          queryClient.invalidateQueries({ queryKey: ['user'] });
          queryClient.invalidateQueries({ queryKey: ['subscription-status'] });
          queryClient.invalidateQueries({ queryKey: ['company'] });
        } else {
          setStatus('pending');
        }
      } catch (error) {
        setStatus('error');
      }
    }, 5000);

    return () => clearTimeout(timeout);
  }, [sessionId, wsStatus, validatePayment, queryClient]);

  const getContent = () => {
    switch (status) {
      case 'checking':
        return {
          icon: <Loader2 className="h-16 w-16 text-primary animate-spin" />,
          title: 'Processing Your Payment',
          description: 'Please wait while we confirm your subscription...',
          showButton: false,
        };
      case 'success':
        return {
          icon: <CheckCircle className="h-16 w-16 text-green-500" />,
          title: 'Payment Successful!',
          description: 'Your subscription has been activated. Welcome to Finance Hub!',
          showButton: true,
        };
      case 'pending':
        return {
          icon: <Loader2 className="h-16 w-16 text-yellow-500 animate-spin" />,
          title: 'Payment Processing',
          description: 'Your payment is still being processed. This may take a few moments...',
          showButton: false,
        };
      case 'error':
        return {
          icon: <XCircle className="h-16 w-16 text-red-500" />,
          title: 'Payment Failed',
          description: sessionId 
            ? 'We couldn\'t verify your payment. Please contact support if you were charged.'
            : 'Invalid payment session. Please try again.',
          showButton: true,
        };
    }
  };

  const content = getContent();

  return (
    <div className="container mx-auto flex items-center justify-center min-h-[600px]">
      <Card className="w-full max-w-md text-center">
        <CardHeader className="space-y-6">
          <div className="flex justify-center">{content.icon}</div>
          <div className="space-y-2">
            <CardTitle className="text-2xl">{content.title}</CardTitle>
            <CardDescription>{content.description}</CardDescription>
          </div>
        </CardHeader>
        {content.showButton && (
          <CardContent>
            {status === 'success' ? (
              <Button 
                className="w-full" 
                onClick={() => router.push('/dashboard')}
              >
                Go to Dashboard
              </Button>
            ) : (
              <div className="space-y-3">
                <Button 
                  className="w-full" 
                  onClick={() => router.push('/subscription/upgrade')}
                >
                  Try Again
                </Button>
                <Button 
                  variant="outline" 
                  className="w-full" 
                  onClick={() => router.push('/dashboard')}
                >
                  Go to Dashboard
                </Button>
              </div>
            )}
          </CardContent>
        )}
      </Card>
    </div>
  );
}