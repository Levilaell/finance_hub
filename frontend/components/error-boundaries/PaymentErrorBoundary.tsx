'use client';

import React, { Component, ErrorInfo, ReactNode } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { AlertCircle, RefreshCw, CreditCard, ArrowLeft } from 'lucide-react';
import { useRouter } from 'next/navigation';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
  onError?: (error: Error, errorInfo: ErrorInfo) => void;
}

interface State {
  hasError: boolean;
  error: Error | null;
  errorId: string;
}

interface PaymentErrorBoundaryFallbackProps {
  error: Error | null;
  resetError: () => void;
  errorId: string;
}

// Fallback component for payment errors
function PaymentErrorFallback({ error, resetError, errorId }: PaymentErrorBoundaryFallbackProps) {
  const router = useRouter();

  const getErrorMessage = (error: Error | null): { title: string; description: string; action: string } => {
    if (!error) {
      return {
        title: 'Something went wrong',
        description: 'An unexpected error occurred with payment processing.',
        action: 'Try again'
      };
    }

    const message = error.message.toLowerCase();

    // Payment-specific error messages
    if (message.includes('payment') && message.includes('failed')) {
      return {
        title: 'Payment Failed',
        description: 'Your payment could not be processed. Please check your payment method and try again.',
        action: 'Try payment again'
      };
    }

    if (message.includes('card') || message.includes('payment method')) {
      return {
        title: 'Payment Method Issue',
        description: 'There was an issue with your payment method. Please update your payment information.',
        action: 'Update payment method'
      };
    }

    if (message.includes('subscription')) {
      return {
        title: 'Subscription Error',
        description: 'There was an issue with your subscription. Please contact support if this continues.',
        action: 'Retry subscription'
      };
    }

    if (message.includes('network') || message.includes('connection')) {
      return {
        title: 'Connection Error',
        description: 'Unable to connect to payment services. Please check your internet connection.',
        action: 'Retry connection'
      };
    }

    // Generic payment error
    return {
      title: 'Payment Service Error',
      description: 'There was an issue processing your request. Please try again or contact support.',
      action: 'Try again'
    };
  };

  const { title, description, action } = getErrorMessage(error);

  const handleContactSupport = () => {
    window.open('mailto:support@financehub.com?subject=Payment Error&body=Error ID: ' + errorId, '_blank');
  };

  return (
    <div className="flex items-center justify-center min-h-[400px] p-4">
      <Card className="w-full max-w-md">
        <CardHeader className="text-center">
          <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-red-50">
            <AlertCircle className="h-6 w-6 text-red-600" />
          </div>
          <CardTitle className="text-xl">{title}</CardTitle>
          <CardDescription>{description}</CardDescription>
        </CardHeader>
        
        <CardContent className="space-y-4">
          <Alert>
            <CreditCard className="h-4 w-4" />
            <AlertDescription>
              Error ID: <code className="text-xs bg-gray-100 px-1 py-0.5 rounded">{errorId}</code>
            </AlertDescription>
          </Alert>

          <div className="space-y-2">
            <Button onClick={resetError} className="w-full">
              <RefreshCw className="mr-2 h-4 w-4" />
              {action}
            </Button>
            
            <Button
              variant="outline"
              onClick={() => router.push('/subscription')}
              className="w-full"
            >
              <ArrowLeft className="mr-2 h-4 w-4" />
              Go to Subscription
            </Button>
            
            <Button
              variant="ghost"
              onClick={handleContactSupport}
              className="w-full text-sm"
            >
              Contact Support
            </Button>
          </div>

          <div className="text-xs text-gray-500 text-center mt-4">
            If this problem persists, please contact our support team with the error ID above.
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

export class PaymentErrorBoundary extends Component<Props, State> {
  private errorId: string;

  constructor(props: Props) {
    super(props);
    this.state = { hasError: false, error: null, errorId: '' };
    this.errorId = '';
  }

  static getDerivedStateFromError(error: Error): State {
    // Generate unique error ID for tracking
    const errorId = `PE-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
    
    return {
      hasError: true,
      error,
      errorId
    };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    // Log error for monitoring
    console.error('Payment Error Boundary caught an error:', error, errorInfo);
    
    // Call onError callback if provided
    if (this.props.onError) {
      this.props.onError(error, errorInfo);
    }

    // Log to external monitoring service in production
    if (process.env.NODE_ENV === 'production') {
      // Example: Send to Sentry, LogRocket, etc.
      this.logErrorToService(error, errorInfo, this.state.errorId);
    }

    this.errorId = this.state.errorId;
  }

  private logErrorToService = (error: Error, errorInfo: ErrorInfo, errorId: string) => {
    // Integration with monitoring services would go here
    // For now, just log to console in production with structured format
    const errorData = {
      errorId,
      error: {
        name: error.name,
        message: error.message,
        stack: error.stack,
      },
      errorInfo,
      timestamp: new Date().toISOString(),
      url: window.location.href,
      userAgent: navigator.userAgent,
      context: 'PaymentErrorBoundary'
    };

    console.error('Production Payment Error:', JSON.stringify(errorData, null, 2));
    
    // Example integration with external service:
    // try {
    //   fetch('/api/errors/log', {
    //     method: 'POST',
    //     headers: { 'Content-Type': 'application/json' },
    //     body: JSON.stringify(errorData)
    //   });
    // } catch (e) {
    //   console.error('Failed to log error to service:', e);
    // }
  };

  resetError = () => {
    this.setState({ hasError: false, error: null, errorId: '' });
  };

  render() {
    if (this.state.hasError) {
      // Use custom fallback if provided, otherwise use default
      if (this.props.fallback) {
        return this.props.fallback;
      }

      return (
        <PaymentErrorFallback
          error={this.state.error}
          resetError={this.resetError}
          errorId={this.state.errorId}
        />
      );
    }

    return this.props.children;
  }
}

// Hook for easier integration with function components
export function usePaymentErrorHandler() {
  const handleError = (error: Error, context: string = 'payment') => {
    console.error(`Payment Error in ${context}:`, error);
    
    // Return user-friendly error message
    if (error.message.includes('payment') && error.message.includes('failed')) {
      return 'Payment failed. Please try again or contact support.';
    }
    
    if (error.message.includes('network') || error.message.includes('fetch')) {
      return 'Connection error. Please check your internet and try again.';
    }
    
    return 'Something went wrong. Please try again or contact support.';
  };

  return { handleError };
}

export default PaymentErrorBoundary;