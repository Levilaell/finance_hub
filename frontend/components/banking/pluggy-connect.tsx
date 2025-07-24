'use client';

import { useEffect, useRef, useState } from 'react';
import { toast } from 'sonner';
import { LoadingSpinner } from '@/components/ui/loading-spinner';

interface PluggyConnectProps {
  connectToken: string;
  updateItem?: string;
  onSuccess: (itemData: any) => void;
  onError: (error: any) => void;
  onClose: () => void;
}

declare global {
  interface Window {
    PluggyConnect: any;
  }
}

export function PluggyConnect({
  connectToken,
  updateItem,
  onSuccess,
  onError,
  onClose
}: PluggyConnectProps) {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const widgetRef = useRef<any>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    let mounted = true;
    let script: HTMLScriptElement | null = null;

    const cleanup = () => {
      // Destruir widget
      if (widgetRef.current?.destroy) {
        try {
          widgetRef.current.destroy();
        } catch (e) {
          console.error('[PluggyConnect] Erro ao destruir widget:', e);
        }
      }
      widgetRef.current = null;

      // Remover elementos do DOM
      const elements = document.querySelectorAll(
        'iframe[src*="pluggy"], [class*="pluggy"], .zoid-overlay, .zoid-container'
      );
      elements.forEach(el => el.remove());

      // Restaurar scroll
      document.body.style.overflow = '';
      document.documentElement.style.overflow = '';

      // Remover script
      if (script?.parentNode) {
        script.parentNode.removeChild(script);
      }
    };

    const loadPluggy = async () => {
      try {
        // Verificar se SDK já está carregado
        if (window.PluggyConnect) {
          console.log('[PluggyConnect] SDK já carregado');
          initializeWidget();
          return;
        }

        // Carregar SDK
        console.log('[PluggyConnect] Carregando SDK...');
        script = document.createElement('script');
        script.src = 'https://cdn.pluggy.ai/pluggy-connect.js';
        script.async = true;

        script.onload = () => {
          console.log('[PluggyConnect] SDK carregado');
          if (mounted) {
            initializeWidget();
          }
        };

        script.onerror = () => {
          console.error('[PluggyConnect] Erro ao carregar SDK');
          if (mounted) {
            setError('Erro ao carregar Pluggy SDK');
            setLoading(false);
          }
        };

        document.body.appendChild(script);
      } catch (err) {
        console.error('[PluggyConnect] Erro:', err);
        if (mounted) {
          setError('Erro ao inicializar conexão');
          setLoading(false);
        }
      }
    };

    const initializeWidget = () => {
      if (!window.PluggyConnect || !mounted) return;

      try {
        console.log('[PluggyConnect] Inicializando widget...');
        
        const config = {
          connectToken,
          includeSandbox: true,
          ...(updateItem && { updateItem }),
          
          onSuccess: (data: any) => {
            console.log('[PluggyConnect] Success:', data);
            if (!mounted) return;
            
            cleanup();
            onSuccess(data);
          },
          
          onError: (err: any) => {
            console.log('[PluggyConnect] Error:', err);
            if (!mounted) return;
            
            cleanup();
            onError(err);
          },
          
          onClose: () => {
            console.log('[PluggyConnect] Close');
            if (!mounted) return;
            
            cleanup();
            onClose();
          },
          
          onEvent: (event: string, metadata: any) => {
            console.log('[PluggyConnect] Event:', event, metadata);
            
            // Eventos informativos
            if (event === 'LOGIN_SUCCESS') {
              toast.success('Login realizado! Buscando informações...');
            } else if (event === 'ITEM_RESPONSE' && metadata?.item?.status) {
              const status = metadata.item.status;
              if (status === 'PARTIAL_SUCCESS') {
                console.log('[PluggyConnect] Partial success - expected for MFA banks');
              }
            }
          }
        };

        widgetRef.current = new window.PluggyConnect(config);
        
        // Inicializar widget
        if (widgetRef.current.init) {
          widgetRef.current.init();
        } else if (widgetRef.current.open) {
          widgetRef.current.open();
        }
        
        setLoading(false);
      } catch (err) {
        console.error('[PluggyConnect] Erro ao criar widget:', err);
        setError('Erro ao criar widget');
        setLoading(false);
      }
    };

    // Timeout para carregamento
    const timeout = setTimeout(() => {
      if (loading && mounted) {
        setError('Timeout ao carregar Pluggy');
        setLoading(false);
      }
    }, 15000);

    loadPluggy();

    return () => {
      mounted = false;
      clearTimeout(timeout);
      cleanup();
    };
  }, [connectToken, updateItem, onSuccess, onError, onClose]);

  return (
    <>
      {/* Overlay */}
      <div 
        className="fixed inset-0 bg-black/50 z-[9998]"
        onClick={onClose}
      />
      
      {/* Container */}
      <div 
        ref={containerRef}
        className="fixed inset-0 z-[9999] flex items-center justify-center pointer-events-none"
      >
        <div className="pointer-events-auto relative">
          {/* Botão fechar */}
          <button
            onClick={onClose}
            className="absolute -top-10 right-0 text-white hover:text-gray-300 text-2xl font-bold z-[10000]"
            aria-label="Fechar"
          >
            ✕
          </button>
          
          {/* Loading state */}
          {loading && (
            <div className="bg-white rounded-lg p-8 shadow-xl">
              <div className="flex flex-col items-center space-y-4">
                <LoadingSpinner />
                <p className="text-gray-600">Carregando conexão segura...</p>
              </div>
            </div>
          )}
          
          {/* Error state */}
          {error && (
            <div className="bg-white rounded-lg p-8 shadow-xl max-w-md">
              <h3 className="text-lg font-semibold text-red-600 mb-2">
                Erro ao conectar
              </h3>
              <p className="text-gray-700 mb-4">{error}</p>
              <button
                onClick={onClose}
                className="w-full px-4 py-2 bg-gray-900 text-white rounded-md hover:bg-gray-800"
              >
                Fechar
              </button>
            </div>
          )}
        </div>
      </div>
    </>
  );
}