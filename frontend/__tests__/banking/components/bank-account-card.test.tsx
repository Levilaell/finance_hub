/**
 * Tests for BankAccountCard component
 */
import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { toast } from 'sonner';
import { BankAccountCard } from '@/components/banking/bank-account-card';
import { BankAccount, PluggyItemStatus } from '@/types/banking.types';

// Mock dependencies
jest.mock('next/navigation', () => ({
  useRouter: jest.fn(() => ({
    push: jest.fn(),
  })),
}));

jest.mock('sonner', () => ({
  toast: {
    success: jest.fn(),
    error: jest.fn(),
  },
}));

jest.mock('@/services/banking.service', () => ({
  bankingService: {
    syncAccount: jest.fn(),
    needsReconnection: jest.fn(() => false),
    formatCurrency: jest.fn((amount) => `R$ ${amount.toFixed(2).replace('.', ',').replace(/\B(?=(\d{3})+(?!\d))/g, '.')}`),
  },
}));

// Mock Next.js Image component
jest.mock('next/image', () => ({
  __esModule: true,
  default: (props: any) => {
    // eslint-disable-next-line @next/next/no-img-element
    return <img {...props} alt={props.alt} />;
  },
}));

describe('BankAccountCard', () => {
  const mockAccount: BankAccount = {
    id: '123',
    pluggy_account_id: 'pluggy_123',
    type: 'BANK',
    subtype: 'CHECKING_ACCOUNT',
    name: 'Test Account',
    display_name: 'Test Account - 1234',
    masked_number: '****1234',
    balance: 1000.00,
    currency_code: 'BRL',
    is_active: true,
    item_id: 'item_123',
    item_pluggy_id: 'pluggy_item_123',
    item: {
      id: 'item_123',
      pluggy_item_id: 'pluggy_item_123',
      status: 'UPDATED' as PluggyItemStatus,
    },
    connector: {
      id: 1,
      name: 'Test Bank',
      image_url: 'https://test.com/logo.png',
      primary_color: '#000000',
      is_open_finance: false,
    },
    balance_date: new Date().toISOString(),
    pluggy_created_at: new Date().toISOString(),
    pluggy_updated_at: new Date().toISOString(),
  };

  const mockProps = {
    account: mockAccount,
    isSyncing: false,
    onSync: jest.fn(),
    onReconnect: jest.fn(),
    onRemove: jest.fn(),
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders account information correctly', () => {
    render(<BankAccountCard {...mockProps} />);

    expect(screen.getByText('Test Account - 1234')).toBeInTheDocument();
    expect(screen.getByText('R$ 1.000,00')).toBeInTheDocument();
    expect(screen.getByText('Conta Bancária')).toBeInTheDocument();
    expect(screen.getByText('Test Bank')).toBeInTheDocument();
  });

  it('displays correct status badge for updated account', () => {
    render(<BankAccountCard {...mockProps} />);

    const statusBadge = screen.getByText('Atualizada');
    expect(statusBadge).toBeInTheDocument();
    expect(statusBadge.closest('div')).toHaveClass('bg-green-100');
  });

  it('displays error status when account has error', () => {
    const errorAccount = {
      ...mockAccount,
      item: {
        ...mockAccount.item,
        status: 'LOGIN_ERROR' as PluggyItemStatus,
      },
    };

    render(<BankAccountCard {...mockProps} account={errorAccount} />);

    const statusBadge = screen.getByText('Erro de Login');
    expect(statusBadge).toBeInTheDocument();
    expect(statusBadge.closest('div')).toHaveClass('bg-red-100');
  });

  it('displays syncing state correctly', () => {
    render(<BankAccountCard {...mockProps} isSyncing={true} />);

    // Check for syncing indicator - adjust based on actual implementation
    expect(screen.getByText(/sincronizando/i)).toBeInTheDocument();
  });

  it('calls onSync when sync button is clicked', async () => {
    render(<BankAccountCard {...mockProps} />);

    const syncButton = screen.getByLabelText('Sincronizar conta');
    fireEvent.click(syncButton);

    expect(mockProps.onSync).toHaveBeenCalledWith(mockAccount.id);
  });

  it('shows dropdown menu with options', () => {
    render(<BankAccountCard {...mockProps} />);

    const menuButton = screen.getByRole('button', { name: /menu de opções/i });
    fireEvent.click(menuButton);

    expect(screen.getByText('Ver transações')).toBeInTheDocument();
    expect(screen.getByText('Detalhes da conexão')).toBeInTheDocument();
    expect(screen.getByText('Reconectar')).toBeInTheDocument();
    expect(screen.getByText('Remover conta')).toBeInTheDocument();
  });

  it('navigates to transactions when "Ver transações" is clicked', () => {
    const mockPush = jest.fn();
    const useRouter = jest.requireMock('next/navigation').useRouter;
    useRouter.mockReturnValue({ push: mockPush });

    render(<BankAccountCard {...mockProps} />);

    const menuButton = screen.getByRole('button', { name: /menu de opções/i });
    fireEvent.click(menuButton);

    const transactionsButton = screen.getByText('Ver transações');
    fireEvent.click(transactionsButton);

    expect(mockPush).toHaveBeenCalledWith(`/transactions?account=${mockAccount.id}`);
  });

  it('shows account details when toggle is clicked', () => {
    render(<BankAccountCard {...mockProps} />);

    const menuButton = screen.getByRole('button', { name: /menu de opções/i });
    fireEvent.click(menuButton);

    const detailsButton = screen.getByText('Detalhes da conexão');
    fireEvent.click(detailsButton);

    expect(screen.getByText('Detalhes da Conta')).toBeInTheDocument();
    expect(screen.getByText('****1234')).toBeInTheDocument();
  });

  it('calls onReconnect when reconnect is clicked', () => {
    const errorAccount = {
      ...mockAccount,
      item: {
        ...mockAccount.item,
        status: 'LOGIN_ERROR' as PluggyItemStatus,
      },
    };

    render(<BankAccountCard {...mockProps} account={errorAccount} />);

    const menuButton = screen.getByRole('button', { name: /menu de opções/i });
    fireEvent.click(menuButton);

    const reconnectButton = screen.getByText('Reconectar');
    fireEvent.click(reconnectButton);

    expect(mockProps.onReconnect).toHaveBeenCalledWith(errorAccount);
  });

  it('calls onRemove when remove is clicked', () => {
    render(<BankAccountCard {...mockProps} />);

    const menuButton = screen.getByRole('button', { name: /menu de opções/i });
    fireEvent.click(menuButton);

    const removeButton = screen.getByText('Remover conta');
    fireEvent.click(removeButton);

    expect(mockProps.onRemove).toHaveBeenCalledWith(mockAccount);
  });

  it('displays different account types correctly', () => {
    const accountTypes = [
      { type: 'CREDIT', label: 'Cartão de Crédito' },
      { type: 'INVESTMENT', label: 'Investimento' },
      { type: 'LOAN', label: 'Empréstimo' },
    ];

    accountTypes.forEach(({ type, label }) => {
      const { unmount } = render(
        <BankAccountCard
          {...mockProps}
          account={{ ...mockAccount, type }}
        />
      );

      expect(screen.getByText(label)).toBeInTheDocument();
      unmount();
    });
  });

  it('formats negative balance correctly for credit cards', () => {
    const creditAccount = {
      ...mockAccount,
      type: 'CREDIT',
      balance: -500.50,
    };

    render(<BankAccountCard {...mockProps} account={creditAccount} />);

    expect(screen.getByText('R$ 500,50')).toBeInTheDocument();
    expect(screen.getByText('Fatura atual')).toBeInTheDocument();
  });

  it('shows open finance badge when applicable', () => {
    const openFinanceAccount = {
      ...mockAccount,
      connector: {
        ...mockAccount.connector,
        is_open_finance: true,
      },
    };

    render(<BankAccountCard {...mockProps} account={openFinanceAccount} />);

    expect(screen.getByText('Open Finance')).toBeInTheDocument();
  });

  it('displays last update time correctly', () => {
    render(<BankAccountCard {...mockProps} />);

    // Should show relative time like "há poucos segundos"
    expect(screen.getByText(/há/)).toBeInTheDocument();
  });

  it('handles inactive accounts correctly', () => {
    const inactiveAccount = {
      ...mockAccount,
      is_active: false,
    };

    render(<BankAccountCard {...mockProps} account={inactiveAccount} />);

    // Check if inactive account displays differently
    // The component might show a different visual state or message
    expect(screen.getByText('Test Account - 1234')).toBeInTheDocument();
    // Adjust assertions based on actual inactive account behavior
  });
});