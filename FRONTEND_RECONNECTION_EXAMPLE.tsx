// Exemplo de implementação de reconexão no Frontend (React + TypeScript)

import React, { useState, useEffect } from 'react';
import { Button, Modal, Alert, Spin } from 'antd';
import { ExclamationCircleOutlined, SyncOutlined } from '@ant-design/icons';

interface Account {
  id: number;
  nickname: string;
  bank_provider: {
    name: string;
    logo?: string;
  };
}

interface AccountStatus {
  item_status: string;
  needs_reconnection: boolean;
  reconnection_message?: string;
  reconnection_url?: string;
}

// Hook para verificar status da conta
export const useAccountStatus = (accountId: number) => {
  const [status, setStatus] = useState<AccountStatus | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const checkStatus = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await fetch(`/api/banking/pluggy/accounts/${accountId}/status/`);
      const data = await response.json();
      
      if (data.success) {
        setStatus(data.data);
      } else {
        setError(data.error);
      }
    } catch (err) {
      setError('Erro ao verificar status da conta');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    checkStatus();
  }, [accountId]);

  return { status, loading, error, refresh: checkStatus };
};

// Componente de Status da Conta
export const AccountStatusBadge: React.FC<{ account: Account }> = ({ account }) => {
  const { status, loading } = useAccountStatus(account.id);

  if (loading) return <Spin size="small" />;

  if (status?.needs_reconnection) {
    return (
      <Alert
        message="Reconexão Necessária"
        type="warning"
        icon={<ExclamationCircleOutlined />}
        showIcon
        style={{ marginBottom: 16 }}
      />
    );
  }

  return null;
};

// Componente de Reconexão
export const ReconnectionModal: React.FC<{
  account: Account;
  visible: boolean;
  onClose: () => void;
  onSuccess: () => void;
}> = ({ account, visible, onClose, onSuccess }) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleReconnect = async () => {
    setLoading(true);
    setError(null);

    try {
      // 1. Obter token de reconexão
      const response = await fetch(`/api/banking/pluggy/accounts/${account.id}/reconnect/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      const data = await response.json();

      if (!data.success) {
        throw new Error(data.error || 'Erro ao gerar token de reconexão');
      }

      // 2. Configurar Pluggy Connect
      const PluggyConnect = (window as any).PluggyConnect;
      
      const connect = new PluggyConnect({
        connectToken: data.data.connect_token,
        includeSandbox: data.data.sandbox_mode,
        updateItem: data.data.item_id, // Importante: passar o itemId para atualização
        
        onSuccess: (itemData: any) => {
          console.log('Reconexão bem-sucedida:', itemData);
          
          // Fechar modal
          onClose();
          
          // Notificar sucesso
          onSuccess();
          
          // Sincronizar transações automaticamente
          syncAccount(account.id);
        },
        
        onError: (error: any) => {
          console.error('Erro na reconexão:', error);
          setError(error.message || 'Erro ao reconectar conta');
        },
        
        onClose: () => {
          setLoading(false);
        }
      });

      // 3. Abrir Pluggy Connect
      connect.init();

    } catch (err: any) {
      setError(err.message || 'Erro ao iniciar reconexão');
      setLoading(false);
    }
  };

  return (
    <Modal
      title="Reconexão Necessária"
      visible={visible}
      onCancel={onClose}
      footer={[
        <Button key="cancel" onClick={onClose}>
          Cancelar
        </Button>,
        <Button
          key="reconnect"
          type="primary"
          icon={<SyncOutlined />}
          loading={loading}
          onClick={handleReconnect}
        >
          Reconectar Conta
        </Button>,
      ]}
    >
      <div style={{ textAlign: 'center', padding: '20px 0' }}>
        {account.bank_provider.logo && (
          <img
            src={account.bank_provider.logo}
            alt={account.bank_provider.name}
            style={{ width: 80, marginBottom: 16 }}
          />
        )}
        
        <h3>{account.bank_provider.name}</h3>
        <p>{account.nickname}</p>
        
        <Alert
          message="O banco está solicitando que você faça login novamente para continuar sincronizando suas transações."
          type="info"
          showIcon
          style={{ marginTop: 16 }}
        />
        
        {error && (
          <Alert
            message={error}
            type="error"
            showIcon
            style={{ marginTop: 16 }}
          />
        )}
        
        <p style={{ marginTop: 16, fontSize: 12, color: '#666' }}>
          A reconexão é segura e suas transações anteriores serão mantidas.
        </p>
      </div>
    </Modal>
  );
};

// Componente principal de sincronização
export const AccountSync: React.FC<{ account: Account }> = ({ account }) => {
  const [syncing, setSyncing] = useState(false);
  const [showReconnection, setShowReconnection] = useState(false);
  const { status, refresh: refreshStatus } = useAccountStatus(account.id);

  const handleSync = async () => {
    // Verificar status antes de sincronizar
    if (status?.needs_reconnection) {
      setShowReconnection(true);
      return;
    }

    setSyncing(true);

    try {
      const response = await fetch(`/api/banking/pluggy/accounts/${account.id}/sync/`, {
        method: 'POST',
      });

      const data = await response.json();

      if (!response.ok) {
        // Verificar se é erro de reconexão
        if (data.error_code === 'WAITING_USER_ACTION') {
          setShowReconnection(true);
          return;
        }
        throw new Error(data.error || 'Erro ao sincronizar');
      }

      // Sucesso
      message.success(`${data.data.transactions_synced} transações sincronizadas!`);
      
    } catch (error: any) {
      message.error(error.message || 'Erro ao sincronizar conta');
    } finally {
      setSyncing(false);
    }
  };

  const handleReconnectionSuccess = () => {
    message.success('Conta reconectada com sucesso!');
    refreshStatus();
    // Sincronizar automaticamente após reconexão
    handleSync();
  };

  return (
    <>
      <Button
        type="primary"
        icon={<SyncOutlined />}
        loading={syncing}
        onClick={handleSync}
        danger={status?.needs_reconnection}
      >
        {status?.needs_reconnection ? 'Reconexão Necessária' : 'Sincronizar'}
      </Button>

      <ReconnectionModal
        account={account}
        visible={showReconnection}
        onClose={() => setShowReconnection(false)}
        onSuccess={handleReconnectionSuccess}
      />
    </>
  );
};

// Função auxiliar para sincronizar conta
async function syncAccount(accountId: number) {
  try {
    const response = await fetch(`/api/banking/pluggy/accounts/${accountId}/sync/`, {
      method: 'POST',
    });
    
    const data = await response.json();
    
    if (data.success) {
      message.success(`${data.data.transactions_synced} transações sincronizadas!`);
    }
  } catch (error) {
    console.error('Erro ao sincronizar após reconexão:', error);
  }
}

// Exemplo de uso na lista de contas
export const AccountsList: React.FC = () => {
  const [accounts, setAccounts] = useState<Account[]>([]);

  return (
    <div>
      {accounts.map(account => (
        <div key={account.id} style={{ marginBottom: 16 }}>
          <AccountStatusBadge account={account} />
          
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div>
              <h3>{account.nickname}</h3>
              <p>{account.bank_provider.name}</p>
            </div>
            
            <AccountSync account={account} />
          </div>
        </div>
      ))}
    </div>
  );
};