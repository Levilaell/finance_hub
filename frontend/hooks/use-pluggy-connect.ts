// Hook for Pluggy Connect integration

import { useState, useCallback, useEffect, useRef } from 'react';
import { useMutation } from '@tanstack/react-query';
import { toast } from 'sonner';
import { bankingService } from '@/services/banking.service';
import { BankingErrorHandler } from '@/utils/banking-errors';
import type { ConnectTokenRequest } from '@/types/banking.types';

declare global {
  interface Window {
    PluggyConnect?: any;
  }
}

interface UsePluggyConnectOptions {
  onSuccess?: (itemId: string) => void;
  onError?: (error: any) => void;
  onExit?: () => void;
}

export function usePluggyConnect(options?: UsePluggyConnectOptions) {
  const [isConnecting, setIsConnecting] = useState(false);
  const [pluggyConnect, setPluggyConnect] = useState<any>(null);
  const [isSDKLoaded, setIsSDKLoaded] = useState(false);
  const scriptRef = useRef<HTMLScriptElement | null>(null);

  // Create connect token
  const createToken = useMutation({
    mutationFn: (params?: ConnectTokenRequest) => bankingService.createConnectToken(params),
    onError: (error: any) => {
      toast.error(error.response?.data?.error || 'Erro ao criar token de conexão');
    }
  });

  // Load Pluggy SDK
  useEffect(() => {
    if (typeof window === 'undefined') return;

    // Check if already loaded
    if (window.PluggyConnect) {
      setIsSDKLoaded(true);
      return;
    }

    // Check if script already exists
    const existingScript = document.querySelector('script[src="https://cdn.pluggy.ai/pluggy-connect.js"]');
    if (existingScript) {
      scriptRef.current = existingScript as HTMLScriptElement;
      // Wait for it to load
      existingScript.addEventListener('load', () => setIsSDKLoaded(true));
      return;
    }

    const script = document.createElement('script');
    script.src = 'https://cdn.pluggy.ai/pluggy-connect.js';
    script.async = true;
    script.onload = () => {
      if (window.PluggyConnect) {
        console.log('Pluggy Connect SDK loaded');
        setIsSDKLoaded(true);
      }
    };
    script.onerror = () => {
      console.error('Failed to load Pluggy Connect SDK');
      toast.error('Erro ao carregar SDK do Pluggy. Por favor, recarregue a página.');
      setIsSDKLoaded(false);
    };

    scriptRef.current = script;
    document.head.appendChild(script);

    return () => {
      // Don't remove the script on cleanup to avoid reloading issues
      // The script will be reused if the component remounts
    };
  }, []);

  // Open Pluggy Connect
  const openConnect = useCallback(async (params?: ConnectTokenRequest) => {
    if (!isSDKLoaded || !window.PluggyConnect) {
      toast.error('SDK do Pluggy ainda está carregando. Por favor, aguarde.');
      return;
    }

    // Prevent multiple connections
    if (isConnecting) {
      console.warn('Connection already in progress');
      return;
    }

    setIsConnecting(true);

    try {
      // Get connect token
      const tokenResponse = await createToken.mutateAsync(params);
      
      if (!tokenResponse.success || !tokenResponse.data?.connect_token) {
        throw new Error(tokenResponse.error || 'Failed to create connect token');
      }
      
      // Configure Pluggy Connect
      const config: any = {
        connectToken: tokenResponse.data.connect_token,
        includeSandbox: false, // Always use production connectors
        language: 'pt',
        theme: 'light',
        onSuccess: async (data: any) => {
          console.log('Pluggy Connect success:', data);
          const itemId = data.item?.id || data.itemId;
          
          if (!itemId) {
            console.error('No item ID received from Pluggy Connect');
            toast.error('Erro ao processar conexão');
            setIsConnecting(false);
            return;
          }
          
          try {
            // Process the callback to save connection in our backend
            const callbackResponse = await bankingService.handleCallback({ item_id: itemId });
            
            if (callbackResponse.success) {
              toast.success(callbackResponse.data?.message || 'Conta conectada com sucesso!');
              options?.onSuccess?.(itemId);
            } else {
              const error = BankingErrorHandler.parseApiError(callbackResponse);
              const errorDisplay = BankingErrorHandler.getErrorDisplay(error);
              toast.error(errorDisplay.message);
            }
          } catch (error) {
            console.error('Error processing connection:', error);
            const bankingError = BankingErrorHandler.parseApiError(error);
            const errorDisplay = BankingErrorHandler.getErrorDisplay(bankingError);
            toast.error(errorDisplay.message);
          } finally {
            setIsConnecting(false);
            if (pluggyConnect) {
              pluggyConnect.close();
              setPluggyConnect(null);
            }
          }
        },
        onError: (error: any) => {
          console.error('Pluggy Connect error:', error);
          
          // Handle specific Pluggy errors
          let errorMessage = 'Erro ao conectar conta';
          
          if (error.code === 'USER_CANCELLED') {
            errorMessage = 'Conexão cancelada';
          } else if (error.code === 'INVALID_CREDENTIALS') {
            errorMessage = 'Credenciais inválidas. Por favor, verifique seus dados.';
          } else if (error.code === 'INSTITUTION_UNAVAILABLE') {
            errorMessage = 'Instituição temporáriamente indisponível.';
          } else if (error.message) {
            errorMessage = error.message;
          }
          
          toast.error(errorMessage);
          options?.onError?.(error);
          setIsConnecting(false);
          
          if (pluggyConnect) {
            pluggyConnect.close();
            setPluggyConnect(null);
          }
        },
        onEvent: (event: any, data: any) => {
          console.log('Pluggy Connect event:', event, data);
          
          // Track important events
          switch (event) {
            case 'SUBMITTED_CONSENT':
              console.log('User submitted consent');
              break;
            case 'SELECTED_INSTITUTION':
              console.log('User selected institution:', data);
              break;
            case 'ERROR':
              console.error('Connect error:', data);
              break;
            case 'EXIT':
              options?.onExit?.();
              setIsConnecting(false);
              break;
          }
        }
      };

      // Create and open Pluggy Connect
      const connect = new window.PluggyConnect(config);
      setPluggyConnect(connect);
      
      // Add error boundary
      try {
        connect.open();
      } catch (error) {
        console.error('Error opening Pluggy Connect:', error);
        toast.error('Erro ao abrir conexão. Por favor, tente novamente.');
        setIsConnecting(false);
        setPluggyConnect(null);
      }

    } catch (error: any) {
      console.error('Error in openConnect:', error);
      const bankingError = BankingErrorHandler.parseApiError(error);
      const errorDisplay = BankingErrorHandler.getErrorDisplay(bankingError);
      toast.error(errorDisplay.message);
      setIsConnecting(false);
      
      if (pluggyConnect) {
        pluggyConnect.close();
        setPluggyConnect(null);
      }
    }
  }, [createToken, options, isSDKLoaded, isConnecting, pluggyConnect]);

  // Update existing connection
  const updateConnection = useCallback(async (itemId: string) => {
    await openConnect({ item_id: itemId });
  }, [openConnect]);

  // Close Pluggy Connect
  const closeConnect = useCallback(() => {
    if (pluggyConnect) {
      pluggyConnect.close();
      setPluggyConnect(null);
    }
    setIsConnecting(false);
  }, [pluggyConnect]);

  return {
    openConnect,
    updateConnection,
    closeConnect,
    isConnecting,
    isLoadingToken: createToken.isPending,
    isSDKLoaded,
  };
}