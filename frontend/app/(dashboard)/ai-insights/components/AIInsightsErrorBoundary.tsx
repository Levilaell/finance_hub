'use client';

import React, { Component, ErrorInfo, ReactNode } from 'react';
import { AlertCircle, RefreshCw, Home } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
  errorInfo: ErrorInfo | null;
  errorCount: number;
}

export class AIInsightsErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
      errorCount: 0,
    };
  }

  static getDerivedStateFromError(error: Error): State {
    // Atualizar state para mostrar a UI de fallback
    return {
      hasError: true,
      error,
      errorInfo: null,
      errorCount: 0,
    };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    // Log do erro para serviços de monitoramento
    if (process.env.NODE_ENV === 'development') {
      console.error('AI Insights Error Boundary caught an error:', error, errorInfo);
    }

    // Incrementar contador de erros
    this.setState(prevState => ({
      error,
      errorInfo,
      errorCount: prevState.errorCount + 1,
    }));

    // Em produção, você poderia enviar para um serviço de monitoramento
    // Exemplo: Sentry.captureException(error, { contexts: { react: { componentStack: errorInfo.componentStack } } });
  }

  handleReset = () => {
    // Limpar o estado de erro e tentar renderizar novamente
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null,
      errorCount: 0,
    });
  };

  handleRefresh = () => {
    // Recarregar a página
    window.location.reload();
  };

  handleGoHome = () => {
    // Navegar para o dashboard
    window.location.href = '/dashboard';
  };

  render() {
    if (this.state.hasError) {
      // Determinar a mensagem de erro baseada no tipo
      const isCompanyError = this.state.error?.message?.includes('company') || 
                            this.state.error?.message?.includes('NO_COMPANY');
      
      const isNetworkError = this.state.error?.message?.includes('Network') ||
                            this.state.error?.message?.includes('fetch');

      return (
        <div className="flex items-center justify-center min-h-[600px] p-6">
          <Card className="max-w-2xl w-full">
            <CardHeader>
              <div className="flex items-center gap-2">
                <AlertCircle className="h-6 w-6 text-destructive" />
                <CardTitle>Oops! Algo deu errado</CardTitle>
              </div>
              <CardDescription>
                Encontramos um problema ao carregar o AI Insights
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {/* Mensagem específica do erro */}
              <Alert variant={isCompanyError ? "default" : "destructive"}>
                <AlertCircle className="h-4 w-4" />
                <AlertTitle>
                  {isCompanyError 
                    ? "Cadastro Incompleto" 
                    : isNetworkError 
                      ? "Erro de Conexão"
                      : "Erro Inesperado"}
                </AlertTitle>
                <AlertDescription>
                  {isCompanyError 
                    ? "Para usar o AI Insights, você precisa completar o cadastro da sua empresa. Por favor, acesse as configurações e finalize seu cadastro." 
                    : isNetworkError 
                      ? "Não foi possível conectar aos nossos servidores. Verifique sua conexão com a internet e tente novamente."
                      : "Ocorreu um erro inesperado. Por favor, tente novamente ou entre em contato com o suporte se o problema persistir."}
                </AlertDescription>
              </Alert>

              {/* Detalhes do erro em desenvolvimento */}
              {process.env.NODE_ENV === 'development' && this.state.error && (
                <Alert>
                  <AlertTitle>Detalhes do Erro (Dev)</AlertTitle>
                  <AlertDescription className="mt-2">
                    <pre className="text-xs overflow-auto max-h-40 p-2 bg-muted rounded">
                      {this.state.error.toString()}
                      {this.state.errorInfo?.componentStack}
                    </pre>
                  </AlertDescription>
                </Alert>
              )}

              {/* Contador de tentativas */}
              {this.state.errorCount > 1 && (
                <Alert>
                  <AlertDescription>
                    Erro ocorreu {this.state.errorCount} vezes. Se o problema persistir, tente recarregar a página.
                  </AlertDescription>
                </Alert>
              )}

              {/* Ações */}
              <div className="flex gap-2 flex-wrap">
                {isCompanyError ? (
                  <Button
                    onClick={() => window.location.href = '/settings?tab=company'}
                    className="flex items-center gap-2"
                  >
                    Completar Cadastro
                  </Button>
                ) : (
                  <Button
                    onClick={this.handleReset}
                    variant="default"
                    className="flex items-center gap-2"
                  >
                    <RefreshCw className="h-4 w-4" />
                    Tentar Novamente
                  </Button>
                )}
                
                <Button
                  onClick={this.handleRefresh}
                  variant="outline"
                  className="flex items-center gap-2"
                >
                  <RefreshCw className="h-4 w-4" />
                  Recarregar Página
                </Button>
                
                <Button
                  onClick={this.handleGoHome}
                  variant="outline"
                  className="flex items-center gap-2"
                >
                  <Home className="h-4 w-4" />
                  Ir para Dashboard
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