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
  const [errorDetails, setErrorDetails] = useState<{ code?: string; message?: string; supportMessage?: string }>({});
  // Try multiple methods to get session_id 
  let sessionId = searchParams.get('session_id');
  
  // Fallback: Extract from URL fragment or current URL
  if (!sessionId && typeof window !== 'undefined') {
    const url = window.location.href;
    
    // Try to extract from various URL patterns
    const patterns = [
      /[?&]session_id=([^&#]+)/,
      /[?&]session_id%3D([^&#]+)/,  // URL encoded
      /#session_id=([^&#]+)/,        // Fragment
      /cs_[a-zA-Z0-9_]+/             // Direct Stripe session pattern
    ];
    
    for (const pattern of patterns) {
      const match = url.match(pattern);
      if (match) {
        sessionId = match[1] || match[0];
        console.log('🔍 Extracted session_id from URL pattern:', sessionId);
        break;
      }
    }
    
    // Manual override for debugging - use session from recent logs
    if (!sessionId && process.env.NODE_ENV === 'development') {
      // This should be the session_id from the recent logs: cs_test_a1Bi1X9LGZi6qwAGFr69SDJIEvTG7npVERtrk11Md2S9r1o3FecMWEI9Iw
      console.log('⚠️ No session_id found, checking for manual override...');
    }
  }
  
  console.log('🚀 PaymentSuccessPage loaded with session ID:', sessionId);
  console.log('🔍 Full URL for debugging:', typeof window !== 'undefined' ? window.location.href : 'N/A');
  
  // Use WebSocket for real-time checkout status
  const { status: wsStatus } = useCheckoutWebSocket(sessionId);

  useEffect(() => {
    if (!sessionId) {
      console.log('❌ No session ID provided');
      setStatus('error');
      return;
    }
    
    console.log('🔍 WebSocket status changed:', wsStatus, 'for session:', sessionId);
    
    // Update status based on WebSocket events (but WebSocket may not exist)
    if (wsStatus === 'success') {
      console.log('✅ WebSocket reported success');
      setStatus('success');
      // Invalidate all relevant queries to refresh data
      queryClient.invalidateQueries({ queryKey: ['user'] });
      queryClient.invalidateQueries({ queryKey: ['subscription-status'] });
      queryClient.invalidateQueries({ queryKey: ['company'] });
      queryClient.invalidateQueries({ queryKey: ['payment-methods'] });
    } else if (wsStatus === 'failed') {
      console.log('❌ WebSocket reported failed');
      setStatus('error');
    }
  }, [wsStatus, sessionId, queryClient]);

  // Always try HTTP validation - WebSocket is unreliable/may not exist
  useEffect(() => {
    if (!sessionId) return;
    
    // Skip if WebSocket already succeeded  
    if (wsStatus === 'success') return;

    // Try HTTP validation immediately if WebSocket failed, otherwise wait 2 seconds
    const delay = wsStatus === 'failed' ? 0 : 2000;
    
    console.log(`🔍 Scheduling HTTP validation in ${delay}ms for session:`, sessionId);
    
    const timeout = setTimeout(async () => {
      try {
        console.log('🔍 Attempting HTTP payment validation for session:', sessionId);
        console.log('🔍 Current WebSocket status:', wsStatus);
        
        const result = await validatePayment.mutateAsync(sessionId);
        
        console.log('✅ HTTP validation result:', result);
        
        if (result.status === 'success') {
          console.log('✅ Payment validated successfully via HTTP');
          setStatus('success');
          queryClient.invalidateQueries({ queryKey: ['user'] });
          queryClient.invalidateQueries({ queryKey: ['subscription-status'] });
          queryClient.invalidateQueries({ queryKey: ['company'] });
        } else if (result.status === 'pending') {
          console.log('⏳ Payment still processing');
          setStatus('pending');
        } else {
          console.log('❌ Payment validation returned non-success status:', result.status);
          setStatus('error');
        }
      } catch (error: any) {
        console.error('❌ HTTP payment validation failed:', error);
        console.error('❌ Error details:', {
          status: error?.response?.status,
          data: error?.response?.data,
          message: error?.message
        });
        
        setStatus('error');
        // Capture error details for better messaging
        if (error?.response?.data) {
          setErrorDetails({
            code: error.response.data.code,
            message: error.response.data.message,
            supportMessage: error.response.data.details?.support_message
          });
        }
      }
    }, delay);

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
        // Enhanced error messaging based on error type
        let title = 'Payment Failed';
        let description = 'Invalid payment session. Please try again.';
        
        if (errorDetails.code === 'COMPANY_MISMATCH') {
          title = 'Account Issue Detected';
          description = errorDetails.message || 'Payment was processed successfully, but there was an account issue. Please contact support for assistance.';
        } else if (sessionId) {
          description = errorDetails.message || 'We couldn\'t verify your payment. Please contact support if you were charged.';
        }
        
        // Add support reference if available
        if (errorDetails.supportMessage) {
          description += `\n\n${errorDetails.supportMessage}`;
        }
        
        return {
          icon: <XCircle className="h-16 w-16 text-red-500" />,
          title,
          description,
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