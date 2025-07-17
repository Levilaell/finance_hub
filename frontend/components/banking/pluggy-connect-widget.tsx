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
  const containerRef = useRef<HTMLDivElement>(null);

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
      if (pluggyInstance.current) {
        try {
          if (typeof pluggyInstance.current.destroy === 'function') {
            pluggyInstance.current.destroy();
          }
          // Remover qualquer iframe ou modal que possa ter ficado
          const iframes = document.querySelectorAll('iframe[src*="pluggy"]');
          iframes.forEach(iframe => iframe.remove());
          
          const modals = document.querySelectorAll('[class*="pluggy"], [id*="pluggy"]');
          modals.forEach(modal => modal.remove());
        } catch (e) {
          console.error('Error cleaning up Pluggy:', e);
        }
      }
    };
  }, []);

  useEffect(() => {
    if (!sdkLoaded || !connectToken || !window.PluggyConnect) {
      return;
    }

    console.log('🔌 Initializing Pluggy Connect with token:', connectToken.substring(0, 20) + '...');
    
    // Função wrapper para garantir que onClose sempre existe
    const handleClose = () => {
      console.log('🚪 Pluggy Connect is closing');
      
      // Remover manualmente o widget se ele não fechar sozinho
      setTimeout(() => {
        const iframes = document.querySelectorAll('iframe[src*="pluggy"]');
        iframes.forEach(iframe => iframe.remove());
        
        const modals = document.querySelectorAll('[class*="pluggy"], [id*="pluggy"]');
        modals.forEach(modal => modal.remove());
      }, 100);
      
      if (onClose && typeof onClose === 'function') {
        onClose();
      }
    };
    
    try {
      // Configuração do Pluggy Connect
      const config = {
        connectToken: connectToken,
        includeSandbox: true, // Mudando para true já que você está em desenvolvimento
        
        onSuccess: (data: any) => {
          console.log('✅ Pluggy Connect success:', data);
          
          const itemId = data?.item?.id || data?.itemId || data?.id;
          
          if (itemId) {
            toast.success('Conta conectada com sucesso!');
            onSuccess({ 
              item: { 
                id: itemId,
                ...(data.item || {})
              } 
            });
          } else {
            console.error('❌ No itemId in success response:', data);
            toast.error('Erro: ID da conexão não encontrado');
            onError(new Error('No itemId received'));
          }
          
          handleClose();
        },
        
        onError: (error: any) => {
          console.log('❌ Pluggy Connect error:', error);
          
          const errorMessage = error?.message || error?.error || 'Erro ao conectar com o banco';
          toast.error(errorMessage);
          onError(new Error(errorMessage));
          
          handleClose();
        },
        
        onExit: handleClose,
        
        // Tentar adicionar onClose em diferentes formatos
        onClose: handleClose,
        props: {
          onClose: handleClose
        },
        
        // Eventos para debug
        onEvent: (event: string, metadata: any) => {
          console.log(`📊 Pluggy event: ${event}`, metadata);
          
          // Detectar eventos de fechamento
          if (event === 'CLOSE' || event === 'EXIT' || event === 'CANCEL') {
            handleClose();
          }
        }
      };

      console.log('Creating Pluggy instance with config:', { 
        ...config, 
        connectToken: config.connectToken.substring(0, 20) + '...' 
      });
      
      // Criar instância do Pluggy Connect
      pluggyInstance.current = new window.PluggyConnect(config);
      
      // Abrir o widget
      if (pluggyInstance.current.init && typeof pluggyInstance.current.init === 'function') {
        pluggyInstance.current.init();
      } else if (pluggyInstance.current.open && typeof pluggyInstance.current.open === 'function') {
        pluggyInstance.current.open();
      }
      
      // Fallback: se o widget não fechar sozinho após alguns segundos sem atividade
      const inactivityTimer = setTimeout(() => {
        console.log('⏰ Inactivity timeout - checking if widget is still open');
        const iframes = document.querySelectorAll('iframe[src*="pluggy"]');
        if (iframes.length === 0) {
          // Widget já foi fechado
          handleClose();
        }
      }, 300000); // 5 minutos
      
      // Limpar timer ao destruir
      return () => {
        clearTimeout(inactivityTimer);
      };
      
    } catch (error: any) {
      console.error('❌ Error initializing Pluggy Connect:', error);
      toast.error('Erro ao inicializar conexão bancária');
      onError(error);
    }
  }, [sdkLoaded, connectToken, onSuccess, onError, onClose]);

  // Container invisível para o widget
  return <div ref={containerRef} style={{ display: 'none' }} />;
}

// Componente alternativo que cria um overlay customizado
export function PluggyConnectModal({
  connectToken,
  onSuccess,
  onError,
  onClose
}: PluggyConnectWidgetProps) {
  const [isOpen, setIsOpen] = useState(true);
  
  const handleClose = () => {
    setIsOpen(false);
    if (onClose) {
      onClose();
    }
  };

  if (!isOpen) return null;

  return (
    <>
      {/* Overlay */}
      <div 
        className="fixed inset-0 bg-black/50 z-[9998]"
        onClick={handleClose}
      />
      
      {/* Container para o Pluggy */}
      <div className="fixed inset-0 z-[9999] flex items-center justify-center pointer-events-none">
        <div className="pointer-events-auto relative">
          {/* Botão de fechar customizado */}
          <button
            onClick={handleClose}
            className="absolute -top-10 right-0 text-white hover:text-gray-300 text-2xl font-bold z-[10000]"
            aria-label="Fechar"
          >
            ✕
          </button>
          
          {/* Widget do Pluggy */}
          <PluggyConnectWidget
            connectToken={connectToken}
            onSuccess={(data) => {
              onSuccess(data);
              handleClose();
            }}
            onError={(error) => {
              onError(error);
              handleClose();
            }}
            onClose={handleClose}
          />
        </div>
      </div>
    </>
  );
}