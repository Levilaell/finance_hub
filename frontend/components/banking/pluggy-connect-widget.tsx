'use client';

import { useEffect, useRef, useState } from 'react';
import { toast } from 'sonner';

interface PluggyConnectWidgetProps {
  connectToken: string;
  onSuccess: (itemData: any) => void;
  onError: (error: any) => void;
  onClose?: () => void;
  updateItem?: string; // Add support for reconnection
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
  onClose,
  updateItem
}: PluggyConnectWidgetProps) {
  const [sdkLoaded, setSdkLoaded] = useState(false);
  const pluggyInstance = useRef<any>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const loadTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    // Garantir que o DOM esteja pronto antes de carregar o SDK
    const initializeSDK = () => {
      // Carregar o SDK da Pluggy
      console.log('[Pluggy] Iniciando carregamento do SDK...');
      
      // Verificar se o script já foi carregado
      const existingScript = document.querySelector('script[src="https://cdn.pluggy.ai/pluggy-connect.js"]');
      if (existingScript) {
        console.log('[Pluggy] SDK já carregado');
        if (window.PluggyConnect) {
          setSdkLoaded(true);
          return;
        }
      }
      
      // Timeout de segurança - 10 segundos para carregar o SDK
      loadTimeoutRef.current = setTimeout(() => {
        if (!sdkLoaded) {
          console.error('[Pluggy] Timeout ao carregar SDK');
          toast.error('Timeout ao carregar Pluggy SDK. Tente novamente.');
          onError(new Error('Timeout loading Pluggy SDK'));
        }
      }, 10000);
      
      const script = document.createElement('script');
      script.src = 'https://cdn.pluggy.ai/pluggy-connect.js';
      script.async = true;
      script.onload = () => {
        console.log('[Pluggy] SDK carregado com sucesso');
        if (loadTimeoutRef.current) {
          clearTimeout(loadTimeoutRef.current);
        }
        setSdkLoaded(true);
      };
      script.onerror = (error) => {
        console.error('[Pluggy] Erro ao carregar SDK:', error);
        if (loadTimeoutRef.current) {
          clearTimeout(loadTimeoutRef.current);
        }
        toast.error('Erro ao carregar Pluggy SDK. Verifique sua conexão.');
        onError(new Error('Failed to load Pluggy SDK'));
      };
      
      document.body.appendChild(script);
    };

    // Aguardar o DOM estar completamente carregado
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', initializeSDK);
    } else {
      initializeSDK();
    }

    return () => {
      // Cleanup timeout
      if (loadTimeoutRef.current) {
        clearTimeout(loadTimeoutRef.current);
      }
      
      // Cleanup event listener
      document.removeEventListener('DOMContentLoaded', initializeSDK);
      
      // Cleanup script
      const existingScript = document.querySelector('script[src="https://cdn.pluggy.ai/pluggy-connect.js"]');
      if (existingScript && existingScript.parentNode) {
        existingScript.parentNode.removeChild(existingScript);
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
          console.error('[Pluggy] Erro no cleanup:', e);
        }
      }
    };
  }, [onError, sdkLoaded]);

  useEffect(() => {
    if (!sdkLoaded || !connectToken || !window.PluggyConnect || !containerRef.current) {
      console.log('[Pluggy] Aguardando condições:', { 
        sdkLoaded, 
        hasToken: !!connectToken, 
        hasPluggyConnect: !!window.PluggyConnect,
        hasContainer: !!containerRef.current 
      });
      return;
    }

    console.log('[Pluggy] Todas as condições atendidas, inicializando widget...');
    
    // Função wrapper para garantir que onClose sempre existe
    const handleClose = () => {
      console.log('[Pluggy] Fechando widget...');
      
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
    
    // Função async para inicializar o widget
    const initializeWidget = async () => {
      try {
        // Aguardar um momento para garantir que o container esteja no DOM
        await new Promise(resolve => setTimeout(resolve, 100));
        
        // Verificar novamente se o container existe
        if (!containerRef.current) {
          throw new Error('Container não encontrado no DOM');
        }
        
        // Configuração do Pluggy Connect
        console.log('[Pluggy] Criando configuração do widget...');
        const config = {
          connectToken: connectToken,
          includeSandbox: true,
          ...(updateItem && { updateItem }),
          
          // Especificar onde renderizar o widget
          target: containerRef.current,
          containerId: 'pluggy-connect-container',
          
          onSuccess: (data: any) => {
            console.log('[Pluggy] Success callback:', data);
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
              toast.error('Erro: ID da conexão não encontrado');
              onError(new Error('No itemId received'));
            }
            
            handleClose();
          },
          
          onError: (error: any) => {
            console.log('[Pluggy] Error callback:', error);
            const errorMessage = error?.message || error?.error || 'Erro ao conectar com o banco';
            toast.error(errorMessage);
            onError(new Error(errorMessage));
            handleClose();
          },
          
          onExit: handleClose,
          onClose: handleClose,
          
          props: {
            onClose: handleClose
          },
          
          // Eventos para debug
          onEvent: (event: string, metadata: any) => {
            console.log('[Pluggy] Event:', event, metadata);
            // Detectar eventos de fechamento
            if (event === 'CLOSE' || event === 'EXIT' || event === 'CANCEL') {
              handleClose();
            }
          }
        };

        console.log('[Pluggy] Configuração criada:', config);
        
        // Criar instância do Pluggy Connect
        console.log('[Pluggy] Criando instância do PluggyConnect...');
        console.log('[Pluggy] window.PluggyConnect:', window.PluggyConnect);
        
        // Verificar se PluggyConnect está disponível
        if (typeof window.PluggyConnect !== 'function') {
          throw new Error('PluggyConnect não é uma função. Tipo: ' + typeof window.PluggyConnect);
        }
        
        pluggyInstance.current = new window.PluggyConnect(config);
        console.log('[Pluggy] Instância criada:', pluggyInstance.current);
        
        // Abrir o widget
        if (pluggyInstance.current.init && typeof pluggyInstance.current.init === 'function') {
          console.log('[Pluggy] Chamando init()...');
          pluggyInstance.current.init();
        } else if (pluggyInstance.current.open && typeof pluggyInstance.current.open === 'function') {
          console.log('[Pluggy] Chamando open()...');
          pluggyInstance.current.open();
        } else {
          console.error('[Pluggy] Nenhum método de abertura encontrado:', pluggyInstance.current);
          throw new Error('Pluggy widget não possui método init() ou open()');
        }
        
        // Fallback: se o widget não fechar sozinho após alguns segundos sem atividade
        const inactivityTimer = setTimeout(() => {
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
        console.error('[Pluggy] Erro ao inicializar widget:', error);
        toast.error('Erro ao inicializar conexão bancária: ' + (error.message || 'Erro desconhecido'));
        onError(error);
      }
    };
    
    // Chamar a função de inicialização
    initializeWidget();
    
  }, [sdkLoaded, connectToken, onSuccess, onError, onClose, updateItem]);

  // Container para o widget - garantir que seja renderizado mas invisível
  return (
    <div 
      ref={containerRef} 
      id="pluggy-connect-container"
      style={{ 
        position: 'fixed',
        top: 0,
        left: 0,
        width: '100%',
        height: '100%',
        zIndex: 9999,
        pointerEvents: 'none'
      }} 
    />
  );
}

// Componente alternativo que cria um overlay customizado
export function PluggyConnectModal({
  connectToken,
  onSuccess,
  onError,
  onClose,
  updateItem
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
            updateItem={updateItem}
          />
        </div>
      </div>
    </>
  );
}