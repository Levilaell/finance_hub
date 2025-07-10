import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { RuleDialog } from '@/components/rules/rule-dialog';
import { categoriesService } from '@/services/categories.service';
import { CategoryRule } from '@/services/rules.service';

// Mock services
jest.mock('@/services/categories.service', () => ({
  categoriesService: {
    getCategories: jest.fn(),
  },
}));

// Mock toast
jest.mock('sonner', () => ({
  toast: {
    error: jest.fn(),
    success: jest.fn(),
  },
}));

const mockCategoriesService = categoriesService as jest.Mocked<typeof categoriesService>;

const mockCategories = [
  { id: 1, name: 'Transportation', slug: 'transportation', category_type: 'expense' },
  { id: 2, name: 'Food', slug: 'food', category_type: 'expense' },
  { id: 3, name: 'Income', slug: 'income', category_type: 'income' },
];

const mockRule: CategoryRule = {
  id: 1,
  name: 'Test Rule',
  rule_type: 'keyword',
  conditions: { keywords: ['uber', 'taxi'] },
  category: 1,
  category_name: 'Transportation',
  priority: 5,
  is_active: true,
  confidence_threshold: 0.8,
  match_count: 10,
  accuracy_rate: 0.9,
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2024-01-01T00:00:00Z',
  created_by: 1,
  created_by_name: 'Test User',
};

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

describe('RuleDialog', () => {
  const mockOnSave = jest.fn();
  const mockOnOpenChange = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
    mockCategoriesService.getCategories.mockResolvedValue(mockCategories);
  });

  it('renders create rule dialog correctly', async () => {
    renderWithQueryClient(
      <RuleDialog
        open={true}
        onOpenChange={mockOnOpenChange}
        onSave={mockOnSave}
      />
    );

    expect(screen.getByText('Create New Rule')).toBeInTheDocument();
    expect(screen.getByText('Create a new rule to automatically categorize transactions.')).toBeInTheDocument();
    expect(screen.getByLabelText('Rule Name')).toBeInTheDocument();
    expect(screen.getByLabelText('Rule Type')).toBeInTheDocument();
    expect(screen.getByLabelText('Target Category')).toBeInTheDocument();
  });

  it('renders edit rule dialog correctly', async () => {
    renderWithQueryClient(
      <RuleDialog
        open={true}
        onOpenChange={mockOnOpenChange}
        rule={mockRule}
        onSave={mockOnSave}
      />
    );

    expect(screen.getByText('Edit Rule')).toBeInTheDocument();
    expect(screen.getByText('Update the categorization rule settings.')).toBeInTheDocument();
    expect(screen.getByDisplayValue('Test Rule')).toBeInTheDocument();
    expect(screen.getByDisplayValue('uber, taxi')).toBeInTheDocument();
  });

  it('shows keyword fields for keyword rule type', async () => {
    renderWithQueryClient(
      <RuleDialog
        open={true}
        onOpenChange={mockOnOpenChange}
        onSave={mockOnSave}
      />
    );

    // Keyword is default type
    expect(screen.getByLabelText('Keywords (comma-separated)')).toBeInTheDocument();
    expect(screen.getByText('Enter keywords that should match in transaction descriptions')).toBeInTheDocument();
  });

  it('shows amount fields when amount_range type is selected', async () => {
    const user = userEvent.setup();

    renderWithQueryClient(
      <RuleDialog
        open={true}
        onOpenChange={mockOnOpenChange}
        onSave={mockOnSave}
      />
    );

    // Click on rule type selector
    const ruleTypeSelect = screen.getByRole('combobox');
    await user.click(ruleTypeSelect);

    // Select amount range option
    const amountOption = screen.getByText('Amount Range');
    await user.click(amountOption);

    await waitFor(() => {
      expect(screen.getByLabelText('Minimum Amount')).toBeInTheDocument();
      expect(screen.getByLabelText('Maximum Amount')).toBeInTheDocument();
    });
  });

  it('shows counterpart fields when counterpart type is selected', async () => {
    const user = userEvent.setup();

    renderWithQueryClient(
      <RuleDialog
        open={true}
        onOpenChange={mockOnOpenChange}
        onSave={mockOnSave}
      />
    );

    // Click on rule type selector
    const ruleTypeSelect = screen.getByRole('combobox');
    await user.click(ruleTypeSelect);

    // Select counterpart option
    const counterpartOption = screen.getByText('Counterpart Match');
    await user.click(counterpartOption);

    await waitFor(() => {
      expect(screen.getByLabelText('Counterparts (comma-separated)')).toBeInTheDocument();
      expect(screen.getByText('Enter exact names of transaction counterparts')).toBeInTheDocument();
    });
  });

  it('shows pattern fields when pattern type is selected', async () => {
    const user = userEvent.setup();

    renderWithQueryClient(
      <RuleDialog
        open={true}
        onOpenChange={mockOnOpenChange}
        onSave={mockOnSave}
      />
    );

    // Click on rule type selector
    const ruleTypeSelect = screen.getByRole('combobox');
    await user.click(ruleTypeSelect);

    // Select pattern option
    const patternOption = screen.getByText('Regex Pattern');
    await user.click(patternOption);

    await waitFor(() => {
      expect(screen.getByLabelText('Regular Expression Pattern')).toBeInTheDocument();
      expect(screen.getByText('Enter a regular expression pattern to match transaction descriptions')).toBeInTheDocument();
    });
  });

  it('submits keyword rule correctly', async () => {
    const user = userEvent.setup();

    renderWithQueryClient(
      <RuleDialog
        open={true}
        onOpenChange={mockOnOpenChange}
        onSave={mockOnSave}
      />
    );

    // Wait for categories to load
    await waitFor(() => {
      expect(mockCategoriesService.getCategories).toHaveBeenCalled();
    });

    // Fill form
    await user.type(screen.getByLabelText('Rule Name'), 'Transportation Rule');
    
    // Fill keywords
    await user.type(screen.getByLabelText('Keywords (comma-separated)'), 'uber, taxi, bus');

    // Select category
    const categorySelect = screen.getAllByRole('combobox')[1]; // Second combobox is category
    await user.click(categorySelect);
    const transportOption = screen.getByText('Transportation');
    await user.click(transportOption);

    // Fill priority
    await user.clear(screen.getByLabelText('Priority'));
    await user.type(screen.getByLabelText('Priority'), '10');

    // Submit form
    const createButton = screen.getByText('Create Rule');
    await user.click(createButton);

    expect(mockOnSave).toHaveBeenCalledWith({
      name: 'Transportation Rule',
      rule_type: 'keyword',
      category: 1,
      priority: 10,
      confidence_threshold: 0.8,
      is_active: true,
      conditions: {
        keywords: ['uber', 'taxi', 'bus'],
        match_type: 'contains'
      }
    });
  });

  it('submits amount range rule correctly', async () => {
    const user = userEvent.setup();

    renderWithQueryClient(
      <RuleDialog
        open={true}
        onOpenChange={mockOnOpenChange}
        onSave={mockOnSave}
      />
    );

    // Wait for categories to load
    await waitFor(() => {
      expect(mockCategoriesService.getCategories).toHaveBeenCalled();
    });

    // Fill basic info
    await user.type(screen.getByLabelText('Rule Name'), 'High Value Rule');

    // Change rule type to amount_range
    const ruleTypeSelect = screen.getByRole('combobox');
    await user.click(ruleTypeSelect);
    const amountOption = screen.getByText('Amount Range');
    await user.click(amountOption);

    // Fill amount fields
    await waitFor(() => {
      expect(screen.getByLabelText('Minimum Amount')).toBeInTheDocument();
    });

    await user.type(screen.getByLabelText('Minimum Amount'), '1000');
    await user.type(screen.getByLabelText('Maximum Amount'), '5000');

    // Select category
    const categorySelect = screen.getAllByRole('combobox')[1];
    await user.click(categorySelect);
    const incomeOption = screen.getByText('Income');
    await user.click(incomeOption);

    // Submit form
    const createButton = screen.getByText('Create Rule');
    await user.click(createButton);

    expect(mockOnSave).toHaveBeenCalledWith({
      name: 'High Value Rule',
      rule_type: 'amount_range',
      category: 3,
      priority: 0,
      confidence_threshold: 0.8,
      is_active: true,
      conditions: {
        min_amount: 1000,
        max_amount: 5000,
      }
    });
  });

  it('handles form validation errors', async () => {
    const user = userEvent.setup();

    renderWithQueryClient(
      <RuleDialog
        open={true}
        onOpenChange={mockOnOpenChange}
        onSave={mockOnSave}
      />
    );

    // Try to submit without filling required fields
    const createButton = screen.getByText('Create Rule');
    await user.click(createButton);

    // Should not call onSave due to validation
    expect(mockOnSave).not.toHaveBeenCalled();
  });

  it('closes dialog when cancel is clicked', async () => {
    const user = userEvent.setup();

    renderWithQueryClient(
      <RuleDialog
        open={true}
        onOpenChange={mockOnOpenChange}
        onSave={mockOnSave}
      />
    );

    const cancelButton = screen.getByText('Cancel');
    await user.click(cancelButton);

    expect(mockOnOpenChange).toHaveBeenCalledWith(false);
  });

  it('toggles active switch correctly', async () => {
    const user = userEvent.setup();

    renderWithQueryClient(
      <RuleDialog
        open={true}
        onOpenChange={mockOnOpenChange}
        onSave={mockOnSave}
      />
    );

    const activeSwitch = screen.getByRole('switch');
    expect(activeSwitch).toBeChecked(); // Default is true

    await user.click(activeSwitch);
    expect(activeSwitch).not.toBeChecked();
  });

  it('populates form when editing existing rule', () => {
    renderWithQueryClient(
      <RuleDialog
        open={true}
        onOpenChange={mockOnOpenChange}
        rule={mockRule}
        onSave={mockOnSave}
      />
    );

    expect(screen.getByDisplayValue('Test Rule')).toBeInTheDocument();
    expect(screen.getByDisplayValue('uber, taxi')).toBeInTheDocument();
    expect(screen.getByDisplayValue('5')).toBeInTheDocument();
    expect(screen.getByDisplayValue('0.8')).toBeInTheDocument();
    expect(screen.getByRole('switch')).toBeChecked();
  });
});