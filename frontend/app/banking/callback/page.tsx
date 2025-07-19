'use client';

import { useEffect, useState, Suspense } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { bankingService } from '@/services/banking.service';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { LoadingSpinner } from '@/components/ui/loading-spinner';
import { CheckCircle, XCircle, AlertCircle } from 'lucide-react';

function BankingCallbackContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [status, setStatus] = useState<'loading' | 'success' | 'error'>('loading');
  const [message, setMessage] = useState<string>('');
  const [accountInfo, setAccountInfo] = useState<{
    account_id?: string;
    account_name?: string;
    balance?: number;
  } | null>(null);

  useEffect(() => {
    const processCallback = async () => {
      try {
        const code = searchParams.get('code');
        const state = searchParams.get('state');
        const error = searchParams.get('error');
        const bankCode = localStorage.getItem('pending_bank_connection');

        if (error) {
          setStatus('error');
          setMessage(`Erro na autorização: ${error}`);
          return;
        }

        if (!code) {
          setStatus('error');
          setMessage('Código de autorização não encontrado');
          return;
        }

        if (!bankCode) {
          setStatus('error');
          setMessage('Código do banco não encontrado. Por favor, inicie o processo novamente.');
          return;
        }

        // Complete the OAuth flow
        const result = await bankingService.handleOAuthCallback(code, bankCode, state || undefined);

        if (result.status === 'success') {
          setStatus('success');
          setMessage(result.message);
          setAccountInfo({
            account_id: result.account_id,
            account_name: result.account_name,
            balance: result.balance,
          });

          // Clear the pending connection
          localStorage.removeItem('pending_bank_connection');

          // Redirect to accounts page after 3 seconds
          setTimeout(() => {
            router.push('/dashboard/accounts');
          }, 3000);
        } else {
          setStatus('error');
          setMessage(result.message || 'Erro ao conectar conta');
        }
      } catch (error: any) {
        console.error('Callback processing error:', error);
        setStatus('error');
        setMessage(error.message || 'Erro interno. Tente novamente.');
      }
    };

    processCallback();
  }, [searchParams, router]);

  const handleRetry = () => {
    router.push('/dashboard/accounts');
  };

  const handleGoToDashboard = () => {
    router.push('/dashboard');
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 px-4">
      <Card className="w-full max-w-md">
        <CardHeader className="text-center">
          <CardTitle className="flex items-center justify-center gap-2">
            {status === 'loading' && (
              <>
                <LoadingSpinner className="w-6 h-6" />
                Processando Autorização
              </>
            )}
            {status === 'success' && (
              <>
                <CheckCircle className="w-6 h-6 text-green-600" />
                Conta Conectada!
              </>
            )}
            {status === 'error' && (
              <>
                <XCircle className="w-6 h-6 text-red-600" />
                Erro na Conexão
              </>
            )}
          </CardTitle>
        </CardHeader>

        <CardContent className="space-y-4">
          {status === 'loading' && (
            <div className="text-center">
              <p className="text-gray-600">
                Estamos processando sua autorização com o banco. 
                Isso pode levar alguns segundos...
              </p>
            </div>
          )}

          {status === 'success' && (
            <div className="text-center space-y-4">
              <p className="text-green-600 font-medium">{message}</p>
              
              {accountInfo && (
                <div className="bg-green-50 p-4 rounded-lg">
                  <h3 className="font-medium text-green-800 mb-2">
                    Detalhes da Conta:
                  </h3>
                  <div className="text-sm text-green-700 space-y-1">
                    <p><strong>Nome:</strong> {accountInfo.account_name}</p>
                    <p><strong>Saldo:</strong> R$ {accountInfo.balance?.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}</p>
                  </div>
                </div>
              )}

              <div className="flex items-center gap-2 text-sm text-blue-600">
                <AlertCircle className="w-4 h-4" />
                Redirecionando para suas contas em alguns segundos...
              </div>

              <Button onClick={handleGoToDashboard} className="w-full">
                Ir para Dashboard
              </Button>
            </div>
          )}

          {status === 'error' && (
            <div className="text-center space-y-4">
              <div className="bg-red-50 p-4 rounded-lg">
                <p className="text-red-600">{message}</p>
              </div>

              <div className="space-y-2">
                <Button onClick={handleRetry} className="w-full">
                  Tentar Novamente
                </Button>
                <Button 
                  onClick={handleGoToDashboard} 
                  variant="outline" 
                  className="w-full"
                >
                  Voltar ao Dashboard
                </Button>
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

export default function BankingCallbackPage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen flex items-center justify-center bg-gray-50 px-4">
        <Card className="w-full max-w-md">
          <CardContent className="flex flex-col items-center space-y-4 pt-6">
            <LoadingSpinner className="w-6 h-6" />
            <p className="text-gray-600">Carregando...</p>
          </CardContent>
        </Card>
      </div>
    }>
      <BankingCallbackContent />
    </Suspense>
  );
}