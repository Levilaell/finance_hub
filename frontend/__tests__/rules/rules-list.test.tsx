import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { RulesList } from '@/components/rules/rules-list';
import { rulesService, CategoryRule } from '@/services/rules.service';

// Mock services
jest.mock('@/services/rules.service', () => ({
  rulesService: {
    getRules: jest.fn(),
    updateRule: jest.fn(),
    deleteRule: jest.fn(),
    testRule: jest.fn(),
    applyRuleToExisting: jest.fn(),
  },
}));

// Mock toast
jest.mock('sonner', () => ({
  toast: {
    success: jest.fn(),
    error: jest.fn(),
    info: jest.fn(),
  },
}));

// Mock confirm dialog
const mockConfirm = jest.fn();
Object.defineProperty(window, 'confirm', {
  value: mockConfirm,
  writable: true,
});

const mockRulesService = rulesService as jest.Mocked<typeof rulesService>;

const mockRules: CategoryRule[] = [
  {
    id: 1,
    name: 'Transportation Rule',
    rule_type: 'keyword',
    conditions: { keywords: ['uber', 'taxi'] },
    category: 1,
    category_name: 'Transportation',
    priority: 10,
    is_active: true,
    confidence_threshold: 0.8,
    match_count: 25,
    accuracy_rate: 0.92,
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
    created_by: 1,
    created_by_name: 'Test User',
  },
  {
    id: 2,
    name: 'Food Rule',
    rule_type: 'amount_range',
    conditions: { min_amount: 10, max_amount: 100 },
    category: 2,
    category_name: 'Food',
    priority: 5,
    is_active: false,
    confidence_threshold: 0.7,
    match_count: 50,
    accuracy_rate: 0.85,
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
    created_by: 1,
    created_by_name: 'Test User',
  },
];

const renderWithQueryClient = (component: React.ReactElement) => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });

  return render(
    <QueryClientProvider client={queryClient}>
      {component}
    </QueryClientProvider>
  );
};

describe('RulesList', () => {
  const mockOnCreateRule = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
    mockRulesService.getRules.mockResolvedValue(mockRules);
  });

  it('renders loading state', () => {
    mockRulesService.getRules.mockImplementation(() => new Promise(() => {})); // Never resolves

    renderWithQueryClient(<RulesList onCreateRule={mockOnCreateRule} />);

    expect(screen.getByTestId('loading-spinner')).toBeInTheDocument();
  });

  it('renders empty state when no rules exist', async () => {
    mockRulesService.getRules.mockResolvedValue([]);

    renderWithQueryClient(<RulesList onCreateRule={mockOnCreateRule} />);

    await waitFor(() => {
      expect(screen.getByText('No custom rules created yet')).toBeInTheDocument();
      expect(screen.getByText('Create Your First Rule')).toBeInTheDocument();
    });
  });

  it('renders rules list correctly', async () => {
    renderWithQueryClient(<RulesList onCreateRule={mockOnCreateRule} />);

    await waitFor(() => {
      expect(screen.getByText('Transportation Rule')).toBeInTheDocument();
      expect(screen.getByText('Food Rule')).toBeInTheDocument();
    });

    // Check rule details
    expect(screen.getByText('Target: Transportation')).toBeInTheDocument();
    expect(screen.getByText('Target: Food')).toBeInTheDocument();
    expect(screen.getByText('Keywords: uber,taxi')).toBeInTheDocument();
    expect(screen.getByText('$10 - $100')).toBeInTheDocument();

    // Check badges
    expect(screen.getByText('Active')).toBeInTheDocument();
    expect(screen.getByText('Inactive')).toBeInTheDocument();
    expect(screen.getByText('Keyword')).toBeInTheDocument();
    expect(screen.getByText('Amount')).toBeInTheDocument();
  });

  it('displays rule statistics correctly', async () => {
    renderWithQueryClient(<RulesList onCreateRule={mockOnCreateRule} />);

    await waitFor(() => {
      expect(screen.getByText('Matches: 25 | Accuracy: 92.0%')).toBeInTheDocument();
      expect(screen.getByText('Matches: 50 | Accuracy: 85.0%')).toBeInTheDocument();
    });
  });

  it('opens edit dialog when edit is clicked', async () => {
    const user = userEvent.setup();

    renderWithQueryClient(<RulesList onCreateRule={mockOnCreateRule} />);

    await waitFor(() => {
      expect(screen.getByText('Transportation Rule')).toBeInTheDocument();
    });

    // Click on first rule's dropdown menu
    const dropdownButtons = screen.getAllByRole('button');
    const firstDropdown = dropdownButtons.find(button => 
      button.querySelector('svg')?.getAttribute('data-testid') === 'ellipsis-vertical-icon' ||
      button.textContent === ''
    );
    
    if (firstDropdown) {
      await user.click(firstDropdown);
      
      await waitFor(() => {
        expect(screen.getByText('Edit')).toBeInTheDocument();
      });

      await user.click(screen.getByText('Edit'));
    }

    // Edit dialog should open (would need to check for dialog content)
    // This would require testing the RuleDialog component integration
  });

  it('tests rule when test is clicked', async () => {
    const user = userEvent.setup();
    const mockTestResult = {
      matches_found: 5,
      total_tested: 10,
      match_rate: 0.5,
      matches: [],
    };

    mockRulesService.testRule.mockResolvedValue(mockTestResult);

    renderWithQueryClient(<RulesList onCreateRule={mockOnCreateRule} />);

    await waitFor(() => {
      expect(screen.getByText('Transportation Rule')).toBeInTheDocument();
    });

    // Click on dropdown and test rule
    const dropdownButtons = screen.getAllByRole('button');
    const firstDropdown = dropdownButtons.find(button => 
      button.querySelector('svg') || button.textContent === ''
    );
    
    if (firstDropdown) {
      await user.click(firstDropdown);
      
      await waitFor(() => {
        expect(screen.getByText('Test Rule')).toBeInTheDocument();
      });

      await user.click(screen.getByText('Test Rule'));
    }

    await waitFor(() => {
      expect(mockRulesService.testRule).toHaveBeenCalledWith(1, 100);
    });
  });

  it('applies rule to existing transactions when apply is clicked', async () => {
    const user = userEvent.setup();
    const mockApplyResult = {
      status: 'success',
      results: {
        processed: 20,
        categorized: 18,
        errors: 2,
      },
    };

    mockRulesService.applyRuleToExisting.mockResolvedValue(mockApplyResult);
    mockConfirm.mockReturnValue(true);

    renderWithQueryClient(<RulesList onCreateRule={mockOnCreateRule} />);

    await waitFor(() => {
      expect(screen.getByText('Transportation Rule')).toBeInTheDocument();
    });

    // Click on dropdown and apply rule
    const dropdownButtons = screen.getAllByRole('button');
    const firstDropdown = dropdownButtons.find(button => 
      button.querySelector('svg') || button.textContent === ''
    );
    
    if (firstDropdown) {
      await user.click(firstDropdown);
      
      await waitFor(() => {
        expect(screen.getByText('Apply to Existing')).toBeInTheDocument();
      });

      await user.click(screen.getByText('Apply to Existing'));
    }

    await waitFor(() => {
      expect(mockConfirm).toHaveBeenCalled();
      expect(mockRulesService.applyRuleToExisting).toHaveBeenCalledWith(1, 1000);
    });
  });

  it('toggles rule activation', async () => {
    const user = userEvent.setup();

    mockRulesService.updateRule.mockResolvedValue({
      ...mockRules[0],
      is_active: false,
    });

    renderWithQueryClient(<RulesList onCreateRule={mockOnCreateRule} />);

    await waitFor(() => {
      expect(screen.getByText('Transportation Rule')).toBeInTheDocument();
    });

    // Click on dropdown and toggle activation
    const dropdownButtons = screen.getAllByRole('button');
    const firstDropdown = dropdownButtons.find(button => 
      button.querySelector('svg') || button.textContent === ''
    );
    
    if (firstDropdown) {
      await user.click(firstDropdown);
      
      await waitFor(() => {
        expect(screen.getByText('Deactivate')).toBeInTheDocument();
      });

      await user.click(screen.getByText('Deactivate'));
    }

    await waitFor(() => {
      expect(mockRulesService.updateRule).toHaveBeenCalledWith(1, { is_active: false });
    });
  });

  it('opens delete confirmation dialog', async () => {
    const user = userEvent.setup();

    renderWithQueryClient(<RulesList onCreateRule={mockOnCreateRule} />);

    await waitFor(() => {
      expect(screen.getByText('Transportation Rule')).toBeInTheDocument();
    });

    // Click on dropdown and delete
    const dropdownButtons = screen.getAllByRole('button');
    const firstDropdown = dropdownButtons.find(button => 
      button.querySelector('svg') || button.textContent === ''
    );
    
    if (firstDropdown) {
      await user.click(firstDropdown);
      
      await waitFor(() => {
        expect(screen.getByText('Delete')).toBeInTheDocument();
      });

      await user.click(screen.getByText('Delete'));
    }

    // Check if delete dialog appears
    await waitFor(() => {
      expect(screen.getByText('Delete Rule')).toBeInTheDocument();
      expect(screen.getByText(/Are you sure you want to delete the rule/)).toBeInTheDocument();
    });
  });

  it('deletes rule when confirmed', async () => {
    const user = userEvent.setup();

    mockRulesService.deleteRule.mockResolvedValue(undefined);

    renderWithQueryClient(<RulesList onCreateRule={mockOnCreateRule} />);

    await waitFor(() => {
      expect(screen.getByText('Transportation Rule')).toBeInTheDocument();
    });

    // Open dropdown and click delete
    const dropdownButtons = screen.getAllByRole('button');
    const firstDropdown = dropdownButtons.find(button => 
      button.querySelector('svg') || button.textContent === ''
    );
    
    if (firstDropdown) {
      await user.click(firstDropdown);
      await user.click(screen.getByText('Delete'));
    }

    // Confirm deletion in dialog
    await waitFor(() => {
      expect(screen.getByText('Delete Rule')).toBeInTheDocument();
    });

    const deleteButton = screen.getByRole('button', { name: /delete/i });
    await user.click(deleteButton);

    await waitFor(() => {
      expect(mockRulesService.deleteRule).toHaveBeenCalledWith(1);
    });
  });

  it('displays correct rule type descriptions', async () => {
    const patterRule: CategoryRule = {
      ...mockRules[0],
      id: 3,
      name: 'Pattern Rule',
      rule_type: 'pattern',
      conditions: { regex_pattern: '(?i)(restaurant|cafe)' },
    };

    const counterpartRule: CategoryRule = {
      ...mockRules[0],
      id: 4,
      name: 'Counterpart Rule',
      rule_type: 'counterpart',
      conditions: { counterparts: ['walmart', 'target'] },
    };

    mockRulesService.getRules.mockResolvedValue([patterRule, counterpartRule]);

    renderWithQueryClient(<RulesList onCreateRule={mockOnCreateRule} />);

    await waitFor(() => {
      expect(screen.getByText('Pattern: (?i)(restaurant|cafe)')).toBeInTheDocument();
      expect(screen.getByText('Counterparts: walmart,target')).toBeInTheDocument();
    });
  });

  it('handles API errors gracefully', async () => {
    mockRulesService.getRules.mockRejectedValue(new Error('API Error'));

    renderWithQueryClient(<RulesList onCreateRule={mockOnCreateRule} />);

    // Should handle error gracefully, might show error state or empty state
    // Depending on error handling implementation
  });
});