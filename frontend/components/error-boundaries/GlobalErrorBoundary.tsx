'use client';

import React, { Component, ErrorInfo, ReactNode } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { AlertTriangle, RefreshCw, Home, Bug } from 'lucide-react';

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

interface GlobalErrorFallbackProps {
  error: Error | null;
  resetError: () => void;
  errorId: string;
}

// Fallback component for global errors
function GlobalErrorFallback({ error, resetError, errorId }: GlobalErrorFallbackProps) {
  const reloadPage = () => {
    window.location.reload();
  };

  const goHome = () => {
    window.location.href = '/';
  };

  const reportError = () => {
    const subject = encodeURIComponent('Application Error Report');
    const body = encodeURIComponent(`
Error ID: ${errorId}
Error: ${error?.message || 'Unknown error'}
URL: ${window.location.href}
Timestamp: ${new Date().toISOString()}
User Agent: ${navigator.userAgent}

Please describe what you were doing when this error occurred:

`);
    window.open(`mailto:support@financehub.com?subject=${subject}&body=${body}`, '_blank');
  };

  return (
    <div className="flex items-center justify-center min-h-screen p-4 bg-gray-50">
      <Card className="w-full max-w-lg">
        <CardHeader className="text-center">
          <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-red-50">
            <AlertTriangle className="h-8 w-8 text-red-600" />
          </div>
          <CardTitle className="text-2xl">Something went wrong</CardTitle>
          <CardDescription>
            We encountered an unexpected error. Our team has been notified and is working on a fix.
          </CardDescription>
        </CardHeader>
        
        <CardContent className="space-y-4">
          <Alert>
            <Bug className="h-4 w-4" />
            <AlertDescription>
              Error ID: <code className="text-xs bg-gray-100 px-2 py-1 rounded font-mono">{errorId}</code>
            </AlertDescription>
          </Alert>

          {error && (
            <div className="rounded-md bg-gray-50 p-3">
              <div className="text-sm font-medium text-gray-700 mb-1">Error Details:</div>
              <div className="text-xs text-gray-600 font-mono break-all">
                {error.message}
              </div>
            </div>
          )}

          <div className="space-y-2">
            <Button onClick={resetError} className="w-full">
              <RefreshCw className="mr-2 h-4 w-4" />
              Try Again
            </Button>
            
            <div className="grid grid-cols-2 gap-2">
              <Button variant="outline" onClick={reloadPage}>
                <RefreshCw className="mr-2 h-4 w-4" />
                Reload Page
              </Button>
              
              <Button variant="outline" onClick={goHome}>
                <Home className="mr-2 h-4 w-4" />
                Go Home
              </Button>
            </div>
            
            <Button variant="ghost" onClick={reportError} className="w-full text-sm">
              <Bug className="mr-2 h-4 w-4" />
              Report This Error
            </Button>
          </div>

          <div className="text-xs text-gray-500 text-center pt-4 border-t">
            <p>If this problem persists, please contact our support team.</p>
            <p className="mt-1">
              Email: <a href="mailto:support@financehub.com" className="text-blue-600 hover:underline">
                support@financehub.com
              </a>
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

export class GlobalErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false, error: null, errorId: '' };
  }

  static getDerivedStateFromError(error: Error): State {
    // Generate unique error ID for tracking
    const errorId = `GE-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
    
    return {
      hasError: true,
      error,
      errorId
    };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    // Log error for monitoring
    console.error('Global Error Boundary caught an error:', error, errorInfo);
    
    // Call onError callback if provided
    if (this.props.onError) {
      this.props.onError(error, errorInfo);
    }

    // Log to external monitoring service in production
    if (process.env.NODE_ENV === 'production') {
      this.logErrorToService(error, errorInfo, this.state.errorId);
    }
  }

  private logErrorToService = (error: Error, errorInfo: ErrorInfo, errorId: string) => {
    const errorData = {
      errorId,
      error: {
        name: error.name,
        message: error.message,
        stack: error.stack,
      },
      errorInfo: {
        componentStack: errorInfo.componentStack,
      },
      timestamp: new Date().toISOString(),
      url: window.location.href,
      userAgent: navigator.userAgent,
      context: 'GlobalErrorBoundary',
      buildInfo: {
        version: process.env.NEXT_PUBLIC_APP_VERSION || 'unknown',
        environment: process.env.NODE_ENV
      }
    };

    console.error('Production Global Error:', JSON.stringify(errorData, null, 2));
    
    // In production, you would send this to your monitoring service
    // Example integrations:
    // - Sentry: Sentry.captureException(error, { contexts: { errorBoundary: errorData } });
    // - LogRocket: LogRocket.captureException(error);
    // - DataDog: datadogRum.addError(error, errorData);
    
    try {
      // Send to your own error logging endpoint
      fetch('/api/errors/log', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(errorData)
      }).catch(e => {
        console.error('Failed to log error to service:', e);
      });
    } catch (e) {
      // Silently fail - don't want error logging to cause more errors
    }
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
        <GlobalErrorFallback
          error={this.state.error}
          resetError={this.resetError}
          errorId={this.state.errorId}
        />
      );
    }

    return this.props.children;
  }
}

export default GlobalErrorBoundary;