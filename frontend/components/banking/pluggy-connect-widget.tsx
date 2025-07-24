'use client';

import { useEffect, useRef, useState } from 'react';
import { toast } from 'sonner';

interface PluggyConnectWidgetProps {
  connectToken: string;
  onSuccess: (itemData: any) => void;
  onError: (error: any) => void;
  onClose?: () => void;
  updateItem?: string;
}

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
  const loadTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const hasClosedRef = useRef(false); // Prevenir múltiplos fechamentos

  useEffect(() => {
    const initializeSDK = () => {
      console.log('[Pluggy] Iniciando carregamento do SDK...');
      
      const existingScript = document.querySelector('script[src="https://cdn.pluggy.ai/pluggy-connect.js"]');
      if (existingScript) {
        console.log('[Pluggy] SDK já carregado');
        if (window.PluggyConnect) {
          setSdkLoaded(true);
          return;
        }
      }
      
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

    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', initializeSDK);
    } else {
      initializeSDK();
    }

    return () => {
      if (loadTimeoutRef.current) {
        clearTimeout(loadTimeoutRef.current);
      }
      
      document.removeEventListener('DOMContentLoaded', initializeSDK);
      
      const existingScript = document.querySelector('script[src="https://cdn.pluggy.ai/pluggy-connect.js"]');
      if (existingScript && existingScript.parentNode) {
        existingScript.parentNode.removeChild(existingScript);
      }
      
      if (pluggyInstance.current) {
        try {
          if (typeof pluggyInstance.current.destroy === 'function') {
            pluggyInstance.current.destroy();
          }
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
    if (!sdkLoaded || !connectToken || !window.PluggyConnect) {
      console.log('[Pluggy] Aguardando condições:', { 
        sdkLoaded, 
        hasToken: !!connectToken, 
        hasPluggyConnect: !!window.PluggyConnect
      });
      return;
    }

    console.log('[Pluggy] Todas as condições atendidas, inicializando widget...');
    
    // Reset do flag de fechamento
    hasClosedRef.current = false;
    
    const handleClose = () => {
      // Prevenir múltiplas chamadas
      if (hasClosedRef.current) {
        console.log('[Pluggy] Widget já fechado, ignorando...');
        return;
      }
      
      hasClosedRef.current = true;
      console.log('[Pluggy] Fechando widget...');
      
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
    
    const initializeWidget = async () => {
      try {
        await new Promise(resolve => setTimeout(resolve, 100));
        
        console.log('[Pluggy] Criando configuração do widget...');
        const config = {
          connectToken: connectToken,
          includeSandbox: true,
          ...(updateItem && { updateItem }),
          
          onSuccess: (data: any) => {
            console.log('[Pluggy] Success callback - Full data:', JSON.stringify(data, null, 2));
            
            const itemId = data?.item?.id || data?.itemId || data?.id;
            
            if (itemId) {
              if (updateItem) {
                toast.success('Conta reconectada com sucesso! Sincronizando transações...');
              } else {
                toast.success('Conta conectada com sucesso!');
              }
              
              onSuccess({ 
                item: { 
                  id: itemId,
                  status: data?.item?.status,
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
            
            // Tratamento especial para erro de sincronização
            if (error?.message === 'Item was not sync successfully') {
              // Este erro ocorre quando o item requer ação do usuário
              // mas ainda assim foi atualizado parcialmente
              console.warn('[Pluggy] Item sync warning:', error);
              
              // Verificar se há dados do item mesmo com erro
              const itemData = error?.data?.item || error?.item;
              if (itemData && itemData.id) {
                console.log('[Pluggy] Item data found despite error:', itemData);
                
                // Se é uma atualização e temos o item, considerar como sucesso parcial
                if (updateItem && itemData.id === updateItem) {
                  toast.warning('Conta reconectada com limitações. Alguns dados podem estar indisponíveis.');
                  onSuccess({ 
                    item: itemData,
                    partial: true,
                    warning: 'Sincronização parcial'
                  });
                  handleClose();
                  return;
                }
              }
            }
            
            const errorMessage = error?.message || error?.error || 'Erro ao conectar com o banco';
            toast.error(errorMessage);
            onError(new Error(errorMessage));
            handleClose();
          },
          
          onExit: () => {
            console.log('[Pluggy] onExit called');
            handleClose();
          },
          
          onClose: () => {
            console.log('[Pluggy] onClose called');
            handleClose();
          },
          
          onEvent: (event: string, metadata: any) => {
            console.log('[Pluggy] Event:', event, metadata);
            
            if (event === 'ITEM_RESPONSE' && metadata) {
              console.log('[Pluggy] Item Response Details:', {
                event,
                metadata,
                item: metadata.item,
                status: metadata.item?.status || metadata.status,
                error: metadata.error,
                timestamp: new Date().toISOString()
              });
              
              const itemStatus = metadata.item?.status || metadata.status;
              if (itemStatus) {
                console.log(`[Pluggy] 📊 Status do Item: ${itemStatus}`);
                
                switch(itemStatus) {
                  case 'WAITING_USER_ACTION':
                    console.warn('[Pluggy] ⚠️ Item requer ação do usuário!');
                    break;
                  case 'LOGIN_ERROR':
                    console.error('[Pluggy] ❌ Erro de login no item!');
                    break;
                  case 'OUTDATED':
                    console.warn('[Pluggy] ⚠️ Item está desatualizado!');
                    break;
                  case 'UPDATED':
                  case 'SUCCESS':
                    console.log('[Pluggy] ✅ Item atualizado com sucesso!');
                    break;
                  case 'PARTIAL_SUCCESS':
                    console.log('[Pluggy] ⚠️ Item atualizado parcialmente!');
                    break;
                }
              }
            }
            
            // Eventos de progresso
            if (event === 'LOGIN_SUCCESS') {
              console.log('[Pluggy] ✅ Login realizado com sucesso!');
              toast.success('Login realizado! Buscando suas informações...');
            } else if (event === 'LOGIN_STEP_COMPLETED') {
              console.log('[Pluggy] ✅ Etapa de login concluída!');
            }
            
            // Detectar eventos de fechamento
            if (event === 'CLOSE' || event === 'EXIT' || event === 'CANCEL') {
              handleClose();
            }
          }
        };

        console.log('[Pluggy] Configuração criada:', config);
        
        if (typeof window.PluggyConnect !== 'function') {
          throw new Error('PluggyConnect não é uma função. Tipo: ' + typeof window.PluggyConnect);
        }
        
        pluggyInstance.current = new window.PluggyConnect(config);
        console.log('[Pluggy] Instância criada:', pluggyInstance.current);
        
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
        
      } catch (error: any) {
        console.error('[Pluggy] Erro ao inicializar widget:', error);
        toast.error('Erro ao inicializar conexão bancária: ' + (error.message || 'Erro desconhecido'));
        onError(error);
      }
    };
    
    initializeWidget();
    
  }, [sdkLoaded, connectToken, onSuccess, onError, onClose, updateItem]);

  return null;
}

export function PluggyConnectModal({
  connectToken,
  onSuccess,
  onError,
  onClose,
  updateItem
}: PluggyConnectWidgetProps) {
  const [isOpen, setIsOpen] = useState(true);
  const hasHandledRef = useRef(false); // Prevenir múltiplas chamadas
  
  const handleClose = () => {
    if (hasHandledRef.current) return;
    hasHandledRef.current = true;
    
    setIsOpen(false);
    if (onClose) {
      onClose();
    }
  };

  const handleSuccess = (data: any) => {
    if (hasHandledRef.current) return;
    hasHandledRef.current = true;
    
    onSuccess(data);
    setIsOpen(false);
  };

  const handleError = (error: any) => {
    if (hasHandledRef.current) return;
    hasHandledRef.current = true;
    
    onError(error);
    setIsOpen(false);
  };

  if (!isOpen) return null;

  return (
    <>
      <div 
        className="fixed inset-0 bg-black/50 z-[9998]"
        onClick={handleClose}
      />
      
      <div className="fixed inset-0 z-[9999] flex items-center justify-center pointer-events-none">
        <div className="pointer-events-auto relative">
          <button
            onClick={handleClose}
            className="absolute -top-10 right-0 text-white hover:text-gray-300 text-2xl font-bold z-[10000]"
            aria-label="Fechar"
          >
            ✕
          </button>
          
          <PluggyConnectWidget
            connectToken={connectToken}
            onSuccess={handleSuccess}
            onError={handleError}
            onClose={handleClose}
            updateItem={updateItem}
          />
        </div>
      </div>
    </>
  );
}