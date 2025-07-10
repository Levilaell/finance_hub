import { rulesService, CategoryRule, CreateRuleRequest } from '@/services/rules.service';
import { apiClient } from '@/services/api.client';

// Mock the API client
jest.mock('@/services/api.client', () => ({
  apiClient: {
    get: jest.fn(),
    post: jest.fn(),
    put: jest.fn(),
    delete: jest.fn(),
  },
}));

const mockApiClient = apiClient as jest.Mocked<typeof apiClient>;

describe('RulesService', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('getRules', () => {
    it('should fetch rules successfully', async () => {
      const mockRules: CategoryRule[] = [
        {
          id: 1,
          name: 'Test Rule',
          rule_type: 'keyword',
          conditions: { keywords: ['test'] },
          category: 1,
          category_name: 'Transportation',
          priority: 1,
          is_active: true,
          confidence_threshold: 0.8,
          match_count: 10,
          accuracy_rate: 0.9,
          created_at: '2024-01-01T00:00:00Z',
          updated_at: '2024-01-01T00:00:00Z',
          created_by: 1,
          created_by_name: 'Test User',
        },
      ];

      mockApiClient.get.mockResolvedValue({ data: mockRules });

      const result = await rulesService.getRules();

      expect(mockApiClient.get).toHaveBeenCalledWith('/api/categories/rules/');
      expect(result).toEqual(mockRules);
    });

    it('should handle API error', async () => {
      mockApiClient.get.mockRejectedValue(new Error('API Error'));

      await expect(rulesService.getRules()).rejects.toThrow('API Error');
    });
  });

  describe('createRule', () => {
    it('should create rule successfully', async () => {
      const mockRule: CreateRuleRequest = {
        name: 'New Rule',
        rule_type: 'keyword',
        conditions: { keywords: ['uber'] },
        category: 1,
        priority: 5,
      };

      const mockCreatedRule: CategoryRule = {
        id: 2,
        ...mockRule,
        category_name: 'Transportation',
        is_active: true,
        confidence_threshold: 0.8,
        match_count: 0,
        accuracy_rate: 0,
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z',
        created_by: 1,
        created_by_name: 'Test User',
      };

      mockApiClient.post.mockResolvedValue({ data: mockCreatedRule });

      const result = await rulesService.createRule(mockRule);

      expect(mockApiClient.post).toHaveBeenCalledWith('/api/categories/rules/', mockRule);
      expect(result).toEqual(mockCreatedRule);
    });
  });

  describe('updateRule', () => {
    it('should update rule successfully', async () => {
      const updateData = { name: 'Updated Rule' };
      const mockUpdatedRule: CategoryRule = {
        id: 1,
        name: 'Updated Rule',
        rule_type: 'keyword',
        conditions: { keywords: ['test'] },
        category: 1,
        category_name: 'Transportation',
        priority: 1,
        is_active: true,
        confidence_threshold: 0.8,
        match_count: 10,
        accuracy_rate: 0.9,
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z',
        created_by: 1,
        created_by_name: 'Test User',
      };

      mockApiClient.put.mockResolvedValue({ data: mockUpdatedRule });

      const result = await rulesService.updateRule(1, updateData);

      expect(mockApiClient.put).toHaveBeenCalledWith('/api/categories/rules/1/', updateData);
      expect(result).toEqual(mockUpdatedRule);
    });
  });

  describe('deleteRule', () => {
    it('should delete rule successfully', async () => {
      mockApiClient.delete.mockResolvedValue({ data: undefined });

      await rulesService.deleteRule(1);

      expect(mockApiClient.delete).toHaveBeenCalledWith('/api/categories/rules/1/');
    });
  });

  describe('testRule', () => {
    it('should test rule successfully', async () => {
      const mockTestResult = {
        matches_found: 5,
        total_tested: 10,
        match_rate: 0.5,
        matches: [
          {
            transaction_id: 1,
            description: 'Uber ride',
            amount: -25.50,
            current_category: null,
          },
        ],
      };

      mockApiClient.post.mockResolvedValue({ data: mockTestResult });

      const result = await rulesService.testRule(1, 100);

      expect(mockApiClient.post).toHaveBeenCalledWith(
        '/api/categories/rules/1/test_rule/',
        { limit: 100 }
      );
      expect(result).toEqual(mockTestResult);
    });
  });

  describe('applyRuleToExisting', () => {
    it('should apply rule to existing transactions', async () => {
      const mockApplyResult = {
        status: 'success',
        results: {
          processed: 50,
          categorized: 45,
          errors: 5,
        },
      };

      mockApiClient.post.mockResolvedValue({ data: mockApplyResult });

      const result = await rulesService.applyRuleToExisting(1, 1000);

      expect(mockApiClient.post).toHaveBeenCalledWith(
        '/api/categories/rules/1/apply_to_existing/',
        { limit: 1000 }
      );
      expect(result).toEqual(mockApplyResult);
    });
  });

  describe('helper methods', () => {
    describe('createKeywordRule', () => {
      it('should create keyword rule with correct conditions', async () => {
        const mockCreatedRule: CategoryRule = {
          id: 1,
          name: 'Uber Rule',
          rule_type: 'keyword',
          conditions: { keywords: ['uber', 'taxi'], match_type: 'contains' },
          category: 1,
          category_name: 'Transportation',
          priority: 5,
          is_active: true,
          confidence_threshold: 0.8,
          match_count: 0,
          accuracy_rate: 0,
          created_at: '2024-01-01T00:00:00Z',
          updated_at: '2024-01-01T00:00:00Z',
          created_by: 1,
          created_by_name: 'Test User',
        };

        mockApiClient.post.mockResolvedValue({ data: mockCreatedRule });

        await rulesService.createKeywordRule('Uber Rule', 1, ['Uber', 'Taxi'], 5);

        expect(mockApiClient.post).toHaveBeenCalledWith('/api/categories/rules/', {
          name: 'Uber Rule',
          rule_type: 'keyword',
          category: 1,
          priority: 5,
          conditions: {
            keywords: ['uber', 'taxi'],
            match_type: 'contains',
          },
        });
      });
    });

    describe('createAmountRule', () => {
      it('should create amount rule with min and max amounts', async () => {
        mockApiClient.post.mockResolvedValue({ data: {} });

        await rulesService.createAmountRule('High Value', 1, 100, 1000, 3);

        expect(mockApiClient.post).toHaveBeenCalledWith('/api/categories/rules/', {
          name: 'High Value',
          rule_type: 'amount_range',
          category: 1,
          priority: 3,
          conditions: {
            min_amount: 100,
            max_amount: 1000,
          },
        });
      });

      it('should create amount rule with only min amount', async () => {
        mockApiClient.post.mockResolvedValue({ data: {} });

        await rulesService.createAmountRule('High Value', 1, 500, undefined, 3);

        expect(mockApiClient.post).toHaveBeenCalledWith('/api/categories/rules/', {
          name: 'High Value',
          rule_type: 'amount_range',
          category: 1,
          priority: 3,
          conditions: {
            min_amount: 500,
            max_amount: undefined,
          },
        });
      });
    });

    describe('createCounterpartRule', () => {
      it('should create counterpart rule with correct conditions', async () => {
        mockApiClient.post.mockResolvedValue({ data: {} });

        await rulesService.createCounterpartRule(
          'Supermarket Rule',
          1,
          ['Walmart', 'Target'],
          2
        );

        expect(mockApiClient.post).toHaveBeenCalledWith('/api/categories/rules/', {
          name: 'Supermarket Rule',
          rule_type: 'counterpart',
          category: 1,
          priority: 2,
          conditions: {
            counterparts: ['walmart', 'target'],
            match_type: 'exact',
          },
        });
      });
    });

    describe('createPatternRule', () => {
      it('should create pattern rule with regex', async () => {
        mockApiClient.post.mockResolvedValue({ data: {} });

        await rulesService.createPatternRule(
          'Restaurant Pattern',
          1,
          '(?i)(restaurant|cafe)',
          4
        );

        expect(mockApiClient.post).toHaveBeenCalledWith('/api/categories/rules/', {
          name: 'Restaurant Pattern',
          rule_type: 'pattern',
          category: 1,
          priority: 4,
          conditions: {
            regex_pattern: '(?i)(restaurant|cafe)',
            flags: 'i',
          },
        });
      });
    });
  });
});