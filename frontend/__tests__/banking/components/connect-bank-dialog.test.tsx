/**
 * Tests for ConnectBankDialog component
 */
import React from 'react';
import { render, screen, fireEvent, waitFor } from '../../test-utils';
import { toast } from 'sonner';
import { ConnectBankDialog } from '@/components/banking/connect-bank-dialog';
import { PluggyConnector } from '@/types/banking.types';
import { bankingService } from '@/services/banking.service';

// Mock dependencies
jest.mock('sonner', () => ({
  toast: {
    success: jest.fn(),
    error: jest.fn(),
    loading: jest.fn(),
  },
}));

jest.mock('@/services/banking.service', () => ({
  bankingService: {
    getConnectors: jest.fn(),
    createConnectToken: jest.fn(),
  },
}));

jest.mock('@/hooks/use-pluggy-connect', () => ({
  usePluggyConnect: jest.fn(() => ({
    openConnect: jest.fn(),
    isConnecting: false,
  })),
}));

// Mock Heroicons
jest.mock('@heroicons/react/24/outline', () => ({
  MagnifyingGlassIcon: () => <div>SearchIcon</div>,
  BuildingLibraryIcon: () => <div>BankIcon</div>,
  FunnelIcon: () => <div>FilterIcon</div>,
  ShieldCheckIcon: () => <div>ShieldIcon</div>,
  XMarkIcon: () => <div>CloseIcon</div>,
}));

describe('ConnectBankDialog', () => {
  const mockConnectors: PluggyConnector[] = [
    {
      pluggy_id: 1,
      name: 'Banco do Brasil',
      institution_url: 'https://bb.com.br',
      image_url: 'https://bb.com.br/logo.png',
      primary_color: '#FFD700',
      type: 'PERSONAL_BANK',
      country: 'BR',
      has_mfa: true,
      has_oauth: false,
      is_open_finance: true,
      is_sandbox: false,
      products: ['ACCOUNTS', 'TRANSACTIONS'],
      credentials: [],
    },
    {
      pluggy_id: 2,
      name: 'Nubank',
      institution_url: 'https://nubank.com.br',
      image_url: 'https://nubank.com.br/logo.png',
      primary_color: '#8A05BE',
      type: 'PERSONAL_BANK',
      country: 'BR',
      has_mfa: true,
      has_oauth: false,
      is_open_finance: false,
      is_sandbox: false,
      products: ['ACCOUNTS', 'TRANSACTIONS', 'CREDIT_CARDS'],
      credentials: [],
    },
    {
      pluggy_id: 3,
      name: 'Itaú',
      institution_url: 'https://itau.com.br',
      image_url: 'https://itau.com.br/logo.png',
      primary_color: '#EC7000',
      type: 'BUSINESS_BANK',
      country: 'BR',
      has_mfa: false,
      has_oauth: false,
      is_open_finance: true,
      is_sandbox: false,
      products: ['ACCOUNTS', 'TRANSACTIONS'],
      credentials: [],
    },
  ];

  const mockProps = {
    isOpen: true,
    onClose: jest.fn(),
    onSuccess: jest.fn(),
  };

  beforeEach(() => {
    jest.clearAllMocks();
    (bankingService.getConnectors as jest.Mock).mockResolvedValue(mockConnectors);
    (bankingService.createConnectToken as jest.Mock).mockResolvedValue({
      accessToken: 'test-token',
    });
  });

  it('renders dialog when open', async () => {
    render(<ConnectBankDialog {...mockProps} />);

    await waitFor(() => {
      expect(screen.getByText('Conectar Conta Bancária')).toBeInTheDocument();
      expect(screen.getByText('Selecione sua instituição financeira')).toBeInTheDocument();
    });
  });

  it('does not render when closed', () => {
    render(<ConnectBankDialog {...mockProps} isOpen={false} />);

    expect(screen.queryByText('Conectar Conta Bancária')).not.toBeInTheDocument();
  });

  it('loads and displays connectors', async () => {
    render(<ConnectBankDialog {...mockProps} />);

    await waitFor(() => {
      expect(screen.getByText('Banco do Brasil')).toBeInTheDocument();
      expect(screen.getByText('Nubank')).toBeInTheDocument();
      expect(screen.getByText('Itaú')).toBeInTheDocument();
    });

    expect(bankingService.getConnectors).toHaveBeenCalled();
  });

  it('shows loading state while fetching connectors', () => {
    (bankingService.getConnectors as jest.Mock).mockImplementation(
      () => new Promise(() => {}) // Never resolves
    );

    render(<ConnectBankDialog {...mockProps} />);

    expect(screen.getByText('Carregando instituições...')).toBeInTheDocument();
  });

  it('filters connectors by search term', async () => {
    render(<ConnectBankDialog {...mockProps} />);

    await waitFor(() => {
      expect(screen.getByText('Banco do Brasil')).toBeInTheDocument();
    });

    const searchInput = screen.getByPlaceholderText('Buscar banco...');
    fireEvent.change(searchInput, { target: { value: 'nubank' } });

    expect(screen.queryByText('Banco do Brasil')).not.toBeInTheDocument();
    expect(screen.getByText('Nubank')).toBeInTheDocument();
    expect(screen.queryByText('Itaú')).not.toBeInTheDocument();
  });

  it('filters connectors by type', async () => {
    render(<ConnectBankDialog {...mockProps} />);

    await waitFor(() => {
      expect(screen.getByText('Banco do Brasil')).toBeInTheDocument();
    });

    // Click filter button
    const filterButton = screen.getByRole('button', { name: /filtros/i });
    fireEvent.click(filterButton);

    // Select business bank filter
    const businessBankOption = screen.getByRole('menuitem', { name: /banco empresarial/i });
    fireEvent.click(businessBankOption);

    // Only Itaú should be visible (it's a BUSINESS_BANK)
    expect(screen.queryByText('Banco do Brasil')).not.toBeInTheDocument();
    expect(screen.queryByText('Nubank')).not.toBeInTheDocument();
    expect(screen.getByText('Itaú')).toBeInTheDocument();
  });

  it('filters connectors by open finance', async () => {
    render(<ConnectBankDialog {...mockProps} />);

    await waitFor(() => {
      expect(screen.getByText('Banco do Brasil')).toBeInTheDocument();
    });

    // Click filter button
    const filterButton = screen.getByRole('button', { name: /filtros/i });
    fireEvent.click(filterButton);

    // Select open finance filter
    const openFinanceOption = screen.getByRole('menuitem', { name: /open finance/i });
    fireEvent.click(openFinanceOption);

    // Only banks with open finance should be visible
    expect(screen.getByText('Banco do Brasil')).toBeInTheDocument();
    expect(screen.queryByText('Nubank')).not.toBeInTheDocument();
    expect(screen.getByText('Itaú')).toBeInTheDocument();
  });

  it('displays connector features correctly', async () => {
    render(<ConnectBankDialog {...mockProps} />);

    await waitFor(() => {
      expect(screen.getByText('Banco do Brasil')).toBeInTheDocument();
    });

    // Check for Open Finance badge
    const openFinanceBadges = screen.getAllByText('Open Finance');
    expect(openFinanceBadges).toHaveLength(2); // BB and Itaú

    // Check for MFA indicator
    const mfaIndicators = screen.getAllByText('Autenticação em 2 etapas');
    expect(mfaIndicators).toHaveLength(2); // BB and Nubank
  });

  it('handles connector selection', async () => {
    const mockOpenConnect = jest.fn();
    const usePluggyConnect = jest.requireMock('@/hooks/use-pluggy-connect').usePluggyConnect;
    usePluggyConnect.mockReturnValue({
      openConnect: mockOpenConnect,
      isConnecting: false,
    });

    render(<ConnectBankDialog {...mockProps} />);

    await waitFor(() => {
      expect(screen.getByText('Banco do Brasil')).toBeInTheDocument();
    });

    // Click on a bank
    const bankCard = screen.getByText('Banco do Brasil').closest('button');
    fireEvent.click(bankCard!);

    await waitFor(() => {
      expect(bankingService.createConnectToken).toHaveBeenCalledWith({
        connector_ids: [1],
      });
      expect(mockOpenConnect).toHaveBeenCalledWith('test-token');
    });
  });

  it('shows error message when connector selection fails', async () => {
    (bankingService.createConnectToken as jest.Mock).mockRejectedValue(
      new Error('Failed to create token')
    );

    render(<ConnectBankDialog {...mockProps} />);

    await waitFor(() => {
      expect(screen.getByText('Banco do Brasil')).toBeInTheDocument();
    });

    const bankCard = screen.getByText('Banco do Brasil').closest('button');
    fireEvent.click(bankCard!);

    await waitFor(() => {
      expect(toast.error).toHaveBeenCalledWith(
        'Erro ao conectar com o banco. Tente novamente.'
      );
    });
  });

  it('shows empty state when no connectors match filter', async () => {
    render(<ConnectBankDialog {...mockProps} />);

    await waitFor(() => {
      expect(screen.getByText('Banco do Brasil')).toBeInTheDocument();
    });

    const searchInput = screen.getByPlaceholderText('Buscar banco...');
    fireEvent.change(searchInput, { target: { value: 'nonexistent bank' } });

    expect(screen.getByText('Nenhuma instituição encontrada')).toBeInTheDocument();
    expect(screen.getByText('Tente buscar por outro nome ou remova os filtros')).toBeInTheDocument();
  });

  it('calls onClose when close button is clicked', async () => {
    render(<ConnectBankDialog {...mockProps} />);

    await waitFor(() => {
      expect(screen.getByText('Conectar Conta Bancária')).toBeInTheDocument();
    });

    const closeButton = screen.getByRole('button', { name: /fechar/i });
    fireEvent.click(closeButton);

    expect(mockProps.onClose).toHaveBeenCalled();
  });

  it('disables interaction while connecting', async () => {
    const usePluggyConnect = jest.requireMock('@/hooks/use-pluggy-connect').usePluggyConnect;
    usePluggyConnect.mockReturnValue({
      openConnect: jest.fn(),
      isConnecting: true,
    });

    render(<ConnectBankDialog {...mockProps} />);

    await waitFor(() => {
      expect(screen.getByText('Banco do Brasil')).toBeInTheDocument();
    });

    const bankCards = screen.getAllByRole('button', { name: /banco/i });
    bankCards.forEach(card => {
      expect(card).toBeDisabled();
    });
  });

  it('resets filters when clear filter is clicked', async () => {
    render(<ConnectBankDialog {...mockProps} />);

    await waitFor(() => {
      expect(screen.getByText('Banco do Brasil')).toBeInTheDocument();
    });

    // Apply search filter
    const searchInput = screen.getByPlaceholderText('Buscar banco...');
    fireEvent.change(searchInput, { target: { value: 'nubank' } });

    expect(screen.queryByText('Banco do Brasil')).not.toBeInTheDocument();

    // Clear filters
    const clearButton = screen.getByRole('button', { name: /limpar filtros/i });
    fireEvent.click(clearButton);

    // All banks should be visible again
    expect(screen.getByText('Banco do Brasil')).toBeInTheDocument();
    expect(screen.getByText('Nubank')).toBeInTheDocument();
    expect(screen.getByText('Itaú')).toBeInTheDocument();
  });
});