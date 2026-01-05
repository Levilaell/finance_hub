'use client';

import { useEffect, useState } from 'react';
import dynamic from 'next/dynamic';
import { toast } from 'sonner';
import { LoadingSpinner } from '@/components/ui/loading-spinner';

const PluggyConnect = dynamic(
  () => import('react-pluggy-connect').then((mod) => mod.PluggyConnect),
  { ssr: false }
);

interface PluggyConnectWidgetProps {
  connectToken: string;
  updateItemId?: string;  // Optional: for updating existing connections
  onSuccess: (itemId: string) => void;
  onError?: (error: any) => void;
  onClose: () => void;
}

export function PluggyConnectWidget({
  connectToken,
  updateItemId,
  onSuccess,
  onError,
  onClose,
}: PluggyConnectWidgetProps) {
  const [isReady, setIsReady] = useState(false);

  useEffect(() => {
    // Small delay to ensure proper rendering
    const timer = setTimeout(() => setIsReady(true), 100);
    return () => clearTimeout(timer);
  }, []);

  const handleSuccess = (response: any) => {
    const successMessage = updateItemId
      ? 'Credenciais atualizadas com sucesso!'
      : 'Banco conectado com sucesso!';
    toast.success(successMessage);

    // Pluggy returns itemId in the response
    const itemId = response.itemId || response.item?.id;
    if (!itemId) {
      console.error('No itemId in Pluggy response:', response);
      toast.error('Erro: ID da conexão não encontrado');
      return;
    }

    onSuccess(itemId);
  };

  const handleError = (error: any) => {
    console.error('Pluggy error:', error);
    const errorMessage = updateItemId
      ? 'Erro ao atualizar credenciais'
      : 'Erro ao conectar banco';
    toast.error(errorMessage);
    if (onError) onError(error);
  };

  const handleExit = () => {
    onClose();
  };

  return (
    <div className="w-full">
      {!isReady ? (
        <div className="flex items-center justify-center min-h-[500px]">
          <LoadingSpinner />
        </div>
      ) : (
        <PluggyConnect
          connectToken={connectToken}
          updateItem={updateItemId}
          onSuccess={handleSuccess}
          onError={handleError}
        />
      )}
    </div>
  );
}