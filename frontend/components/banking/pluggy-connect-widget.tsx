'use client';

import { useEffect, useState } from 'react';
import dynamic from 'next/dynamic';
import { toast } from 'sonner';
import { LoadingSpinner } from '@/components/ui/loading-spinner';
import type { PluggyConnectEventPayload, PluggyItem } from '@/types/banking';

const PluggyConnect = dynamic(
  () => import('react-pluggy-connect').then((mod) => mod.PluggyConnect),
  { ssr: false }
);

interface PluggyConnectWidgetProps {
  connectToken: string;
  updateItemId?: string;  // Optional: for updating existing connections (reconnection)
  onSuccess: (itemId: string) => void;
  onError?: (error: any) => void;
  onClose: () => void;
  onEvent?: (event: PluggyConnectEventPayload) => void; // Optional: for tracking MFA events
}

/**
 * Pluggy Connect Widget Component
 * Ref: https://docs.pluggy.ai/docs/environments-and-configurations
 *
 * This widget handles:
 * - Credential validation
 * - Multi-factor authentication (MFA) automatically
 * - Error handling per institution
 *
 * The widget automatically detects and handles MFA requirements:
 * - For 1-step MFA: User provides token upfront
 * - For 2-step MFA: Widget shows field after login when WAITING_USER_INPUT
 */
export function PluggyConnectWidget({
  connectToken,
  updateItemId,
  onSuccess,
  onError,
  onClose,
  onEvent,
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
    // Response can be { item: Item } or { item: Item, itemId: string }
    const itemId = response.itemId || response.item?.id;
    if (!itemId) {
      console.error('No itemId in Pluggy response:', response);
      toast.error('Erro: ID da conexão não encontrado');
      return;
    }

    onSuccess(itemId);
  };

  const handleError = (error: { message: string; data?: any }) => {
    console.error('Pluggy error:', error);
    const errorMessage = updateItemId
      ? 'Erro ao atualizar credenciais'
      : 'Erro ao conectar banco';
    toast.error(errorMessage);
    if (onError) onError(error);
  };

  const handleEvent = (event: any) => {
    // Handle MFA events
    // Ref: https://docs.pluggy.ai/docs/environments-and-configurations
    console.log('Pluggy event:', event);

    // Event payload structure from react-pluggy-connect library
    const eventType = event.event;

    switch (eventType) {
      case 'SUBMITTED_LOGIN':
        toast.info('Credenciais enviadas, validando...', { duration: 2000 });
        break;

      case 'SUBMITTED_MFA':
        toast.info('Código MFA enviado, validando...', { duration: 3000 });
        break;

      case 'LOGIN_MFA_SUCCESS':
        toast.success('Autenticação MFA aprovada!', { duration: 2000 });
        break;

      case 'LOGIN_SUCCESS':
        toast.success('Login realizado com sucesso!', { duration: 2000 });
        break;

      case 'SELECTED_INSTITUTION':
        if (event.connector) {
          console.log('Instituição selecionada:', event.connector.name);
        }
        break;
    }

    // Call custom onEvent handler if provided
    if (onEvent) {
      onEvent(event as PluggyConnectEventPayload);
    }
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
          onEvent={handleEvent}
          language="pt"
        />
      )}
    </div>
  );
}