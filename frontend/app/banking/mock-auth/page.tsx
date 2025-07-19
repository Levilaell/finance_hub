'use client';

import { useEffect, useState, Suspense } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { CheckCircle, Building2, AlertCircle } from 'lucide-react';

function MockAuthContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [bankName, setBankName] = useState('');

  useEffect(() => {
    // Extract bank info from URL or localStorage
    const clientId = searchParams.get('client_id');
    const redirectUri = searchParams.get('redirect_uri');
    const state = searchParams.get('state');
    const consentId = searchParams.get('consent_id');
    
    // Set bank name based on redirect or stored info
    setBankName('Banco Simulado');
  }, [searchParams]);

  const handleAuthorize = () => {
    const redirectUri = searchParams.get('redirect_uri');
    const state = searchParams.get('state');
    
    if (redirectUri && state) {
      // Generate mock authorization code
      const authCode = `mock-auth-code-${Date.now()}`;
      
      // Redirect back to callback with authorization code
      const callbackUrl = `${redirectUri}?code=${authCode}&state=${state}`;
      window.location.href = callbackUrl;
    } else {
      // Fallback to default callback
      router.push(`/banking/callback?code=mock-auth-code-${Date.now()}&state=mock-state`);
    }
  };

  const handleDeny = () => {
    const redirectUri = searchParams.get('redirect_uri');
    const state = searchParams.get('state');
    
    if (redirectUri && state) {
      const callbackUrl = `${redirectUri}?error=access_denied&state=${state}`;
      window.location.href = callbackUrl;
    } else {
      router.push('/dashboard/accounts');
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 px-4">
      <Card className="w-full max-w-md">
        <CardHeader className="text-center">
          <CardTitle className="flex items-center justify-center gap-2">
            <Building2 className="w-6 h-6 text-blue-600" />
            Autorização Bancária
          </CardTitle>
        </CardHeader>

        <CardContent className="space-y-6">
          <div className="text-center">
            <h2 className="text-lg font-semibold text-gray-800 mb-2">
              {bankName}
            </h2>
            <p className="text-gray-600 text-sm">
              A aplicação Finance Management está solicitando acesso às suas informações bancárias.
            </p>
          </div>

          <div className="bg-blue-50 p-4 rounded-lg">
            <h3 className="font-medium text-blue-800 mb-2 flex items-center gap-2">
              <CheckCircle className="w-4 h-4" />
              Permissões Solicitadas:
            </h3>
            <ul className="text-sm text-blue-700 space-y-1">
              <li>• Visualizar informações da conta</li>
              <li>• Acessar saldo e extratos</li>
              <li>• Ler histórico de transações</li>
            </ul>
          </div>

          <div className="bg-amber-50 p-4 rounded-lg">
            <div className="flex items-start gap-2">
              <AlertCircle className="w-4 h-4 text-amber-600 mt-0.5" />
              <div className="text-sm text-amber-700">
                <p className="font-medium mb-1">Ambiente de Desenvolvimento</p>
                <p>Esta é uma simulação para fins de teste. Em produção, você seria redirecionado para o portal do seu banco.</p>
              </div>
            </div>
          </div>

          <div className="space-y-3">
            <Button 
              onClick={handleAuthorize} 
              className="w-full bg-blue-600 hover:bg-blue-700"
            >
              Autorizar Acesso
            </Button>
            <Button 
              onClick={handleDeny} 
              variant="outline" 
              className="w-full"
            >
              Negar Acesso
            </Button>
          </div>

          <div className="text-xs text-gray-500 text-center">
            Ao autorizar, você concorda em compartilhar suas informações bancárias com a Finance Management de forma segura e criptografada.
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

export default function MockAuthPage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen flex items-center justify-center bg-gray-50 px-4">
        <Card className="w-full max-w-md">
          <CardContent className="flex flex-col items-center space-y-4 pt-6">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
            <p className="text-gray-600">Carregando...</p>
          </CardContent>
        </Card>
      </div>
    }>
      <MockAuthContent />
    </Suspense>
  );
}