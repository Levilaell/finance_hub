'use client';

import { useState, useEffect, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import Image from 'next/image';
import dynamic from 'next/dynamic';
import { toast } from 'sonner';

const PluggyConnect = dynamic(
  () => import('react-pluggy-connect').then((mod) => mod.PluggyConnect),
  { ssr: false }
);

import { useAuthStore } from '@/store/auth-store';
import { useBankingStore } from '@/store/banking-store';
import { bankingService } from '@/services/banking.service';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { LoadingSpinner } from '@/components/ui/loading-spinner';
import { ErrorMessage } from '@/components/ui/error-message';
import { EmptyState } from '@/components/ui/empty-state';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';

import {
  CreditCardIcon,
  ArrowPathIcon,
  LinkIcon,
  BuildingLibraryIcon,
  EllipsisVerticalIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon,
  XCircleIcon,
} from '@heroicons/react/24/outline';

import {
  BankAccount,
  PluggyConnectState,
  SyncError,
  PluggyItemStatus,
} from '@/types/banking.types';

export default function AccountsPage() {
  const router = useRouter();
  const { isAuthenticated, isLoading: authLoading } = useAuthStore();
  const {
    accounts,
    loadingAccounts,
    accountsError,
    fetchAccounts,
    syncAccount,
  } = useBankingStore();

  // Local state
  const [pluggyConnect, setPluggyConnect] = useState<PluggyConnectState>({
    isOpen: false,
    token: null,
    mode: 'connect',
  });
  const [syncingAccountId, setSyncingAccountId] = useState<string | null>(null);
  const [syncError, setSyncError] = useState<SyncError | null>(null);
  const [selectedAccount, setSelectedAccount] = useState<BankAccount | null>(null);

  // Check authentication
  useEffect(() => {
    if (!isAuthenticated && !authLoading) {
      router.push('/login');
      return;
    }

    if (isAuthenticated) {
      fetchAccounts();
    }
  }, [isAuthenticated, authLoading, fetchAccounts, router]);

  // Connect new bank
  const handleConnectBank = useCallback(async () => {
    try {
      const response = await bankingService.createConnectToken();

      if (response.success && response.data) {
        setPluggyConnect({
          isOpen: true,
          token: response.data.connect_token,
          mode: 'connect',
        });
      } else {
        throw new Error(response.error || 'Failed to create connect token');
      }
    } catch (error: any) {
      console.error('Failed to connect bank:', error);
      toast.error(error.message || 'Failed to connect bank');
    }
  }, []);

  // Update existing connection
  const handleUpdateConnection = useCallback(async (account: BankAccount) => {
    try {
      // Get the item ID from the account
      const itemId = account.pluggy_id; // This should be from the related item
      
      const response = await bankingService.getUpdateToken(itemId);

      if (response.success && response.data) {
        setPluggyConnect({
          isOpen: true,
          token: response.data.connect_token,
          mode: 'update',
          itemId,
          accountId: account.id,
        });
      } else {
        throw new Error(response.error || 'Failed to create update token');
      }
    } catch (error: any) {
      console.error('Failed to update connection:', error);
      toast.error(error.message || 'Failed to update connection');
    }
  }, []);

  // Sync account
  const handleSyncAccount = useCallback(async (accountId: string) => {
    setSyncingAccountId(accountId);
    setSyncError(null);

    try {
      const response = await syncAccount(accountId);

      if (response.success) {
        const txCount = response.data?.sync_stats?.transactions_synced || 0;
        
        if (txCount > 0) {
          toast.success(`Synced ${txCount} new transactions`);
        } else {
          toast.info('No new transactions found');
        }

        await fetchAccounts();
      } else {
        // Handle specific errors
        if (response.error_code === 'MFA_REQUIRED' || 
            response.error_code === 'LOGIN_ERROR' ||
            response.reconnection_required) {
          
          const account = accounts.find(a => a.id === accountId);
          setSyncError({
            accountId,
            accountName: account?.display_name || 'Bank account',
            errorCode: response.error_code,
            message: response.message || 'Authentication required',
            requiresReconnect: true,
          });
        } else {
          toast.error(response.message || 'Sync failed');
        }
      }
    } catch (error: any) {
      console.error('Sync error:', error);
      toast.error('Failed to sync account');
    } finally {
      setSyncingAccountId(null);
    }
  }, [accounts, syncAccount, fetchAccounts]);

  // Pluggy Connect callbacks
  const handlePluggySuccess = useCallback(async (data: any) => {
    try {
      console.log('Pluggy success:', data);
      
      const itemId = data?.item?.id || data?.itemId;
      if (!itemId) {
        throw new Error('No item ID received');
      }

      // Handle update mode
      if (pluggyConnect.mode === 'update' && pluggyConnect.accountId) {
        toast.success('Connection updated! Syncing...');
        setPluggyConnect({ isOpen: false, token: null, mode: 'connect' });
        
        // Sync the account
        await handleSyncAccount(pluggyConnect.accountId);
        return;
      }

      // Handle new connection
      toast.info('Processing connection...');
      
      const response = await bankingService.handleCallback({
        item_id: itemId,
      });

      if (response.success && response.data) {
        const accountCount = response.data.accounts.length;
        toast.success(`Connected ${accountCount} account(s)`);
        
        setPluggyConnect({ isOpen: false, token: null, mode: 'connect' });
        await fetchAccounts();
      } else {
        throw new Error(response.error || 'Failed to process connection');
      }
    } catch (error: any) {
      console.error('Callback error:', error);
      toast.error(error.message || 'Failed to process connection');
      setPluggyConnect({ isOpen: false, token: null, mode: 'connect' });
    }
  }, [pluggyConnect, handleSyncAccount, fetchAccounts]);

  const handlePluggyError = useCallback((error: any) => {
    console.error('Pluggy error:', error);
    toast.error(error?.message || 'Connection failed');
    setPluggyConnect({ isOpen: false, token: null, mode: 'connect' });
  }, []);

  const handlePluggyClose = useCallback(() => {
    setPluggyConnect({ isOpen: false, token: null, mode: 'connect' });
  }, []);

  // UI Helpers
  const getAccountTypeInfo = (type: string) => {
    const types: Record<string, { label: string; color: string }> = {
      BANK: { label: 'Bank Account', color: 'bg-blue-100 text-blue-800' },
      CREDIT: { label: 'Credit Card', color: 'bg-purple-100 text-purple-800' },
      INVESTMENT: { label: 'Investment', color: 'bg-green-100 text-green-800' },
      LOAN: { label: 'Loan', color: 'bg-orange-100 text-orange-800' },
      OTHER: { label: 'Other', color: 'bg-gray-100 text-gray-800' },
    };
    return types[type] || types.OTHER;
  };

  const getStatusIcon = (status?: PluggyItemStatus) => {
    switch (status) {
      case 'UPDATED':
        return <CheckCircleIcon className="h-5 w-5 text-green-600" />;
      case 'LOGIN_ERROR':
      case 'ERROR':
        return <XCircleIcon className="h-5 w-5 text-red-600" />;
      case 'WAITING_USER_INPUT':
      case 'OUTDATED':
        return <ExclamationTriangleIcon className="h-5 w-5 text-amber-600" />;
      default:
        return <ArrowPathIcon className="h-5 w-5 text-gray-400 animate-spin" />;
    }
  };

  const needsReconnection = (account: BankAccount) => {
    return bankingService.needsReconnection(account);
  };

  // Loading state
  if (authLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <LoadingSpinner />
      </div>
    );
  }

  if (!isAuthenticated) {
    return null;
  }

  if (loadingAccounts && accounts.length === 0) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <LoadingSpinner />
          <p className="mt-4 text-gray-600">Loading accounts...</p>
        </div>
      </div>
    );
  }

  if (accountsError) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <ErrorMessage message={accountsError} onRetry={fetchAccounts} />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Pluggy Connect Widget */}
      {pluggyConnect.isOpen && pluggyConnect.token && (
        <PluggyConnect
          connectToken={pluggyConnect.token}
          updateItem={pluggyConnect.itemId}
          onSuccess={handlePluggySuccess}
          onError={handlePluggyError}
          onClose={handlePluggyClose}
        />
      )}

      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:justify-between sm:items-center gap-4">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Bank Accounts</h1>
          <p className="text-gray-600 mt-1">
            Manage your connected accounts via Open Banking
          </p>
        </div>
        <Button onClick={handleConnectBank} className="w-full sm:w-auto">
          <LinkIcon className="h-4 w-4 mr-2" />
          Connect Bank
        </Button>
      </div>

      {/* Accounts Grid */}
      {accounts.length > 0 ? (
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          {accounts.map((account) => {
            const typeInfo = getAccountTypeInfo(account.type);
            const isSyncing = syncingAccountId === account.id;
            const needsReconnect = needsReconnection(account);

            return (
              <Card key={account.id} className="hover:shadow-lg transition-shadow">
                <CardHeader className="pb-4">
                  <div className="flex items-start justify-between">
                    <div className="flex items-center gap-3">
                      {account.connector?.image_url ? (
                        <Image
                          src={account.connector.image_url}
                          alt={account.connector.name}
                          width={32}
                          height={32}
                          className="object-contain"
                        />
                      ) : (
                        <BuildingLibraryIcon className="h-8 w-8 text-gray-400" />
                      )}
                      <div>
                        <CardTitle className="text-lg">
                          {account.display_name || account.name}
                        </CardTitle>
                        <p className="text-sm text-gray-600">
                          {account.connector?.name}
                        </p>
                      </div>
                    </div>
                    <DropdownMenu>
                      <DropdownMenuTrigger asChild>
                        <Button variant="ghost" size="icon">
                          <EllipsisVerticalIcon className="h-5 w-5" />
                        </Button>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent align="end">
                        <DropdownMenuItem
                          onClick={() => handleSyncAccount(account.id)}
                          disabled={isSyncing || needsReconnect}
                        >
                          <ArrowPathIcon className="h-4 w-4 mr-2" />
                          Sync
                        </DropdownMenuItem>
                        {needsReconnect && (
                          <DropdownMenuItem
                            onClick={() => handleUpdateConnection(account)}
                          >
                            <LinkIcon className="h-4 w-4 mr-2" />
                            Reconnect
                          </DropdownMenuItem>
                        )}
                        <DropdownMenuItem
                          className="text-red-600"
                          onClick={() => setSelectedAccount(account)}
                        >
                          Remove
                        </DropdownMenuItem>
                      </DropdownMenuContent>
                    </DropdownMenu>
                  </div>
                </CardHeader>
                <CardContent className="space-y-4">
                  {/* Account Info */}
                  <div className="flex items-center justify-between">
                    <Badge variant="secondary" className={typeInfo.color}>
                      {typeInfo.label}
                    </Badge>
                    {getStatusIcon(account.item_status)}
                  </div>

                  {/* Balance */}
                  <div>
                    <p className="text-2xl font-bold">
                      {bankingService.formatCurrency(account.balance)}
                    </p>
                    {account.masked_number && (
                      <p className="text-sm text-gray-600">
                        {account.masked_number}
                      </p>
                    )}
                  </div>

                  {/* Status */}
                  {needsReconnect && (
                    <div className="p-3 bg-amber-50 border border-amber-200 rounded-md">
                      <p className="text-sm text-amber-800">
                        Reconnection required to sync
                      </p>
                    </div>
                  )}

                  {/* Last Update */}
                  <p className="text-sm text-gray-500">
                    {account.updated_at
                      ? `Updated ${bankingService.formatDate(account.updated_at)}`
                      : 'Never synced'}
                  </p>

                  {/* Actions */}
                  <div className="flex gap-2">
                    {needsReconnect ? (
                      <Button
                        variant="outline"
                        size="sm"
                        className="flex-1"
                        onClick={() => handleUpdateConnection(account)}
                      >
                        <LinkIcon className="h-4 w-4 mr-1" />
                        Reconnect
                      </Button>
                    ) : (
                      <Button
                        variant="outline"
                        size="sm"
                        className="flex-1"
                        onClick={() => handleSyncAccount(account.id)}
                        disabled={isSyncing}
                      >
                        <ArrowPathIcon
                          className={`h-4 w-4 mr-1 ${
                            isSyncing ? 'animate-spin' : ''
                          }`}
                        />
                        {isSyncing ? 'Syncing...' : 'Sync'}
                      </Button>
                    )}
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => router.push(`/transactions?account=${account.id}`)}
                    >
                      View Transactions
                    </Button>
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>
      ) : (
        <EmptyState
          icon={CreditCardIcon}
          title="No accounts connected"
          description="Connect your first bank account to start tracking your finances"
          action={
            <Button onClick={handleConnectBank}>
              <LinkIcon className="h-4 w-4 mr-2" />
              Connect Bank
            </Button>
          }
        />
      )}

      {/* Sync Error Dialog */}
      <Dialog open={!!syncError} onOpenChange={() => setSyncError(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Authentication Required</DialogTitle>
            <DialogDescription>
              {syncError?.message ||
                'Your bank requires additional authentication to continue syncing.'}
            </DialogDescription>
          </DialogHeader>
          <div className="py-4">
            <div className="bg-blue-50 border border-blue-200 rounded-md p-4">
              <h4 className="font-medium text-blue-900 mb-2">Why does this happen?</h4>
              <ul className="text-sm text-blue-800 space-y-1">
                <li>• Banks require periodic re-authentication for security</li>
                <li>• Some banks need authentication for each sync</li>
                <li>• Your existing transactions are preserved</li>
              </ul>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setSyncError(null)}>
              Cancel
            </Button>
            {syncError?.requiresReconnect && (
              <Button
                onClick={() => {
                  const account = accounts.find(
                    (a) => a.id === syncError.accountId
                  );
                  if (account) {
                    setSyncError(null);
                    handleUpdateConnection(account);
                  }
                }}
              >
                <LinkIcon className="h-4 w-4 mr-2" />
                Reconnect Account
              </Button>
            )}
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <Dialog
        open={!!selectedAccount}
        onOpenChange={() => setSelectedAccount(null)}
      >
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Remove Account</DialogTitle>
            <DialogDescription>
              Are you sure you want to remove {selectedAccount?.display_name}?
              This will disconnect the account but preserve all transaction history.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setSelectedAccount(null)}>
              Cancel
            </Button>
            <Button
              variant="destructive"
              onClick={async () => {
                if (selectedAccount) {
                  try {
                    // TODO: Implement disconnect
                    toast.success('Account removed');
                    setSelectedAccount(null);
                    await fetchAccounts();
                  } catch (error) {
                    toast.error('Failed to remove account');
                  }
                }
              }}
            >
              Remove Account
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}