'use client';

import { useEffect, useRef, useState } from 'react';
import { PluggyConnect } from 'pluggy-connect-sdk';
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
  const pluggyConnectRef = useRef<any>(null);
  const [isInitialized, setIsInitialized] = useState(false);
  const initializationTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    if (!connectToken) {
      console.error('No connect token provided');
      return;
    }

    // Delay initialization to avoid React StrictMode double-mounting issues
    initializationTimeoutRef.current = setTimeout(() => {
      console.log('🔌 Initializing Pluggy Connect with token:', connectToken.substring(0, 50) + '...');

      try {
        // Create Pluggy Connect instance
        const pluggyConnect = new PluggyConnect({
          connectToken,
          includeSandbox: true, // Enable sandbox for development
          updateMode: false,
          connectorTypes: ['PERSONAL_BANK'],
          countries: ['BR'],
          
          onSuccess: (itemData: any) => {
            console.log('✅ Pluggy Connect success:', itemData);
            onSuccess(itemData);
            setIsInitialized(false);
          },
          
          onError: (error: any) => {
            console.error('❌ Pluggy Connect error:', error);
            onError(error);
            setIsInitialized(false);
          },
          
          onOpen: () => {
            console.log('🔓 Pluggy Connect opened');
          },
          
          onClose: () => {
            console.log('🔒 Pluggy Connect closed');
            if (onClose) {
              onClose();
            }
            setIsInitialized(false);
          },
          
          onEvent: (event: string, metadata: any) => {
            console.log('📊 Pluggy Connect event:', event, metadata);
            
            // Track important events
            switch (event) {
              case 'SELECTED_INSTITUTION':
                console.log('🏦 Selected institution:', metadata.connector);
                break;
              case 'SUBMITTED_CREDENTIALS':
                console.log('🔑 Credentials submitted');
                toast.info('Verificando credenciais...');
                break;
              case 'AUTHENTICATED':
                console.log('✅ Authentication successful');
                toast.success('Autenticação bem-sucedida!');
                break;
              case 'AUTHENTICATION_FAILED':
                console.log('❌ Authentication failed');
                toast.error('Falha na autenticação');
                break;
            }
          }
        });

        // Store reference
        pluggyConnectRef.current = pluggyConnect;

        // Initialize the widget
        pluggyConnect.init()
          .then(() => {
            console.log('✅ Pluggy Connect initialized successfully');
            setIsInitialized(true);
          })
          .catch((error: any) => {
            console.error('❌ Failed to initialize Pluggy Connect:', error);
            onError(error);
          });

      } catch (error: any) {
        console.error('❌ Error creating Pluggy Connect instance:', error);
        onError(error);
      }
    }, 100); // Small delay to avoid StrictMode issues

    // Cleanup
    return () => {
      if (initializationTimeoutRef.current) {
        clearTimeout(initializationTimeoutRef.current);
      }
      
      if (pluggyConnectRef.current && isInitialized) {
        console.log('🧹 Destroying Pluggy Connect instance');
        try {
          pluggyConnectRef.current.destroy();
        } catch (err: any) {
          // Ignore errors during cleanup
          console.log('Cleanup error (ignored):', err.message);
        }
        pluggyConnectRef.current = null;
      }
    };
  }, [connectToken]); // Remove dependencies to prevent re-initialization

  // This component doesn't render anything visible
  // The Pluggy Connect SDK creates its own modal
  return null;
}