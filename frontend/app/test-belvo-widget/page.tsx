'use client';

import { useState, useEffect } from 'react';
import { BelvoConnect } from '@/components/banking/belvo-connect';
import { belvoService } from '@/services/belvo.service';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { toast } from 'sonner';
import { Info, ExternalLink, CheckCircle, Loader2 } from 'lucide-react';

export default function TestBelvoWidgetPage() {
  const [isWidgetOpen, setIsWidgetOpen] = useState(false);
  const [connectionResult, setConnectionResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [widgetToken, setWidgetToken] = useState<string>('');

  // Pre-load widget token
  useEffect(() => {
    loadWidgetToken();
  }, []);

  const loadWidgetToken = async () => {
    try {
      const { access_token } = await belvoService.createWidgetToken();
      setWidgetToken(access_token);
    } catch (error) {
      console.error('Error loading widget token:', error);
      toast.error('Erro ao carregar token do widget');
    }
  };

  const handleWidgetSuccess = async (linkId: string) => {
    console.log('Widget success with link:', linkId);
    setIsWidgetOpen(false);
    
    try {
      setLoading(true);
      // After successful connection, sync data
      const syncResult = await belvoService.syncBankData();
      
      setConnectionResult({
        linkId,
        syncResult,
        timestamp: new Date().toISOString()
      });
      
      toast.success(`Conexão estabelecida! ${syncResult.transactions_synced} transações sincronizadas.`);
    } catch (error: any) {
      console.error('Error syncing after connection:', error);
      toast.error('Conexão criada mas houve erro na sincronização');
    } finally {
      setLoading(false);
    }
  };

  const handleWidgetExit = () => {
    console.log('Widget closed');
    setIsWidgetOpen(false);
    toast.info('Widget fechado');
  };

  const handleWidgetError = (error: string) => {
    console.error('Widget error:', error);
    setIsWidgetOpen(false);
    toast.error(`Erro no widget: ${error}`);
  };

  const testSyncAgain = async () => {
    try {
      setLoading(true);
      const syncResult = await belvoService.syncBankData();
      toast.success(`Sincronização concluída: ${syncResult.transactions_synced} transações`);
      
      setConnectionResult((prev: any) => ({
        ...prev,
        lastSync: new Date().toISOString(),
        lastSyncResult: syncResult
      }));
    } catch (error: any) {
      console.error('Sync error:', error);
      toast.error('Erro ao sincronizar dados');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container mx-auto p-6 max-w-4xl">
      <h1 className="text-3xl font-bold mb-6">Teste do Widget Belvo</h1>

      {/* Instructions */}
      <Card className="p-6 mb-6 bg-blue-50 border-blue-200">
        <div className="flex items-start gap-3">
          <Info className="h-5 w-5 text-blue-600 mt-0.5" />
          <div className="space-y-3">
            <div>
              <h2 className="text-lg font-semibold mb-2">Como testar o Widget Belvo</h2>
              <ol className="list-decimal list-inside space-y-1 text-sm">
                <li>Clique em "Abrir Widget Belvo" para iniciar o processo</li>
                <li>Selecione um banco sandbox (ex: "Banco Sandbox MX")</li>
                <li>Use as credenciais de teste fornecidas no widget</li>
                <li>Complete o fluxo de autenticação</li>
                <li>Após sucesso, os dados serão sincronizados automaticamente</li>
              </ol>
            </div>

            <div className="bg-white p-4 rounded-lg border border-blue-200">
              <h3 className="font-semibold mb-2 text-sm">Credenciais Sandbox Comuns:</h3>
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <p className="font-medium">Para contas completas:</p>
                  <code className="block bg-gray-100 p-2 rounded mt-1">
                    Username: bnk100<br />
                    Password: full
                  </code>
                </div>
                <div>
                  <p className="font-medium">Para contas limitadas:</p>
                  <code className="block bg-gray-100 p-2 rounded mt-1">
                    Username: bnk100<br />
                    Password: limited
                  </code>
                </div>
              </div>
            </div>

            <div className="flex items-center gap-2 text-sm">
              <ExternalLink className="h-4 w-4" />
              <a
                href="https://developers.belvo.com/docs/test-in-sandbox"
                target="_blank"
                rel="noopener noreferrer"
                className="text-blue-600 hover:underline"
              >
                Ver documentação completa do Sandbox Belvo
              </a>
            </div>
          </div>
        </div>
      </Card>

      {/* Widget Token Status */}
      <Card className="p-6 mb-6">
        <h2 className="text-xl font-semibold mb-4">Status do Widget</h2>
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-sm text-gray-600">Token do Widget:</span>
            <span className="font-mono text-xs">
              {widgetToken ? `${widgetToken.substring(0, 20)}...` : 'Não carregado'}
            </span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-sm text-gray-600">Status:</span>
            <span className={`text-sm font-medium ${widgetToken ? 'text-green-600' : 'text-gray-500'}`}>
              {widgetToken ? 'Pronto' : 'Aguardando'}
            </span>
          </div>
        </div>
      </Card>

      {/* Open Widget Button */}
      <Card className="p-6 mb-6">
        <h2 className="text-xl font-semibold mb-4">Testar Conexão via Widget</h2>
        <div className="space-y-4">
          <p className="text-sm text-gray-600">
            O widget Belvo abrirá em uma janela modal onde você poderá selecionar
            o banco e autenticar com as credenciais de teste.
          </p>
          
          <Button
            onClick={() => setIsWidgetOpen(true)}
            disabled={!widgetToken || loading}
            size="lg"
            className="w-full"
          >
            Abrir Widget Belvo
          </Button>
        </div>
      </Card>

      {/* Connection Result */}
      {connectionResult && (
        <Card className="p-6 mb-6">
          <h2 className="text-xl font-semibold mb-4">Resultado da Conexão</h2>
          
          <div className="space-y-4">
            <div className="bg-green-50 border border-green-200 rounded-lg p-4">
              <div className="flex items-start gap-2">
                <CheckCircle className="h-5 w-5 text-green-500 mt-0.5" />
                <div className="flex-1">
                  <p className="font-medium text-green-800">Conexão estabelecida com sucesso!</p>
                  <div className="mt-2 space-y-1 text-sm text-green-600">
                    <p>Link ID: <code className="bg-green-100 px-1">{connectionResult.linkId}</code></p>
                    <p>Conectado em: {new Date(connectionResult.timestamp).toLocaleString('pt-BR')}</p>
                  </div>
                </div>
              </div>
            </div>

            {connectionResult.syncResult && (
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <h3 className="font-medium mb-2">Dados Sincronizados:</h3>
                <div className="space-y-1 text-sm">
                  <p>Transações: <span className="font-medium">{connectionResult.syncResult.transactions_synced}</span></p>
                  <p>Mensagem: {connectionResult.syncResult.message}</p>
                  {connectionResult.lastSync && (
                    <p>Última sincronização: {new Date(connectionResult.lastSync).toLocaleString('pt-BR')}</p>
                  )}
                </div>
              </div>
            )}

            <Button
              onClick={testSyncAgain}
              variant="outline"
              disabled={loading}
              className="w-full"
            >
              {loading ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin mr-2" />
                  Sincronizando...
                </>
              ) : (
                'Sincronizar Novamente'
              )}
            </Button>
          </div>
        </Card>
      )}

      {/* Debug Info */}
      <Card className="p-6 bg-gray-50">
        <h2 className="text-lg font-semibold mb-3">Informações de Debug</h2>
        <div className="space-y-2 text-sm font-mono">
          <p>Widget aberto: {isWidgetOpen ? 'Sim' : 'Não'}</p>
          <p>Token carregado: {widgetToken ? 'Sim' : 'Não'}</p>
          <p>Conexão estabelecida: {connectionResult ? 'Sim' : 'Não'}</p>
          <p>Loading: {loading ? 'Sim' : 'Não'}</p>
          {connectionResult && (
            <>
              <p>Link ID: {connectionResult.linkId}</p>
              <p>Transações sincronizadas: {connectionResult.syncResult?.transactions_synced || 0}</p>
            </>
          )}
        </div>
      </Card>

      {/* Belvo Connect Widget */}
      {isWidgetOpen && (
        <BelvoConnect
          isOpen={isWidgetOpen}
          onSuccess={handleWidgetSuccess}
          onExit={handleWidgetExit}
          onError={handleWidgetError}
        />
      )}
    </div>
  );
}