'use client';

import { useEffect, useRef, useState } from 'react';
import { toast } from 'sonner';

interface PluggyConnectWidgetProps {
  connectToken: string;
  onSuccess: (itemData: any) => void;
  onError: (error: any) => void;
  onClose?: () => void;
}

// Declaração global para o SDK da Pluggy
declare global {
  interface Window {
    PluggyConnect: any;
  }
}

export function PluggyConnectWidget({
  connectToken,
  onSuccess,
  onError,
  onClose
}: PluggyConnectWidgetProps) {
  const [sdkLoaded, setSdkLoaded] = useState(false);
  const pluggyInstance = useRef<any>(null);

  useEffect(() => {
    // Carregar o SDK da Pluggy
    const script = document.createElement('script');
    script.src = 'https://cdn.pluggy.ai/pluggy-connect.js';
    script.async = true;
    script.onload = () => {
      console.log('✅ Pluggy SDK loaded');
      setSdkLoaded(true);
    };
    script.onerror = () => {
      console.error('❌ Failed to load Pluggy SDK');
      onError(new Error('Failed to load Pluggy SDK'));
    };
    
    document.body.appendChild(script);

    return () => {
      // Cleanup
      if (script.parentNode) {
        script.parentNode.removeChild(script);
      }
      
      // Destruir instância se existir
      if (pluggyInstance.current && pluggyInstance.current.destroy) {
        pluggyInstance.current.destroy();
      }
    };
  }, []);

  useEffect(() => {
    if (!sdkLoaded || !connectToken || !window.PluggyConnect) {
      return;
    }

    console.log('🔌 Initializing Pluggy Connect...');
    
    try {
      // Criar instância do Pluggy Connect
      pluggyInstance.current = new window.PluggyConnect({
        connectToken: connectToken,
        includeSandbox: false, // Em produção deve ser false
        updateItem: null,
        // Configurações opcionais
        products: ['ACCOUNTS', 'TRANSACTIONS'], // Produtos que queremos acessar
        countries: ['BR'], // Apenas Brasil
        language: 'pt', // Português
        
        // Callbacks
        onSuccess: (data: any) => {
          console.log('✅ Pluggy Connect success:', data);
          
          // A resposta pode vir em diferentes formatos
          const itemId = data?.item?.id || data?.itemId || data?.data?.itemId;
          
          if (itemId) {
            onSuccess({ 
              item: { 
                id: itemId,
                ...data.item 
              } 
            });
          } else {
            console.error('❌ No itemId in success response:', data);
            onError(new Error('No itemId received'));
          }
        },
        
        onError: (error: any) => {
          console.error('❌ Pluggy Connect error:', error);
          
          const errorMessage = error?.message || error?.error || 'Erro ao conectar com o banco';
          onError(new Error(errorMessage));
        },
        
        onExit: () => {
          console.log('🚪 Pluggy Connect closed');
          if (onClose) {
            onClose();
          }
        },
        
        // Eventos adicionais para debug
        onEvent: (event: string, metadata: any) => {
          console.log(`📊 Pluggy event: ${event}`, metadata);
          
          switch (event) {
            case 'OPEN':
              toast.info('Abrindo conexão com o banco...');
              break;
            case 'SELECT_INSTITUTION':
              if (metadata?.connector?.name) {
                toast.info(`Conectando com ${metadata.connector.name}...`);
              }
              break;
            case 'SUBMIT_CREDENTIALS':
              toast.loading('Validando credenciais...', { id: 'pluggy-auth' });
              break;
            case 'LOGIN_SUCCESS':
              toast.dismiss('pluggy-auth');
              toast.success('Login realizado com sucesso!');
              break;
            case 'ACCOUNT_CREATED':
              toast.success('Conta conectada!');
              break;
            case 'ERROR':
              toast.dismiss('pluggy-auth');
              break;
          }
        }
      });
      
      // Abrir o widget
      pluggyInstance.current.init()
        .then(() => {
          console.log('✅ Pluggy Connect opened');
        })
        .catch((error: any) => {
          console.error('❌ Failed to open Pluggy Connect:', error);
          onError(error);
        });
      
    } catch (error: any) {
      console.error('❌ Error initializing Pluggy Connect:', error);
      onError(error);
    }
  }, [sdkLoaded, connectToken, onSuccess, onError, onClose]);

  // Componente não renderiza nada - o SDK cria seu próprio modal
  return null;
}

// Componente alternativo que abre em popup (método antigo)
export function PluggyConnectPopup({
  connectToken,
  onSuccess,
  onError,
  onClose
}: PluggyConnectWidgetProps) {
  const windowRef = useRef<Window | null>(null);
  const intervalRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    if (!connectToken) {
      console.error('No connect token provided');
      return;
    }

    // URL correta segundo a documentação
    const pluggyConnectUrl = `https://connect.pluggy.ai/?connectToken=${connectToken}`;
    
    console.log('🔗 Opening Pluggy Connect popup...');
    
    // Configurações da janela
    const width = 500;
    const height = 700;
    const left = (window.screen.width - width) / 2;
    const top = (window.screen.height - height) / 2;
    
    const windowFeatures = `width=${width},height=${height},left=${left},top=${top},toolbar=no,location=no,directories=no,status=no,menubar=no,scrollbars=yes,resizable=yes`;
    
    // Abrir janela
    windowRef.current = window.open(pluggyConnectUrl, 'pluggy-connect', windowFeatures);
    
    if (!windowRef.current) {
      toast.error('Por favor, permita pop-ups para conectar sua conta bancária');
      onError(new Error('Pop-up bloqueado'));
      return;
    }

    // Handler para mensagens
    const handleMessage = (event: MessageEvent) => {
      // Verificar origem
      if (!event.origin.includes('pluggy.ai')) {
        return;
      }

      console.log('📬 Message from Pluggy:', event.data);

      const data = event.data;
      
      // Sucesso
      if (data.success === true && data.item) {
        onSuccess({ item: data.item });
        closeWindow();
      }
      // Erro
      else if (data.error || data.type === 'error') {
        onError(new Error(data.message || 'Erro na conexão'));
        closeWindow();
      }
      // Fechado
      else if (data.type === 'close' || data.type === 'exit') {
        if (onClose) onClose();
        closeWindow();
      }
    };

    const closeWindow = () => {
      if (windowRef.current && !windowRef.current.closed) {
        windowRef.current.close();
      }
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };

    window.addEventListener('message', handleMessage);

    // Verificar se janela foi fechada
    intervalRef.current = setInterval(() => {
      if (windowRef.current && windowRef.current.closed) {
        if (onClose) onClose();
        if (intervalRef.current) {
          clearInterval(intervalRef.current);
        }
      }
    }, 1000);

    // Cleanup
    return () => {
      window.removeEventListener('message', handleMessage);
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
      if (windowRef.current && !windowRef.current.closed) {
        windowRef.current.close();
      }
    };
  }, [connectToken, onSuccess, onError, onClose]);

  return null;
}