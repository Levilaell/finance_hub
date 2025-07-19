'use client';

import { useEffect, useRef, useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { toast } from 'sonner';

export default function PluggyConnectPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const connectRef = useRef<HTMLDivElement>(null);
  const sdkLoadedRef = useRef(false);

  useEffect(() => {
    const connectToken = searchParams.get('connectToken');
    const returnUrl = searchParams.get('returnUrl') || '/accounts';

    if (!connectToken) {
      setError('Token de conexão não encontrado');
      setTimeout(() => router.push('/accounts'), 3000);
      return;
    }


    const loadPluggySDK = () => {
      return new Promise<void>((resolve, reject) => {
        // Check if already loaded
        if ((window as any).PluggyConnect) {
          resolve();
          return;
        }

        if (sdkLoadedRef.current) {
          // Already loading
          return;
        }

        sdkLoadedRef.current = true;

        // Try multiple SDK URLs
        const sdkUrls = [
          'https://connect.pluggy.ai/js/pluggy-connect.js',
          'https://cdn.pluggy.ai/widget/v2/pluggy-connect.js',
          'https://unpkg.com/@pluggyai/pluggy-connect@latest/dist/pluggy-connect.min.js'
        ];

        let currentUrlIndex = 0;

        const tryLoadSDK = (urlIndex: number) => {
          if (urlIndex >= sdkUrls.length) {
            reject(new Error('Nenhuma URL do SDK funcionou'));
            return;
          }

          const script = document.createElement('script');
          script.src = sdkUrls[urlIndex];
          script.async = true;


          script.onload = () => {
            if ((window as any).PluggyConnect) {
              resolve();
            } else {
              tryLoadSDK(urlIndex + 1);
            }
          };

          script.onerror = (error) => {
            tryLoadSDK(urlIndex + 1);
          };

          document.head.appendChild(script);
        };

        tryLoadSDK(0);
      });
    };

    const initializePluggyConnect = async () => {
      try {
        setIsLoading(true);
        
        // Try to load the real SDK first
        try {
          await loadPluggySDK();
          await initializeRealPluggyConnect();
        } catch (sdkError) {
          await initializeMockPluggyConnect();
        }
        
      } catch (error: any) {
        setError(error.message);
        
        // Redirect back with error after 3 seconds
        setTimeout(() => {
          const callbackUrl = new URL(returnUrl, window.location.origin);
          callbackUrl.searchParams.set('error', error.message);
          callbackUrl.searchParams.set('status', 'error');
          window.location.href = callbackUrl.toString();
        }, 3000);
      }
    };

    const initializeRealPluggyConnect = async () => {
      
      if (!connectRef.current) {
        throw new Error('Container não encontrado');
      }

      const PluggyConnect = (window as any).PluggyConnect;
      
      const connect = new PluggyConnect({
        connectToken: connectToken,
        includeSandbox: true,
        connectorTypes: ['PERSONAL_BANK'],
        countries: ['BR'],
      });

      connect.init('pluggy-connect-container');

      // Handle success
      connect.onSuccess((itemData: any) => {
        const itemId = itemData?.item?.id;
        
        if (itemId) {
          // Redirect back with success
          const callbackUrl = new URL(returnUrl, window.location.origin);
          callbackUrl.searchParams.set('itemId', itemId);
          callbackUrl.searchParams.set('status', 'success');
          
          toast.success('Conta conectada com sucesso!');
          window.location.href = callbackUrl.toString();
        } else {
          throw new Error('Item ID não encontrado na resposta');
        }
      });

      // Handle error
      connect.onError((error: any) => {
        
        // Redirect back with error
        const callbackUrl = new URL(returnUrl, window.location.origin);
        callbackUrl.searchParams.set('error', error.message || 'Erro desconhecido');
        callbackUrl.searchParams.set('status', 'error');
        
        toast.error('Erro na conexão: ' + (error.message || 'Erro desconhecido'));
        window.location.href = callbackUrl.toString();
      });

      // Handle events
      connect.onEvent((eventName: string, data: any) => {
        
        if (eventName === 'CLOSE') {
          // User closed the widget
          router.push(returnUrl);
        }
      });

      setIsLoading(false);
    };

    const initializeMockPluggyConnect = async () => {
      
      const provider = searchParams.get('provider') || 'Banco de Teste';
      
      setIsLoading(false);
      
      // First try iframe approach
      if (connectRef.current) {
        // Try iframe first
        const iframeUrl = `https://connect.pluggy.ai/?connectToken=${connectToken}`;
        
        connectRef.current.innerHTML = `
          <div class="space-y-4">
            <div class="text-center mb-4">
              <h3 class="text-lg font-semibold">Conectando com ${provider}</h3>
              <p class="text-sm text-gray-600">Usando Pluggy Connect</p>
            </div>
            
            <iframe 
              id="pluggy-iframe"
              src="${iframeUrl}"
              class="w-full h-[600px] border rounded-lg"
              allow="clipboard-read; clipboard-write"
            ></iframe>
            
            <div class="text-center">
              <button id="use-simulator" class="text-sm text-blue-600 hover:text-blue-800 underline">
                Usar simulador de desenvolvimento
              </button>
            </div>
          </div>
        `;

        // Add listener for simulator button
        const simulatorBtn = document.getElementById('use-simulator');
        simulatorBtn?.addEventListener('click', () => {
          showMockInterface();
        });

        // Listen for postMessage from iframe (Pluggy may communicate this way)
        window.addEventListener('message', (event) => {
          
          // Check if message is from Pluggy
          if (event.origin === 'https://connect.pluggy.ai') {
            const { data } = event;
            
            if (data.type === 'success' && data.itemId) {
              // Success!
              const callbackUrl = new URL(returnUrl, window.location.origin);
              callbackUrl.searchParams.set('itemId', data.itemId);
              callbackUrl.searchParams.set('status', 'success');
              
              toast.success('Conta conectada com sucesso!');
              window.location.href = callbackUrl.toString();
            } else if (data.type === 'error') {
              // Error
              const callbackUrl = new URL(returnUrl, window.location.origin);
              callbackUrl.searchParams.set('error', data.message || 'Erro desconhecido');
              callbackUrl.searchParams.set('status', 'error');
              
              toast.error('Erro na conexão');
              window.location.href = callbackUrl.toString();
            }
          }
        });
      }

      const showMockInterface = () => {
        if (!connectRef.current) return;
        
        connectRef.current.innerHTML = `
          <div class="max-w-md mx-auto bg-white rounded-lg shadow-md p-6 text-center">
            <div class="text-blue-600 text-6xl mb-4">🏦</div>
            <h2 class="text-xl font-semibold text-gray-900 mb-2">
              Simulador Pluggy Connect
            </h2>
            <p class="text-gray-600 mb-4">
              Conectando com <strong>${provider}</strong>
            </p>
            <p class="text-sm text-gray-500 mb-6">
              Simulador para desenvolvimento e testes.
            </p>
            
            <div class="space-y-3">
              <button id="mock-success" class="w-full bg-green-600 text-white py-2 px-4 rounded-lg hover:bg-green-700 transition-colors">
                ✅ Simular Conexão Bem-sucedida
              </button>
              <button id="mock-error" class="w-full bg-red-600 text-white py-2 px-4 rounded-lg hover:bg-red-700 transition-colors">
                ❌ Simular Erro de Conexão
              </button>
              <button id="mock-cancel" class="w-full bg-gray-600 text-white py-2 px-4 rounded-lg hover:bg-gray-700 transition-colors">
                🚫 Cancelar
              </button>
            </div>
            
            <div class="mt-4 p-3 bg-blue-50 rounded-lg">
              <p class="text-xs text-blue-700">
                <strong>Token:</strong> ${connectToken.substring(0, 30)}...
              </p>
            </div>
          </div>
        `;

        // Add event listeners
        const successBtn = document.getElementById('mock-success');
        const errorBtn = document.getElementById('mock-error');
        const cancelBtn = document.getElementById('mock-cancel');

        successBtn?.addEventListener('click', () => {
          
          // Generate a mock item ID
          const mockItemId = 'mock_item_' + Date.now();
          
          // Redirect back with success
          const callbackUrl = new URL(returnUrl, window.location.origin);
          callbackUrl.searchParams.set('itemId', mockItemId);
          callbackUrl.searchParams.set('status', 'success');
          
          toast.success('Conexão simulada com sucesso!');
          setTimeout(() => {
            window.location.href = callbackUrl.toString();
          }, 1000);
        });

        errorBtn?.addEventListener('click', () => {
          
          // Redirect back with error
          const callbackUrl = new URL(returnUrl, window.location.origin);
          callbackUrl.searchParams.set('error', 'Erro simulado para desenvolvimento');
          callbackUrl.searchParams.set('status', 'error');
          
          toast.error('Erro simulado!');
          setTimeout(() => {
            window.location.href = callbackUrl.toString();
          }, 1000);
        });

        cancelBtn?.addEventListener('click', () => {
          router.push(returnUrl);
        });
      }
    };

    initializePluggyConnect();
  }, [searchParams, router]);

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="max-w-md w-full bg-white rounded-lg shadow-md p-6 text-center">
          <div className="text-red-500 text-6xl mb-4">⚠️</div>
          <h1 className="text-xl font-semibold text-gray-900 mb-2">
            Erro ao Carregar Pluggy Connect
          </h1>
          <p className="text-gray-600 mb-4">{error}</p>
          <p className="text-sm text-gray-500">
            Redirecionando em alguns segundos...
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {isLoading && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
            <p className="text-gray-600">Carregando Pluggy Connect...</p>
          </div>
        </div>
      )}
      
      <div className="container mx-auto px-4 py-8">
        <div className="max-w-4xl mx-auto">
          <div className="bg-white rounded-lg shadow-md overflow-hidden">
            <div className="bg-blue-600 text-white p-4">
              <h1 className="text-xl font-semibold">Conectar Conta Bancária</h1>
              <p className="text-blue-100 text-sm">
                Complete a autenticação com seu banco via Pluggy Connect
              </p>
            </div>
            
            <div className="p-6">
              <div 
                id="pluggy-connect-container" 
                ref={connectRef}
                className="min-h-[600px] w-full"
              />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}