'use client';

import { useEffect, useState } from 'react';
import { toast } from 'sonner';
import { XMarkIcon } from '@heroicons/react/24/outline';

interface PluggyConnectIframeProps {
  connectToken: string;
  onSuccess: (itemData: any) => void;
  onError: (error: any) => void;
  onClose: () => void;
  updateItem?: string;
}

export function PluggyConnectIframe({
  connectToken,
  onSuccess,
  onError,
  onClose,
  updateItem
}: PluggyConnectIframeProps) {
  const [iframeUrl, setIframeUrl] = useState<string>('');

  useEffect(() => {
    if (!connectToken) return;

    // Construir URL do iframe da Pluggy
    const baseUrl = 'https://connect.pluggy.ai';
    const params = new URLSearchParams({
      connectToken: connectToken,
    });
    
    if (updateItem) {
      params.append('updateItem', updateItem);
    }
    
    const url = `${baseUrl}?${params.toString()}`;
    console.log('[Pluggy Iframe] URL criada:', url);
    setIframeUrl(url);

    // Listener para mensagens do iframe
    const handleMessage = (event: MessageEvent) => {
      // Verificar origem da mensagem
      if (!event.origin.includes('pluggy.ai')) {
        return;
      }

      console.log('[Pluggy Iframe] Mensagem recebida:', event.data);

      // Processar mensagens do Pluggy
      if (event.data.type === 'PLUGGY_CONNECT:SUCCESS') {
        const itemId = event.data.payload?.itemId || event.data.payload?.item?.id;
        if (itemId) {
          toast.success('Conta conectada com sucesso!');
          onSuccess({ item: { id: itemId } });
        } else {
          onError(new Error('ID da conexão não encontrado'));
        }
      } else if (event.data.type === 'PLUGGY_CONNECT:ERROR') {
        const error = event.data.payload?.error || 'Erro desconhecido';
        toast.error(`Erro: ${error}`);
        onError(new Error(error));
      } else if (event.data.type === 'PLUGGY_CONNECT:EXIT' || event.data.type === 'PLUGGY_CONNECT:CLOSE') {
        onClose();
      }
    };

    window.addEventListener('message', handleMessage);

    return () => {
      window.removeEventListener('message', handleMessage);
    };
  }, [connectToken, onSuccess, onError, onClose]);

  if (!iframeUrl) {
    return null;
  }

  return (
    <div className="fixed inset-0 z-[9999] bg-black/50">
      <div className="fixed inset-4 md:inset-8 lg:inset-16 bg-white rounded-lg shadow-2xl flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b">
          <h2 className="text-lg font-semibold">Conectar Conta Bancária</h2>
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
            aria-label="Fechar"
          >
            <XMarkIcon className="h-5 w-5" />
          </button>
        </div>

        {/* Iframe */}
        <div className="flex-1 p-4">
          <iframe
            src={iframeUrl}
            className="w-full h-full rounded-lg border"
            title="Pluggy Connect"
            allow="camera; microphone"
            sandbox="allow-scripts allow-same-origin allow-forms allow-popups allow-popups-to-escape-sandbox"
          />
        </div>

        {/* Footer */}
        <div className="p-4 border-t text-center text-sm text-gray-600">
          Conexão segura via Open Banking
        </div>
      </div>
    </div>
  );
}