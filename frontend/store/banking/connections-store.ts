/**
 * Bank connections store - handles bank connection (items) state management
 */
import { create } from 'zustand';
import { devtools, subscribeWithSelector } from 'zustand/middleware';
import { bankingService } from '@/services/banking.service';
import { BankingCache } from '@/utils/banking-cache';
import { BankingErrorHandler } from '@/utils/banking-errors';
import type { PluggyItem, PluggyConnector } from '@/types/banking.types';

interface ConnectionsState {
  // Data
  items: PluggyItem[];
  connectors: PluggyConnector[];

  // UI State
  isConnectDialogOpen: boolean;
  connectingItemId: string | null; // For reconnection
  
  // Loading states
  isLoadingItems: boolean;
  isLoadingConnectors: boolean;
  isDeletingItem: Record<string, boolean>; // itemId -> isDeleting
  isSyncingItem: Record<string, boolean>; // itemId -> isSyncing

  // Error states
  itemsError: Error | null;
  connectorsError: Error | null;

  // Actions
  fetchItems: (forceRefresh?: boolean) => Promise<void>;
  fetchConnectors: (forceRefresh?: boolean) => Promise<void>;
  syncItem: (itemId: string) => Promise<void>;
  disconnectItem: (itemId: string) => Promise<void>;
  openConnectDialog: (itemId?: string) => void;
  closeConnectDialog: () => void;
  handleConnectionSuccess: (itemId: string) => Promise<void>;
  reset: () => void;
}

const initialState: Omit<ConnectionsState,
  'fetchItems' | 'fetchConnectors' | 'syncItem' | 'disconnectItem' |
  'openConnectDialog' | 'closeConnectDialog' | 'handleConnectionSuccess' | 'reset'
> = {
  items: [],
  connectors: [],
  isConnectDialogOpen: false,
  connectingItemId: null,
  isLoadingItems: false,
  isLoadingConnectors: false,
  isDeletingItem: {},
  isSyncingItem: {},
  itemsError: null,
  connectorsError: null,
};

export const useConnectionsStore = create<ConnectionsState>()(
  devtools(
    subscribeWithSelector((set, get) => ({
      ...initialState,

      fetchItems: async (forceRefresh = false) => {
        const cacheKey = BankingCache.createKey('items');
        
        // Check cache first
        if (!forceRefresh) {
          const cached = BankingCache.get<PluggyItem[]>(cacheKey);
          if (cached) {
            set({ items: cached, isLoadingItems: false });
            return;
          }
        }

        set({ isLoadingItems: true, itemsError: null });

        try {
          const response = await bankingService.getItems();
          const items = response.results || [];
          
          // Cache the data
          BankingCache.set(cacheKey, items, 10 * 60 * 1000); // 10 minutes
          
          set({ items, isLoadingItems: false });
        } catch (error) {
          set({ itemsError: error as Error, isLoadingItems: false });
          throw error;
        }
      },

      fetchConnectors: async (forceRefresh = false) => {
        const cacheKey = BankingCache.createKey('connectors');
        
        // Check cache first
        if (!forceRefresh) {
          const cached = BankingCache.get<PluggyConnector[]>(cacheKey);
          if (cached) {
            set({ connectors: cached, isLoadingConnectors: false });
            return;
          }
        }

        set({ isLoadingConnectors: true, connectorsError: null });

        try {
          const connectors = await bankingService.getConnectors();
          
          // Cache the data (24 hours for connectors)
          BankingCache.set(cacheKey, connectors, 24 * 60 * 60 * 1000);
          
          set({ connectors, isLoadingConnectors: false });
        } catch (error) {
          set({ connectorsError: error as Error, isLoadingConnectors: false });
        }
      },

      syncItem: async (itemId: string) => {
        // Set syncing state
        set((state) => ({
          isSyncingItem: { ...state.isSyncingItem, [itemId]: true }
        }));

        try {
          await bankingService.syncItem(itemId);
          
          // Refresh items
          await get().fetchItems(true);
          
          // Clear cache for accounts and transactions
          BankingCache.remove(BankingCache.createKey('accounts'));
          BankingCache.remove(BankingCache.createKey('transactions'));
          
        } catch (error) {
          const bankingError = BankingErrorHandler.parseApiError(error);
          throw bankingError;
        } finally {
          // Clear syncing state
          set((state) => {
            const { [itemId]: _, ...rest } = state.isSyncingItem;
            return { isSyncingItem: rest };
          });
        }
      },

      disconnectItem: async (itemId: string) => {
        // Set deleting state
        set((state) => ({
          isDeletingItem: { ...state.isDeletingItem, [itemId]: true }
        }));

        try {
          await bankingService.disconnectItem(itemId);
          
          // Remove item from state
          set((state) => ({
            items: state.items.filter((item) => item.id !== itemId),
          }));
          
          // Clear cache
          BankingCache.remove(BankingCache.createKey('items'));
          BankingCache.remove(BankingCache.createKey('accounts'));
          
        } catch (error) {
          throw error;
        } finally {
          // Clear deleting state
          set((state) => {
            const { [itemId]: _, ...rest } = state.isDeletingItem;
            return { isDeletingItem: rest };
          });
        }
      },

      openConnectDialog: (itemId?: string) => {
        set({
          isConnectDialogOpen: true,
          connectingItemId: itemId || null,
        });
      },

      closeConnectDialog: () => {
        set({
          isConnectDialogOpen: false,
          connectingItemId: null,
        });
      },

      handleConnectionSuccess: async (itemId: string) => {
        // Refresh items and accounts
        await Promise.all([
          get().fetchItems(true),
          // This will trigger account refresh in accounts store
          BankingCache.remove(BankingCache.createKey('accounts')),
        ]);
        
        // Close dialog
        get().closeConnectDialog();
      },

      reset: () => {
        set(initialState);
        // Clear related cache
        BankingCache.remove(BankingCache.createKey('items'));
        BankingCache.remove(BankingCache.createKey('connectors'));
      },
    })),
    {
      name: 'connections-store',
    }
  )
);

// Selectors
export const getItemsByStatus = (state: ConnectionsState, status: string) =>
  state.items.filter((item) => item.status === status);

export const getErrorItems = (state: ConnectionsState) =>
  state.items.filter((item) => 
    ['LOGIN_ERROR', 'ERROR', 'WAITING_USER_INPUT'].includes(item.status)
  );

export const getActiveItems = (state: ConnectionsState) =>
  state.items.filter((item) => item.status === 'UPDATED');

export const getConnectorById = (state: ConnectionsState, connectorId: number) =>
  state.connectors.find((connector) => connector.pluggy_id === connectorId);

export const isItemSyncing = (state: ConnectionsState, itemId: string) =>
  state.isSyncingItem[itemId] || false;

export const isItemDeleting = (state: ConnectionsState, itemId: string) =>
  state.isDeletingItem[itemId] || false;