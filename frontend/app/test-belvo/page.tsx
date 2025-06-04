'use client';

import { useState, useEffect } from 'react';
import { belvoService, BelvoInstitution } from '@/services/belvo.service';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { toast } from 'sonner';
import { Loader2, CheckCircle, XCircle, Info } from 'lucide-react';

export default function TestBelvoPage() {
  const [institutions, setInstitutions] = useState<BelvoInstitution[]>([]);
  const [loading, setLoading] = useState(false);
  const [selectedInstitution, setSelectedInstitution] = useState<string>('');
  const [connectionResult, setConnectionResult] = useState<any>(null);
  const [error, setError] = useState<string>('');

  // Test credentials for sandbox
  const sandboxCredentials = {
    username: 'bnk100',
    password: 'full'
  };

  useEffect(() => {
    loadInstitutions();
  }, []);

  const loadInstitutions = async () => {
    try {
      setLoading(true);
      const data = await belvoService.getInstitutions();
      // Filter for sandbox institutions
      const sandboxInstitutions = data.filter(inst => 
        inst.name.toLowerCase().includes('sandbox') || 
        inst.name.toLowerCase().includes('test')
      );
      setInstitutions(sandboxInstitutions.length > 0 ? sandboxInstitutions : data.slice(0, 5));
    } catch (err: any) {
      console.error('Error loading institutions:', err);
      toast.error('Erro ao carregar instituições bancárias');
      setError(err.message || 'Erro ao carregar instituições');
    } finally {
      setLoading(false);
    }
  };

  const testConnection = async () => {
    if (!selectedInstitution) {
      toast.error('Por favor, selecione uma instituição');
      return;
    }

    try {
      setLoading(true);
      setError('');
      setConnectionResult(null);

      // Create connection using sandbox credentials
      const result = await belvoService.createConnection({
        institution: selectedInstitution,
        username: sandboxCredentials.username,
        password: sandboxCredentials.password
      });

      setConnectionResult(result);
      toast.success('Conexão criada com sucesso!');

      // Optionally sync data immediately
      if (result.connection_id) {
        await testSync();
      }
    } catch (err: any) {
      console.error('Connection error:', err);
      const errorMessage = err.response?.data?.error || err.message || 'Erro ao conectar';
      setError(errorMessage);
      toast.error(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const testSync = async () => {
    try {
      setLoading(true);
      const syncResult = await belvoService.syncBankData();
      toast.success(`Sincronização concluída: ${syncResult.transactions_synced} transações`);
      
      // Update connection result with sync info
      setConnectionResult(prev => ({
        ...prev,
        syncResult
      }));
    } catch (err: any) {
      console.error('Sync error:', err);
      toast.error('Erro ao sincronizar dados');
    } finally {
      setLoading(false);
    }
  };

  const disconnectBank = async () => {
    if (!connectionResult?.connection_id) {
      toast.error('Nenhuma conexão para desconectar');
      return;
    }

    try {
      setLoading(true);
      await belvoService.disconnectBank(connectionResult.connection_id);
      toast.success('Banco desconectado com sucesso');
      setConnectionResult(null);
      setSelectedInstitution('');
    } catch (err: any) {
      console.error('Disconnect error:', err);
      toast.error('Erro ao desconectar banco');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container mx-auto p-6 max-w-4xl">
      <h1 className="text-3xl font-bold mb-6">Teste de Integração Belvo</h1>

      {/* Instructions Card */}
      <Card className="p-6 mb-6 bg-blue-50 border-blue-200">
        <div className="flex items-start gap-3">
          <Info className="h-5 w-5 text-blue-600 mt-0.5" />
          <div>
            <h2 className="text-lg font-semibold mb-2">Instruções de Teste</h2>
            <ol className="list-decimal list-inside space-y-1 text-sm">
              <li>Selecione uma instituição bancária sandbox da lista</li>
              <li>Clique em "Testar Conexão" (usa credenciais sandbox automaticamente)</li>
              <li>Credenciais sandbox: Username: <code className="bg-gray-100 px-1">bnk100</code>, Password: <code className="bg-gray-100 px-1">full</code></li>
              <li>Verifique o resultado da conexão e as contas criadas</li>
              <li>Teste a sincronização de dados para buscar transações</li>
              <li>Opcionalmente, desconecte o banco ao finalizar o teste</li>
            </ol>
          </div>
        </div>
      </Card>

      {/* Institution Selection */}
      <Card className="p-6 mb-6">
        <h2 className="text-xl font-semibold mb-4">1. Selecionar Instituição Bancária</h2>
        
        {loading && !institutions.length ? (
          <div className="flex items-center justify-center py-8">
            <Loader2 className="h-6 w-6 animate-spin" />
          </div>
        ) : (
          <div className="space-y-3">
            {institutions.map((inst) => (
              <div
                key={inst.id}
                className={`p-4 border rounded-lg cursor-pointer transition-all ${
                  selectedInstitution === inst.id
                    ? 'border-blue-500 bg-blue-50'
                    : 'border-gray-200 hover:border-gray-300'
                }`}
                onClick={() => setSelectedInstitution(inst.id)}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    {inst.logo && (
                      <img
                        src={inst.logo}
                        alt={inst.name}
                        className="h-8 w-8 object-contain"
                      />
                    )}
                    <div>
                      <h3 className="font-medium">{inst.name}</h3>
                      <p className="text-sm text-gray-500">
                        Tipo: {inst.type} | País: {inst.country}
                      </p>
                    </div>
                  </div>
                  {selectedInstitution === inst.id && (
                    <CheckCircle className="h-5 w-5 text-blue-500" />
                  )}
                </div>
              </div>
            ))}
          </div>
        )}

        <Button
          onClick={loadInstitutions}
          variant="outline"
          className="mt-4"
          disabled={loading}
        >
          Recarregar Instituições
        </Button>
      </Card>

      {/* Test Connection */}
      <Card className="p-6 mb-6">
        <h2 className="text-xl font-semibold mb-4">2. Testar Conexão</h2>
        
        <div className="space-y-4">
          <div className="bg-gray-50 p-4 rounded-lg">
            <p className="text-sm text-gray-600 mb-2">Credenciais Sandbox:</p>
            <div className="font-mono text-sm">
              <p>Username: {sandboxCredentials.username}</p>
              <p>Password: {sandboxCredentials.password}</p>
            </div>
          </div>

          <Button
            onClick={testConnection}
            disabled={!selectedInstitution || loading}
            className="w-full"
          >
            {loading ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin mr-2" />
                Conectando...
              </>
            ) : (
              'Testar Conexão'
            )}
          </Button>
        </div>

        {error && (
          <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg">
            <div className="flex items-start gap-2">
              <XCircle className="h-5 w-5 text-red-500 mt-0.5" />
              <div>
                <p className="font-medium text-red-800">Erro na conexão:</p>
                <p className="text-sm text-red-600 mt-1">{error}</p>
              </div>
            </div>
          </div>
        )}
      </Card>

      {/* Connection Result */}
      {connectionResult && (
        <Card className="p-6 mb-6">
          <h2 className="text-xl font-semibold mb-4">3. Resultado da Conexão</h2>
          
          <div className="space-y-4">
            <div className="bg-green-50 border border-green-200 rounded-lg p-4">
              <div className="flex items-start gap-2">
                <CheckCircle className="h-5 w-5 text-green-500 mt-0.5" />
                <div className="flex-1">
                  <p className="font-medium text-green-800">Conexão estabelecida!</p>
                  <p className="text-sm text-green-600 mt-1">
                    Connection ID: {connectionResult.connection_id}
                  </p>
                </div>
              </div>
            </div>

            {connectionResult.accounts && connectionResult.accounts.length > 0 && (
              <div>
                <h3 className="font-medium mb-2">Contas encontradas:</h3>
                <div className="space-y-2">
                  {connectionResult.accounts.map((account: any) => (
                    <div
                      key={account.id}
                      className="p-3 bg-gray-50 rounded-lg border border-gray-200"
                    >
                      <div className="flex justify-between items-start">
                        <div>
                          <p className="font-medium">{account.bank_name}</p>
                          <p className="text-sm text-gray-600">
                            {account.account_type} - {account.account_number}
                          </p>
                        </div>
                        <p className="font-medium">
                          {account.currency} {account.current_balance.toFixed(2)}
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {connectionResult.syncResult && (
              <div className="p-3 bg-blue-50 rounded-lg">
                <p className="text-sm">
                  <span className="font-medium">Sincronização:</span>{' '}
                  {connectionResult.syncResult.transactions_synced} transações sincronizadas
                </p>
              </div>
            )}

            <div className="flex gap-3">
              <Button
                onClick={testSync}
                variant="outline"
                disabled={loading}
                className="flex-1"
              >
                {loading ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin mr-2" />
                    Sincronizando...
                  </>
                ) : (
                  'Sincronizar Dados'
                )}
              </Button>
              
              <Button
                onClick={disconnectBank}
                variant="destructive"
                disabled={loading}
                className="flex-1"
              >
                Desconectar Banco
              </Button>
            </div>
          </div>
        </Card>
      )}

      {/* Debug Info */}
      <Card className="p-6 bg-gray-50">
        <h2 className="text-lg font-semibold mb-3">Informações de Debug</h2>
        <div className="space-y-2 text-sm font-mono">
          <p>Instituição selecionada: {selectedInstitution || 'Nenhuma'}</p>
          <p>Status: {loading ? 'Carregando...' : 'Pronto'}</p>
          <p>Erro: {error || 'Nenhum'}</p>
          <p>Conexão ID: {connectionResult?.connection_id || 'Nenhuma'}</p>
          <p>Contas: {connectionResult?.accounts?.length || 0}</p>
        </div>
      </Card>
    </div>
  );
}