'use client';

import { useEffect, useState } from 'react';
import { belvoService } from '@/services/belvo.service';
import { toast } from 'sonner';

declare global {
  interface Window {
    belvoSDK: any;
  }
}

interface BelvoConnectProps {
  isOpen: boolean;
  onSuccess: (linkId: string) => void;
  onExit: () => void;
  onError: (error: string) => void;
}

export function BelvoConnect({ isOpen, onSuccess, onExit, onError }: BelvoConnectProps) {
  const [widgetReady, setWidgetReady] = useState(false);

  useEffect(() => {
    if (!isOpen) return;

    // Load Belvo SDK
    const script = document.createElement('script');
    script.src = 'https://cdn.belvo.io/belvo-widget-1-stable.js';
    script.async = true;
    script.onload = () => {
      setWidgetReady(true);
    };
    document.body.appendChild(script);

    return () => {
      document.body.removeChild(script);
    };
  }, [isOpen]);

  useEffect(() => {
    if (!widgetReady || !isOpen) return;

    const initializeBelvoWidget = async () => {
      try {
        // Get widget token from backend
        const { access_token } = await belvoService.createWidgetToken();

        // Initialize Belvo widget
        window.belvoSDK.createWidget(access_token, {
          locale: 'pt',
          country_codes: ['BR'],
          callback: (link: string, institution: string) => {
            console.log('Belvo success:', { link, institution });
            onSuccess(link);
          },
          onExit: (data: any) => {
            console.log('Belvo exit:', data);
            onExit();
          },
          onError: (error: any) => {
            console.error('Belvo error:', error);
            onError(error.message || 'Erro ao conectar com o banco');
          },
          onEvent: (data: any) => {
            console.log('Belvo event:', data);
          }
        }).build();

      } catch (error: any) {
        console.error('Error initializing Belvo widget:', error);
        toast.error('Erro ao inicializar conexão bancária');
        onError(error.message);
      }
    };

    initializeBelvoWidget();
  }, [widgetReady, isOpen, onSuccess, onExit, onError]);

  return null;
}