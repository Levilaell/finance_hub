'use client';

import { useEffect } from 'react';
import { toast } from 'sonner';
import { pluggyService } from '@/services/pluggy.service';
import { useRouter } from 'next/navigation';

interface PluggyConnectHandlerProps {
  onSuccess?: () => void;
  onError?: (error: string) => void;
}

export function PluggyConnectHandler({ onSuccess, onError }: PluggyConnectHandlerProps) {
  const router = useRouter();

  useEffect(() => {
    // Listen for Pluggy Connect events
    const handleMessage = async (event: MessageEvent) => {
      // Validate origin
      if (!event.origin.includes('pluggy.ai')) {
        return;
      }

      console.log('Pluggy event:', event.data);

      // Handle different Pluggy events
      if (event.data.type === 'item/created' || event.data.type === 'success') {
        // Item successfully created
        const itemId = event.data.itemId || event.data.data?.id;
        
        if (itemId) {
          toast.success('Conta conectada com sucesso! Processando...');
          
          try {
            // Process the successful connection
            const result = await pluggyService.handleItemCreated(itemId);
            
            if (result.success) {
              toast.success('Conta sincronizada com sucesso!');
              if (onSuccess) {
                onSuccess();
              } else {
                // Default: redirect to accounts page
                router.push('/accounts');
              }
            }
          } catch (error: any) {
            console.error('Error processing Pluggy item:', error);
            toast.error(error.message || 'Erro ao processar conexão');
            if (onError) {
              onError(error.message);
            }
          }
        }
      } else if (event.data.type === 'error' || event.data.type === 'close') {
        // Handle errors or user closing the widget
        const errorMessage = event.data.message || 'Conexão cancelada pelo usuário';
        
        if (event.data.type === 'error') {
          toast.error(errorMessage);
          if (onError) {
            onError(errorMessage);
          }
        } else {
          toast.info('Conexão cancelada');
        }
      } else if (event.data.type === 'item/update-mfa') {
        // MFA required
        toast.info('Autenticação adicional necessária. Por favor, complete o processo.');
      }
    };

    // Add event listener
    window.addEventListener('message', handleMessage);

    // Cleanup
    return () => {
      window.removeEventListener('message', handleMessage);
    };
  }, [router, onSuccess, onError]);

  return null; // This component doesn't render anything
}