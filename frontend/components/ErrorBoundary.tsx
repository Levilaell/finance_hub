import React, { Component, ErrorInfo, ReactNode } from 'react';
import { AlertCircle, RefreshCw, Home } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
  onError?: (error: Error, errorInfo: React.ErrorInfo) => void;
}

interface State {
  hasError: boolean;
  error: Error | null;
  errorInfo: ErrorInfo | null;
  errorCount: number;
}

/**
 * Error boundary component to catch and handle React errors gracefully
 */
export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
      errorCount: 0
    };
  }

  static getDerivedStateFromError(error: Error): Partial<State> {
    // Update state so the next render will show the fallback UI
    return {
      hasError: true,
      error
    };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    // Log error to error reporting service
    console.error('Error caught by boundary:', error, errorInfo);
    
    this.setState(prevState => ({
      errorInfo,
      errorCount: prevState.errorCount + 1
    }));

    // Call custom error handler if provided
    if (this.props.onError) {
      this.props.onError(error, errorInfo);
    }

    // Send to error tracking service (e.g., Sentry)
    if (typeof window !== 'undefined' && (window as any).Sentry) {
      (window as any).Sentry.captureException(error, {
        contexts: {
          react: {
            componentStack: errorInfo.componentStack
          }
        }
      });
    }
  }

  handleReset = () => {
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null,
      errorCount: 0
    });
  };

  handleReload = () => {
    window.location.reload();
  };

  handleGoHome = () => {
    window.location.href = '/';
  };

  render() {
    if (this.state.hasError) {
      // Custom fallback UI
      if (this.props.fallback) {
        return <>{this.props.fallback}</>;
      }

      const { error, errorInfo, errorCount } = this.state;
      const isDevelopment = process.env.NODE_ENV === 'development';

      return (
        <div className="min-h-[400px] flex items-center justify-center p-4">
          <Card className="max-w-2xl w-full">
            <CardHeader>
              <div className="flex items-center space-x-2">
                <AlertCircle className="h-6 w-6 text-red-500" />
                <CardTitle className="text-2xl">Oops! Algo deu errado</CardTitle>
              </div>
              <CardDescription>
                Encontramos um erro inesperado. Nossa equipe foi notificada e está trabalhando para resolver.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {errorCount > 2 && (
                <Alert variant="destructive">
                  <AlertTitle>Múltiplos erros detectados</AlertTitle>
                  <AlertDescription>
                    Parece que você está enfrentando problemas recorrentes. 
                    Recomendamos recarregar a página ou limpar o cache do navegador.
                  </AlertDescription>
                </Alert>
              )}

              <div className="space-y-2">
                <h3 className="font-semibold">O que você pode fazer:</h3>
                <ul className="list-disc list-inside space-y-1 text-sm text-gray-600">
                  <li>Tente recarregar a página</li>
                  <li>Volte para a página inicial</li>
                  <li>Verifique sua conexão com a internet</li>
                  <li>Se o problema persistir, entre em contato com o suporte</li>
                </ul>
              </div>

              {isDevelopment && error && (
                <div className="mt-4 p-4 bg-gray-100 rounded-lg">
                  <h4 className="font-semibold text-sm mb-2">Detalhes do erro (desenvolvimento):</h4>
                  <pre className="text-xs overflow-auto">
                    <code className="text-red-600">{error.toString()}</code>
                  </pre>
                  {errorInfo && (
                    <details className="mt-2">
                      <summary className="cursor-pointer text-sm font-medium">
                        Stack trace
                      </summary>
                      <pre className="text-xs overflow-auto mt-2">
                        <code>{errorInfo.componentStack}</code>
                      </pre>
                    </details>
                  )}
                </div>
              )}

              <div className="flex flex-col sm:flex-row gap-2 pt-4">
                <Button 
                  onClick={this.handleReset} 
                  variant="default"
                  className="flex-1"
                >
                  <RefreshCw className="h-4 w-4 mr-2" />
                  Tentar novamente
                </Button>
                <Button 
                  onClick={this.handleReload} 
                  variant="outline"
                  className="flex-1"
                >
                  Recarregar página
                </Button>
                <Button 
                  onClick={this.handleGoHome} 
                  variant="outline"
                  className="flex-1"
                >
                  <Home className="h-4 w-4 mr-2" />
                  Ir para início
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      );
    }

    return this.props.children;
  }
}