'use client';

import { useEffect, useRef } from 'react';
import { toast } from 'sonner';

interface PluggyConnectWidgetProps {
  connectToken: string;
  onSuccess: (itemData: any) => void;
  onError: (error: any) => void;
  onClose?: () => void;
}

export function PluggyConnectWidget({
  connectToken,
  onSuccess,
  onError,
  onClose
}: PluggyConnectWidgetProps) {
  const windowRef = useRef<Window | null>(null);
  const intervalRef = useRef<NodeJS.Timeout | null>(null);
  const messageHandlerRef = useRef<((event: MessageEvent) => void) | null>(null);

  useEffect(() => {
    if (!connectToken) {
      console.error('No connect token provided');
      return;
    }

    // URL da Pluggy Connect com o token
    const pluggyConnectUrl = `https://connect.pluggy.ai?connectToken=${encodeURIComponent(connectToken)}`;
    
    console.log('🔗 Opening Pluggy Connect with URL:', pluggyConnectUrl);
    
    // Configurações da janela
    const windowFeatures = 'width=500,height=700,left=200,top=100,toolbar=no,location=no,directories=no,status=no,menubar=no,scrollbars=yes,resizable=yes';
    
    // Abrir janela
    windowRef.current = window.open(pluggyConnectUrl, 'pluggy-connect', windowFeatures);
    
    if (!windowRef.current) {
      toast.error('Por favor, permita pop-ups para conectar sua conta bancária');
      onError(new Error('Pop-up bloqueado'));
      return;
    }
    
    console.log('✅ Pluggy Connect window opened successfully');

    // Handler para mensagens da Pluggy
    messageHandlerRef.current = (event: MessageEvent) => {
      // Verificar origem
      if (event.origin !== 'https://connect.pluggy.ai') {
        return;
      }

      console.log('📬 Received message from Pluggy:', event.data);

      const data = event.data;
      
      // Diferentes formatos de resposta da Pluggy
      
      // Formato 1: Mensagem de sucesso com item
      if (data.success === true && data.item) {
        console.log('✅ Pluggy Connect success (format 1):', data);
        onSuccess({ item: data.item });
        closeWindow();
        return;
      }
      
      // Formato 2: Evento com tipo
      if (data.type) {
        switch (data.type) {
          case 'success':
          case 'PLUGGY_SUCCESS':
          case 'ITEM_CREATED':
            console.log('✅ Pluggy Connect success (format 2):', data);
            const itemId = data.itemId || data.item?.id || data.data?.itemId;
            if (itemId) {
              onSuccess({ item: { id: itemId } });
              closeWindow();
            }
            break;
            
          case 'error':
          case 'PLUGGY_ERROR':
            console.error('❌ Pluggy Connect error:', data);
            onError(new Error(data.message || data.error || 'Erro na conexão'));
            closeWindow();
            break;
            
          case 'close':
          case 'PLUGGY_CLOSE':
          case 'exit':
            console.log('🔒 Pluggy Connect closed by user');
            if (onClose) {
              onClose();
            }
            closeWindow();
            break;
        }
      }
      
      // Formato 3: Ação direta
      if (data.action) {
        switch (data.action) {
          case 'on-success':
            console.log('✅ Pluggy Connect success (format 3):', data);
            if (data.item) {
              onSuccess({ item: data.item });
              closeWindow();
            }
            break;
            
          case 'on-error':
            console.error('❌ Pluggy Connect error:', data);
            onError(new Error(data.error?.message || 'Erro na conexão'));
            closeWindow();
            break;
            
          case 'on-exit':
            console.log('🔒 Pluggy Connect exited');
            if (onClose) {
              onClose();
            }
            closeWindow();
            break;
        }
      }
      
      // Formato 4: itemId direto (para retrocompatibilidade)
      if (data.itemId && !data.type && !data.action) {
        console.log('✅ Pluggy Connect success (format 4):', data);
        onSuccess({ item: { id: data.itemId } });
        closeWindow();
      }
    };
    
    // Função para fechar a janela
    const closeWindow = () => {
      if (windowRef.current && !windowRef.current.closed) {
        windowRef.current.close();
      }
      windowRef.current = null;
      
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
    };

    // Adicionar listener de mensagens
    window.addEventListener('message', messageHandlerRef.current);

    // Verificar periodicamente se a janela foi fechada
    intervalRef.current = setInterval(() => {
      if (windowRef.current && windowRef.current.closed) {
        console.log('🔒 Pluggy Connect window was closed manually');
        if (intervalRef.current) {
          clearInterval(intervalRef.current);
          intervalRef.current = null;
        }
        if (onClose) {
          onClose();
        }
      }
    }, 1000);

    // Cleanup
    return () => {
      if (messageHandlerRef.current) {
        window.removeEventListener('message', messageHandlerRef.current);
        messageHandlerRef.current = null;
      }
      
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
      
      if (windowRef.current && !windowRef.current.closed) {
        windowRef.current.close();
        windowRef.current = null;
      }
    };
  }, [connectToken, onSuccess, onError, onClose]);

  // Este componente não renderiza nada
  return null;
}

// Componente alternativo usando iframe embutido
export function PluggyConnectEmbed({
  connectToken,
  onSuccess,
  onError,
  onClose
}: PluggyConnectWidgetProps) {
  const iframeRef = useRef<HTMLIFrameElement>(null);

  useEffect(() => {
    if (!connectToken) return;

    const handleMessage = (event: MessageEvent) => {
      if (event.origin !== 'https://connect.pluggy.ai') {
        return;
      }

      console.log('📬 Iframe message from Pluggy:', event.data);

      const data = event.data;
      
      // Processar resposta similar ao componente principal
      if (data.success === true && data.item) {
        onSuccess({ item: data.item });
      } else if (data.type === 'success' || data.action === 'on-success') {
        const itemId = data.itemId || data.item?.id;
        if (itemId) {
          onSuccess({ item: { id: itemId } });
        }
      } else if (data.type === 'error' || data.action === 'on-error') {
        onError(new Error(data.message || data.error?.message || 'Erro na conexão'));
      } else if (data.type === 'close' || data.action === 'on-exit') {
        if (onClose) {
          onClose();
        }
      }
    };

    window.addEventListener('message', handleMessage);

    return () => {
      window.removeEventListener('message', handleMessage);
    };
  }, [connectToken, onSuccess, onError, onClose]);

  return (
    <div 
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        backgroundColor: 'rgba(0, 0, 0, 0.5)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        zIndex: 9999
      }}
      onClick={onClose}
    >
      <div 
        style={{
          width: '500px',
          height: '700px',
          backgroundColor: 'white',
          borderRadius: '8px',
          overflow: 'hidden',
          position: 'relative',
          boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)'
        }}
        onClick={(e) => e.stopPropagation()}
      >
        <button
          onClick={onClose}
          style={{
            position: 'absolute',
            top: '10px',
            right: '10px',
            background: 'white',
            border: '1px solid #e0e0e0',
            borderRadius: '50%',
            width: '32px',
            height: '32px',
            fontSize: '20px',
            cursor: 'pointer',
            zIndex: 1,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            boxShadow: '0 2px 4px rgba(0, 0, 0, 0.1)'
          }}
        >
          ×
        </button>
        <iframe
          ref={iframeRef}
          src={`https://connect.pluggy.ai?connectToken=${encodeURIComponent(connectToken)}`}
          style={{
            width: '100%',
            height: '100%',
            border: 'none'
          }}
          title="Pluggy Connect"
          allow="clipboard-read; clipboard-write"
        />
      </div>
    </div>
  );
}