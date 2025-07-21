'use client';

import { useRouter } from 'next/navigation';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { XCircleIcon } from '@heroicons/react/24/outline';

export default function PaymentCancelPage() {
  const router = useRouter();

  return (
    <div className="min-h-screen flex items-center justify-center p-4">
      <Card className="max-w-md w-full">
        <CardHeader className="text-center">
          <div className="flex justify-center mb-4">
            <XCircleIcon className="h-16 w-16 text-gray-400" />
          </div>
          <CardTitle className="text-2xl">Pagamento Cancelado</CardTitle>
          <CardDescription className="mt-2">
            Você cancelou o processo de pagamento. Nenhuma cobrança foi realizada.
          </CardDescription>
        </CardHeader>
        
        <CardContent className="text-center space-y-4">
          <p className="text-sm text-gray-600">
            Você ainda está no período de teste. Configure o pagamento antes que expire para continuar usando todos os recursos.
          </p>
          
          <div className="flex flex-col space-y-2">
            <Button
              onClick={() => router.push('/settings?tab=status')}
              className="w-full"
            >
              Voltar para Configurações
            </Button>
            
            <Button
              variant="outline"
              onClick={() => router.push('/dashboard')}
              className="w-full"
            >
              Ir para o Dashboard
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}