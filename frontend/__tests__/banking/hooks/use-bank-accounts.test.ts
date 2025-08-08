/**
 * Tests for useBankAccounts hook
 */
import { renderHook, act, waitFor } from '../../test-utils';
import { useBankAccounts } from '@/hooks/use-bank-accounts';
import { bankingService } from '@/services/banking.service';
import { BankAccount } from '@/types/banking.types';

// Mock the banking service
jest.mock('@/services/banking.service', () => ({
  bankingService: {
    getBankAccounts: jest.fn(),
    syncAccount: jest.fn(),
    deleteAccount: jest.fn(),
  },
}));

describe('useBankAccounts', () => {
  const mockAccounts: BankAccount[] = [
    {
      id: '1',
      pluggy_account_id: 'pluggy_1',
      type: 'BANK',
      subtype: 'CHECKING_ACCOUNT',
      name: 'Account 1',
      display_name: 'Account 1',
      masked_number: '****1234',
      balance: 1000,
      currency_code: 'BRL',
      is_active: true,
      item_id: 'item_1',
      item_pluggy_id: 'pluggy_item_1',
      item: {
        id: 'item_1',
        pluggy_item_id: 'pluggy_item_1',
        status: 'UPDATED',
      },
      connector: {
        id: 1,
        name: 'Bank 1',
        image_url: 'https://bank1.com/logo.png',
        primary_color: '#000000',
        is_open_finance: false,
      },
      balance_date: new Date().toISOString(),
      pluggy_created_at: new Date().toISOString(),
      pluggy_updated_at: new Date().toISOString(),
    },
    {
      id: '2',
      pluggy_account_id: 'pluggy_2',
      type: 'CREDIT',
      subtype: 'CREDIT_CARD',
      name: 'Credit Card',
      display_name: 'Credit Card',
      masked_number: '****5678',
      balance: -500,
      currency_code: 'BRL',
      is_active: true,
      item_id: 'item_2',
      item_pluggy_id: 'pluggy_item_2',
      item: {
        id: 'item_2',
        pluggy_item_id: 'pluggy_item_2',
        status: 'UPDATED',
      },
      connector: {
        id: 2,
        name: 'Bank 2',
        image_url: 'https://bank2.com/logo.png',
        primary_color: '#FF0000',
        is_open_finance: true,
      },
      balance_date: new Date().toISOString(),
      pluggy_created_at: new Date().toISOString(),
      pluggy_updated_at: new Date().toISOString(),
    },
  ];

  beforeEach(() => {
    jest.clearAllMocks();
    (bankingService.getBankAccounts as jest.Mock).mockResolvedValue(mockAccounts);
  });

  it('should fetch accounts on mount', async () => {
    const { result } = renderHook(() => useBankAccounts());

    expect(result.current.loading).toBe(true);
    expect(result.current.accounts).toEqual([]);

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.accounts).toEqual(mockAccounts);
    expect(bankingService.getBankAccounts).toHaveBeenCalledTimes(1);
  });

  it('should handle fetch error', async () => {
    const error = new Error('Failed to fetch');
    (bankingService.getBankAccounts as jest.Mock).mockRejectedValue(error);

    const { result } = renderHook(() => useBankAccounts());

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.error).toBe('Failed to fetch');
    expect(result.current.accounts).toEqual([]);
  });

  it('should refetch accounts', async () => {
    const { result } = renderHook(() => useBankAccounts());

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(bankingService.getBankAccounts).toHaveBeenCalledTimes(1);

    // Call refetch
    await act(async () => {
      await result.current.refetch();
    });

    expect(bankingService.getBankAccounts).toHaveBeenCalledTimes(2);
  });

  it('should sync specific account', async () => {
    const syncResponse = { success: true, message: 'Synced' };
    (bankingService.syncAccount as jest.Mock).mockResolvedValue(syncResponse);

    const { result } = renderHook(() => useBankAccounts());

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    // Sync account
    await act(async () => {
      await result.current.syncAccount('1');
    });

    expect(bankingService.syncAccount).toHaveBeenCalledWith('1');
    // Should refetch accounts after sync
    expect(bankingService.getBankAccounts).toHaveBeenCalledTimes(2);
  });

  it('should track syncing state for individual accounts', async () => {
    (bankingService.syncAccount as jest.Mock).mockImplementation(
      () => new Promise(resolve => setTimeout(() => resolve({ success: true }), 100))
    );

    const { result } = renderHook(() => useBankAccounts());

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.syncingAccounts).toEqual({});

    // Start syncing
    act(() => {
      result.current.syncAccount('1');
    });

    expect(result.current.syncingAccounts['1']).toBe(true);

    await waitFor(() => {
      expect(result.current.syncingAccounts['1']).toBe(false);
    });
  });

  it('should delete account', async () => {
    (bankingService.deleteAccount as jest.Mock).mockResolvedValue({ success: true });

    const { result } = renderHook(() => useBankAccounts());

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    // Delete account
    await act(async () => {
      await result.current.deleteAccount('1');
    });

    expect(bankingService.deleteAccount).toHaveBeenCalledWith('1');
    // Should refetch accounts after deletion
    expect(bankingService.getBankAccounts).toHaveBeenCalledTimes(2);
  });

  it('should get accounts by type', async () => {
    const { result } = renderHook(() => useBankAccounts());

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    const bankAccounts = result.current.getAccountsByType('BANK');
    expect(bankAccounts).toHaveLength(1);
    expect(bankAccounts[0].id).toBe('1');

    const creditAccounts = result.current.getAccountsByType('CREDIT');
    expect(creditAccounts).toHaveLength(1);
    expect(creditAccounts[0].id).toBe('2');
  });

  it('should calculate total balance', async () => {
    const { result } = renderHook(() => useBankAccounts());

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    const totalBalance = result.current.getTotalBalance();
    expect(totalBalance).toBe(500); // 1000 - 500
  });

  it('should calculate total balance by type', async () => {
    const { result } = renderHook(() => useBankAccounts());

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    const bankBalance = result.current.getTotalBalanceByType('BANK');
    expect(bankBalance).toBe(1000);

    const creditBalance = result.current.getTotalBalanceByType('CREDIT');
    expect(creditBalance).toBe(-500);
  });

  it('should filter active accounts', async () => {
    const accountsWithInactive = [
      ...mockAccounts,
      {
        ...mockAccounts[0],
        id: '3',
        is_active: false,
      },
    ];
    (bankingService.getBankAccounts as jest.Mock).mockResolvedValue(accountsWithInactive);

    const { result } = renderHook(() => useBankAccounts());

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    const activeAccounts = result.current.getActiveAccounts();
    expect(activeAccounts).toHaveLength(2);
    expect(activeAccounts.every(acc => acc.is_active)).toBe(true);
  });

  it('should handle concurrent sync requests', async () => {
    (bankingService.syncAccount as jest.Mock).mockResolvedValue({ success: true });

    const { result } = renderHook(() => useBankAccounts());

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    // Start multiple syncs
    await act(async () => {
      result.current.syncAccount('1');
      result.current.syncAccount('2');
    });

    expect(result.current.syncingAccounts['1']).toBe(true);
    expect(result.current.syncingAccounts['2']).toBe(true);

    await waitFor(() => {
      expect(result.current.syncingAccounts['1']).toBe(false);
      expect(result.current.syncingAccounts['2']).toBe(false);
    });

    expect(bankingService.syncAccount).toHaveBeenCalledTimes(2);
  });
});