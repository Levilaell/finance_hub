'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { LoadingSpinner } from '@/components/ui/loading-spinner';
import { pluggyService, type PluggyBank } from '@/services/pluggy.service';
import { toast } from 'react-hot-toast';
import { 
  BanknotesIcon, 
  LinkIcon, 
  ExclamationTriangleIcon,
  CheckCircleIcon 
} from '@heroicons/react/24/outline';

interface PluggyConnectProps {
  onConnectionSuccess?: (accounts: any[]) => void;
  onConnectionError?: (error: any) => void;
  className?: string;
  showBankSelection?: boolean;
}

export default function PluggyConnect({
  onConnectionSuccess,
  onConnectionError,
  className = '',
  showBankSelection = true,
}: PluggyConnectProps) {
  const [banks, setBanks] = useState<PluggyBank[]>([]);
  const [loading, setLoading] = useState(true);
  const [connecting, setConnecting] = useState(false);
  const [selectedBank, setSelectedBank] = useState<PluggyBank | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleConnectionSuccess = useCallback((event: any) => {
    const { accounts } = event.detail;
    setConnecting(false);
    
    toast.success(`${accounts?.length || 0} conta(s) conectada(s) com sucesso!`);
    
    if (onConnectionSuccess) {
      onConnectionSuccess(accounts);
    }
  }, [onConnectionSuccess]);

  const handleConnectionError = useCallback((event: any) => {
    const { error } = event.detail;
    setConnecting(false);
    
    console.error('Pluggy connection error:', error);
    toast.error('Falha na conexão com o banco');
    
    if (onConnectionError) {
      onConnectionError(error);
    }
  }, [onConnectionError]);

  const handlePluggyEvent = useCallback((event: any) => {
    const { eventName, data } = event.detail;
    
    switch (eventName) {
      case 'OPEN':
        setConnecting(true);
        break;
      case 'CLOSE':
        setConnecting(false);
        break;
      case 'SUBMIT_CREDENTIALS':
        toast.loading('Validando credenciais...', { id: 'pluggy-auth' });
        break;
      case 'SUCCESS':
        toast.dismiss('pluggy-auth');
        break;
      case 'ERROR':
        toast.dismiss('pluggy-auth');
        break;
    }
  }, []);

  const setupEventListeners = useCallback(() => {
    window.addEventListener('pluggyConnectionSuccess', handleConnectionSuccess);
    window.addEventListener('pluggyConnectionError', handleConnectionError);
    window.addEventListener('pluggyEvent', handlePluggyEvent);
  }, [handleConnectionSuccess, handleConnectionError, handlePluggyEvent]);

  const removeEventListeners = useCallback(() => {
    window.removeEventListener('pluggyConnectionSuccess', handleConnectionSuccess);
    window.removeEventListener('pluggyConnectionError', handleConnectionError);
    window.removeEventListener('pluggyEvent', handlePluggyEvent);
  }, [handleConnectionSuccess, handleConnectionError, handlePluggyEvent]);

  const loadSupportedBanks = async () => {
    try {
      setLoading(true);
      const supportedBanks = await pluggyService.getSupportedBanks();
      
      // Filter for online banks only
      const onlineBanks = supportedBanks.filter(
        bank => bank.health_status === 'ONLINE'
      );
      
      setBanks(onlineBanks);
      setError(null);
    } catch (err) {
      console.error('Error loading banks:', err);
      setError('Falha ao carregar bancos disponíveis');
      toast.error('Erro ao carregar bancos disponíveis');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadSupportedBanks();
    setupEventListeners();

    return () => {
      removeEventListeners();
    };
  }, [removeEventListeners, setupEventListeners]);

  const connectWithBank = async (bank?: PluggyBank) => {
    try {
      setConnecting(true);
      setError(null);

      if (bank) {
        setSelectedBank(bank);
      }

      await pluggyService.openConnectModal({
        includeSandbox: process.env.NODE_ENV === 'development',
        connectorTypes: ['PERSONAL_BANK'],
        countries: ['BR'],
        connectorIds: bank ? [bank.id] : undefined,
      });

    } catch (err) {
      console.error('Error connecting with bank:', err);
      setConnecting(false);
      setError('Falha ao iniciar conexão');
      toast.error('Erro ao conectar com o banco');
    }
  };

  const connectAnyBank = async () => {
    await connectWithBank();
  };

  const getBankStatusBadge = (status: string) => {
    switch (status) {
      case 'ONLINE':
        return (
          <Badge variant="default" className="bg-green-100 text-green-800">
            <CheckCircleIcon className="w-3 h-3 mr-1" />
            Online
          </Badge>
        );
      case 'UNSTABLE':
        return (
          <Badge variant="secondary" className="bg-yellow-100 text-yellow-800">
            <ExclamationTriangleIcon className="w-3 h-3 mr-1" />
            Instável
          </Badge>
        );
      default:
        return (
          <Badge variant="destructive">
            Offline
          </Badge>
        );
    }
  };

  if (loading) {
    return (
      <Card className={className}>
        <CardContent className="flex items-center justify-center py-8">
          <LoadingSpinner size="lg" />
          <span className="ml-2">Carregando bancos disponíveis...</span>
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card className={className}>
        <CardContent className="text-center py-8">
          <ExclamationTriangleIcon className="w-12 h-12 text-red-500 mx-auto mb-4" />
          <p className="text-red-600 mb-4">{error}</p>
          <Button onClick={loadSupportedBanks} variant="outline">
            Tentar Novamente
          </Button>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className={className}>
      <CardHeader>
        <CardTitle className="flex items-center">
          <LinkIcon className="w-6 h-6 mr-2" />
          Conectar Banco
        </CardTitle>
        <CardDescription>
          Conecte suas contas bancárias de forma segura para sincronização automática das transações.
        </CardDescription>
      </CardHeader>
      
      <CardContent>
        {/* Quick Connect Button */}
        <div className="mb-6">
          <Button
            onClick={connectAnyBank}
            disabled={connecting}
            className="w-full"
            size="lg"
          >
            {connecting ? (
              <>
                <LoadingSpinner size="sm" className="mr-2" />
                Conectando...
              </>
            ) : (
              <>
                <BanknotesIcon className="w-5 h-5 mr-2" />
                Conectar Qualquer Banco
              </>
            )}
          </Button>
        </div>

        {/* Bank Selection */}
        {showBankSelection && banks.length > 0 && (
          <>
            <div className="mb-4">
              <h4 className="text-sm font-medium text-gray-700 mb-3">
                Ou escolha um banco específico:
              </h4>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3 max-h-64 overflow-y-auto">
              {banks.map((bank) => (
                <div
                  key={bank.id}
                  className="border rounded-lg p-3 hover:border-blue-300 hover:bg-blue-50 cursor-pointer transition-colors"
                  onClick={() => connectWithBank(bank)}
                >
                  <div className="flex items-center justify-between mb-2">
                    <div 
                      className="w-8 h-8 rounded-full flex items-center justify-center text-white text-sm font-bold"
                      style={{ backgroundColor: bank.color }}
                    >
                      {bank.name.substring(0, 2).toUpperCase()}
                    </div>
                    {getBankStatusBadge(bank.health_status)}
                  </div>
                  
                  <div>
                    <p className="font-medium text-sm text-gray-900 truncate">
                      {bank.name}
                    </p>
                    <p className="text-xs text-gray-500">
                      {bank.supports_transactions ? 'Transações disponíveis' : 'Banco disponível'}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </>
        )}

        {/* No banks available */}
        {banks.length === 0 && (
          <div className="text-center py-4">
            <p className="text-gray-500">
              Nenhum banco disponível no momento.
            </p>
            <Button
              onClick={loadSupportedBanks}
              variant="outline"
              size="sm"
              className="mt-2"
            >
              Recarregar
            </Button>
          </div>
        )}

        {/* Info */}
        <div className="mt-6 p-4 bg-blue-50 rounded-lg">
          <div className="flex items-start">
            <CheckCircleIcon className="w-5 h-5 text-blue-600 mt-0.5 mr-2 flex-shrink-0" />
            <div className="text-sm text-blue-800">
              <p className="font-medium mb-1">Conexão Segura</p>
              <p className="text-blue-700">
                Utilizamos a tecnologia Pluggy para conectar com seu banco de forma segura.
                Suas credenciais não são armazenadas em nossos servidores.
              </p>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}