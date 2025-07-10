/**
 * Pluggy service for bank connections
 */
import { apiClient } from '@/lib/api-client';
import { BankProvider, BankAccount } from '@/types';

export interface PluggyBank {
  id: number;
  name: string;
  code: string;
  logo?: string;
  color?: string;
  primary_color?: string;
  health_status: 'ONLINE' | 'UNSTABLE' | 'OFFLINE';
  supports_accounts?: boolean;
  supports_transactions?: boolean;
}

export interface PluggyConnectToken {
  connect_token: string;
  connect_url: string;
  expires_at?: string;
}

export interface PluggyConnectionResult {
  accounts: BankAccount[];
  message: string;
}

export interface PluggyAccountStatus {
  account_id: string;
  external_id: string;
  status: string;
  last_sync?: string;
  balance: number;
  pluggy_status?: string;
  last_update?: string;
  error?: string;
}

class PluggyService {
  /**
   * Get available banks from Pluggy
   */
  async getSupportedBanks(): Promise<PluggyBank[]> {
    try {
      const response = await apiClient.get('/api/banking/pluggy/banks/');
      
      // Handle different response formats
      if ((response as any).success && (response as any).data) {
        // Pluggy format: { success: true, data: [...] }
        return (response as any).data;
      } else if (Array.isArray(response)) {
        // Direct array format
        return response;
      } else if ((response as any).data && Array.isArray((response as any).data)) {
        // Nested data format: { data: [...] }
        return (response as any).data;
      } else {
        console.warn('Unexpected response format:', response);
        return [];
      }
    } catch (error) {
      console.error('Error fetching banks from Pluggy:', error);
      throw error;
    }
  }

  /**
   * Create connect token for Pluggy Connect widget
   */
  async createConnectToken(itemId?: string): Promise<PluggyConnectToken> {
    const response = await apiClient.post('/api/banking/pluggy/connect-token/', {
      item_id: itemId,
    });
    return (response as any).data.data;
  }

  /**
   * Handle successful connection callback from Pluggy Connect
   */
  async handleConnectionCallback(
    itemId: string,
    connectorName: string
  ): Promise<PluggyConnectionResult> {
    const response = await apiClient.post('/api/banking/pluggy/callback/', {
      item_id: itemId,
      connector_name: connectorName,
    });
    return (response as any).data.data;
  }

  /**
   * Handle successful item creation from Pluggy Connect
   */
  async handleItemCreated(itemId: string): Promise<{
    success: boolean;
    message?: string;
    accounts?: any[];
  }> {
    try {
      const response = await apiClient.post('/api/banking/pluggy/callback/', {
        item_id: itemId
      });
      
      return {
        success: (response as any).success || false,
        message: (response as any).data?.message || (response as any).message,
        accounts: (response as any).data?.accounts || []
      };
    } catch (error) {
      console.error('Error handling Pluggy item:', error);
      throw error;
    }
  }

  /**
   * Manually sync account transactions
   */
  async syncAccount(accountId: string): Promise<{ transactions_synced: number; message: string }> {
    const response = await apiClient.post(`/api/banking/pluggy/accounts/${accountId}/sync/`);
    return (response as any).data.data;
  }

  /**
   * Disconnect account from Pluggy
   */
  async disconnectAccount(accountId: string): Promise<{ message: string }> {
    const response = await apiClient.delete(`/api/banking/pluggy/accounts/${accountId}/disconnect/`);
    return (response as any).data;
  }

  /**
   * Get account connection status
   */
  async getAccountStatus(accountId: string): Promise<PluggyAccountStatus> {
    const response = await apiClient.get(`/api/banking/pluggy/accounts/${accountId}/status/`);
    return (response as any).data.data;
  }

  /**
   * Initialize Pluggy Connect widget
   */
  async initializeConnect(
    containerId: string,
    options: {
      connectToken: string;
      includeSandbox?: boolean;
      updateMode?: boolean;
      itemId?: string;
      connectorTypes?: string[];
      connectorIds?: number[];
      countries?: string[];
    }
  ): Promise<void> {
    return new Promise((resolve, reject) => {
      // Check if Pluggy SDK is loaded
      if (typeof window !== 'undefined' && (window as any).PluggyConnect) {
        const PluggyConnect = (window as any).PluggyConnect;
        console.log('🔌 PluggyConnect SDK loaded successfully');

        const connectConfig = {
          connectToken: options.connectToken,
          includeSandbox: options.includeSandbox || false,
          updateMode: options.updateMode || false,
          itemId: options.itemId,
          connectorTypes: options.connectorTypes || ['PERSONAL_BANK'],
          connectorIds: options.connectorIds,
          countries: options.countries || ['BR'],
        };
        
        console.log('🔌 Creating PluggyConnect with config:', {
          ...connectConfig,
          connectToken: connectConfig.connectToken?.substring(0, 50) + '...'
        });

        const connect = new PluggyConnect(connectConfig);

        // Mount the widget
        console.log('🔌 Mounting widget to container:', containerId);
        connect.init(containerId);

        // Handle events
        connect.onSuccess((itemData: any) => {
          console.log('Pluggy connection successful:', itemData);
          
          // Handle the successful connection
          this.handleConnectionCallback(itemData.item.id, itemData.item.connector.name)
            .then((result) => {
              // Emit success event or call callback
              const event = new CustomEvent('pluggyConnectionSuccess', {
                detail: { itemData, accounts: result.accounts }
              });
              window.dispatchEvent(event);
              resolve();
            })
            .catch((error) => {
              console.error('Error handling Pluggy callback:', error);
              reject(error);
            });
        });

        connect.onError((error: any) => {
          console.error('Pluggy connection error:', error);
          
          // Emit error event
          const event = new CustomEvent('pluggyConnectionError', {
            detail: { error }
          });
          window.dispatchEvent(event);
          
          reject(new Error(error.message || 'Connection failed'));
        });

        connect.onEvent((eventName: string, data: any) => {
          console.log('Pluggy event:', eventName, data);
          
          // Handle different events
          switch (eventName) {
            case 'OPEN':
              console.log('Pluggy widget opened');
              break;
            case 'CLOSE':
              console.log('Pluggy widget closed');
              break;
            case 'SELECT_CONNECTOR':
              console.log('Connector selected:', data);
              break;
            case 'SUBMIT_CREDENTIALS':
              console.log('Credentials submitted');
              break;
            case 'WAITING_USER_INPUT':
              console.log('Waiting for user input (MFA, etc.)');
              break;
            case 'SUCCESS':
              console.log('Connection successful');
              break;
            case 'ERROR':
              console.error('Connection error:', data);
              break;
          }
          
          // Emit generic event
          const event = new CustomEvent('pluggyEvent', {
            detail: { eventName, data }
          });
          window.dispatchEvent(event);
        });

      } else {
        reject(new Error('Pluggy SDK not loaded'));
      }
    });
  }

  /**
   * Load Pluggy SDK script
   */
  async loadPluggySDK(): Promise<void> {
    return new Promise((resolve, reject) => {
      if (typeof window === 'undefined') {
        reject(new Error('Window object not available'));
        return;
      }

      // Check if already loaded
      if ((window as any).PluggyConnect) {
        resolve();
        return;
      }

      // Create script element
      const script = document.createElement('script');
      script.src = 'https://connect.pluggy.ai/js/pluggy-connect.js';
      script.async = true;

      console.log('🔄 Loading Pluggy SDK from:', script.src);

      script.onload = () => {
        console.log('✅ Pluggy SDK script loaded');
        if ((window as any).PluggyConnect) {
          console.log('✅ PluggyConnect object available');
          resolve();
        } else {
          console.error('❌ PluggyConnect object not found after script load');
          reject(new Error('Pluggy SDK failed to load'));
        }
      };

      script.onerror = (error) => {
        console.error('❌ Failed to load Pluggy SDK script:', error);
        console.error('❌ Script src was:', script.src);
        reject(new Error('Failed to load Pluggy SDK'));
      };

      // Append to head
      document.head.appendChild(script);
    });
  }

  /**
   * Open Pluggy Connect in a modal
   */
  async openConnectModal(options: {
    connectToken?: string;
    includeSandbox?: boolean;
    updateMode?: boolean;
    itemId?: string;
    connectorTypes?: string[];
    connectorIds?: number[];
    countries?: string[];
  } = {}): Promise<void> {
    try {
      // Load SDK if not already loaded
      await this.loadPluggySDK();

      // Use provided token or get a new one
      let connect_token = options.connectToken;
      if (!connect_token) {
        const tokenResponse = await this.createConnectToken(options.itemId);
        connect_token = tokenResponse.connect_token;
      }

      // Create modal container
      const modalId = 'pluggy-connect-modal';
      let modal = document.getElementById(modalId);
      
      if (!modal) {
        modal = document.createElement('div');
        modal.id = modalId;
        modal.style.cssText = `
          position: fixed;
          top: 0;
          left: 0;
          width: 100%;
          height: 100%;
          background-color: rgba(0, 0, 0, 0.5);
          display: flex;
          justify-content: center;
          align-items: center;
          z-index: 10000;
        `;

        const container = document.createElement('div');
        container.id = 'pluggy-connect-container';
        container.style.cssText = `
          background: white;
          border-radius: 8px;
          padding: 20px;
          max-width: 90%;
          max-height: 90%;
          overflow: auto;
        `;

        modal.appendChild(container);
        document.body.appendChild(modal);
      }

      // Initialize Pluggy Connect
      const containerId = 'pluggy-connect-container';
      console.log('🔧 Initializing Pluggy Connect with token:', connect_token?.substring(0, 50) + '...');
      
      await this.initializeConnect(containerId, {
        connectToken: connect_token,
        ...options,
      });

      // Add close functionality
      const closeModal = () => {
        if (modal && modal.parentNode) {
          modal.parentNode.removeChild(modal);
        }
      };

      // Close on backdrop click
      modal.addEventListener('click', (e) => {
        if (e.target === modal) {
          closeModal();
        }
      });

      // Listen for success/error events to close modal
      const handleSuccess = () => {
        closeModal();
        window.removeEventListener('pluggyConnectionSuccess', handleSuccess);
        window.removeEventListener('pluggyConnectionError', handleError);
      };

      const handleError = () => {
        closeModal();
        window.removeEventListener('pluggyConnectionSuccess', handleSuccess);
        window.removeEventListener('pluggyConnectionError', handleError);
      };

      window.addEventListener('pluggyConnectionSuccess', handleSuccess);
      window.addEventListener('pluggyConnectionError', handleError);

    } catch (error) {
      console.error('Error opening Pluggy Connect modal:', error);
      throw error;
    }
  }
}

export const pluggyService = new PluggyService();