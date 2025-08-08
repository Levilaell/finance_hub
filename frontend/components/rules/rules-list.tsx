'use client';

import { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog';
import { LoadingSpinner } from '@/components/ui/loading-spinner';
import { RuleDialog } from './rule-dialog';
import { CategoryRule, CreateRuleRequest, rulesService } from '@/services/rules.service';
import {
  EllipsisVerticalIcon,
  PencilIcon,
  TrashIcon,
  PlayIcon,
  BeakerIcon,
  EyeIcon,
} from '@heroicons/react/24/outline';

interface RulesListProps {
  onCreateRule?: () => void;
}

export function RulesList({ onCreateRule }: RulesListProps) {
  const [editingRule, setEditingRule] = useState<CategoryRule | null>(null);
  const [deletingRule, setDeletingRule] = useState<CategoryRule | null>(null);
  const [testingRule, setTestingRule] = useState<CategoryRule | null>(null);
  const queryClient = useQueryClient();

  const { data: rules, isLoading } = useQuery({
    queryKey: ['rules'],
    queryFn: rulesService.getRules,
  });

  const updateRuleMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: Partial<CreateRuleRequest> }) =>
      rulesService.updateRule(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['rules'] });
      toast.success('Regra atualizada com sucesso');
      setEditingRule(null);
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Falha ao atualizar regra');
    },
  });

  const deleteRuleMutation = useMutation({
    mutationFn: rulesService.deleteRule,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['rules'] });
      toast.success('Regra excluída com sucesso');
      setDeletingRule(null);
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Falha ao excluir regra');
    },
  });

  const testRuleMutation = useMutation({
    mutationFn: ({ id, limit }: { id: number; limit: number }) =>
      rulesService.testRule(id, limit),
    onSuccess: (data) => {
      toast.success(
        `Teste concluído: ${data.matches_found} correspondências encontradas de ${data.total_tested} transações (${(data.match_rate * 100).toFixed(1)}% de taxa de correspondência)`,
        { duration: 5000 }
      );
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to test rule');
    },
  });

  const applyRuleMutation = useMutation({
    mutationFn: ({ id, limit }: { id: number; limit: number }) =>
      rulesService.applyRuleToExisting(id, limit),
    onSuccess: (data) => {
      toast.success(
        `Rule applied: ${data.results.categorized} transactions categorized`,
        { duration: 5000 }
      );
      queryClient.invalidateQueries({ queryKey: ['transactions'] });
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to apply rule');
    },
  });

  const getRuleTypeDisplay = (ruleType: CategoryRule['rule_type']) => {
    const types = {
      keyword: 'Keyword',
      amount_range: 'Amount',
      counterpart: 'Counterpart',
      pattern: 'Pattern',
      ai_prediction: 'AI',
    };
    return types[ruleType] || ruleType;
  };

  const getRuleConditionsDisplay = (rule: CategoryRule) => {
    switch (rule.rule_type) {
      case 'keyword':
        return `Keywords: ${rule.conditions.keywords?.join(', ') || 'None'}`;
      case 'amount_range':
        const min = rule.conditions.min_amount;
        const max = rule.conditions.max_amount;
        if (min && max) return `$${min} - $${max}`;
        if (min) return `≥ $${min}`;
        if (max) return `≤ $${max}`;
        return 'Any amount';
      case 'counterpart':
        return `Counterparts: ${rule.conditions.counterparts?.join(', ') || 'None'}`;
      case 'pattern':
        return `Pattern: ${rule.conditions.regex_pattern || 'None'}`;
      default:
        return 'Custom conditions';
    }
  };

  const handleUpdateRule = async (data: CreateRuleRequest) => {
    if (!editingRule) return;
    await updateRuleMutation.mutateAsync({ id: editingRule.id, data });
  };

  const handleDeleteRule = () => {
    if (!deletingRule) return;
    deleteRuleMutation.mutate(deletingRule.id);
  };

  const handleTestRule = (rule: CategoryRule) => {
    testRuleMutation.mutate({ id: rule.id, limit: 100 });
  };

  const handleApplyRule = (rule: CategoryRule) => {
    if (confirm(`Apply this rule to existing transactions? This will categorize matching uncategorized transactions.`)) {
      applyRuleMutation.mutate({ id: rule.id, limit: 1000 });
    }
  };

  const toggleRuleActive = (rule: CategoryRule) => {
    updateRuleMutation.mutate({
      id: rule.id,
      data: { is_active: !rule.is_active }
    });
  };

  if (isLoading) {
    return (
      <div className="flex justify-center py-8">
        <LoadingSpinner />
      </div>
    );
  }

  return (
    <>
      <div className="space-y-4">
        {rules?.length === 0 ? (
          <Card>
            <CardContent className="py-8 text-center">
              <p className="text-gray-500 mb-4">No custom rules created yet</p>
              <Button onClick={onCreateRule}>Create Your First Rule</Button>
            </CardContent>
          </Card>
        ) : (
          rules?.map((rule) => (
            <Card key={rule.id}>
              <CardContent className="p-4">
                <div className="flex justify-between items-start">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-2">
                      <h3 className="font-medium">{rule.name}</h3>
                      <Badge variant={rule.is_active ? 'default' : 'secondary'}>
                        {rule.is_active ? 'Active' : 'Inactive'}
                      </Badge>
                      <Badge variant="outline">
                        {getRuleTypeDisplay(rule.rule_type)}
                      </Badge>
                      <Badge variant="outline">
                        Priority: {rule.priority}
                      </Badge>
                    </div>
                    
                    <div className="space-y-1 text-sm text-gray-600">
                      <p>Target: <span className="font-medium">{rule.category_name}</span></p>
                      <p>{getRuleConditionsDisplay(rule)}</p>
                      {rule.match_count > 0 && (
                        <p>
                          Matches: {rule.match_count} | 
                          Accuracy: {(rule.accuracy_rate * 100).toFixed(1)}%
                        </p>
                      )}
                    </div>
                  </div>

                  <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                      <Button variant="ghost" size="sm">
                        <EllipsisVerticalIcon className="h-4 w-4" />
                      </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="end">
                      <DropdownMenuItem onClick={() => setEditingRule(rule)}>
                        <PencilIcon className="h-4 w-4 mr-2" />
                        Edit
                      </DropdownMenuItem>
                      <DropdownMenuItem onClick={() => handleTestRule(rule)}>
                        <BeakerIcon className="h-4 w-4 mr-2" />
                        Test Rule
                      </DropdownMenuItem>
                      <DropdownMenuItem onClick={() => handleApplyRule(rule)}>
                        <PlayIcon className="h-4 w-4 mr-2" />
                        Apply to Existing
                      </DropdownMenuItem>
                      <DropdownMenuItem onClick={() => toggleRuleActive(rule)}>
                        <EyeIcon className="h-4 w-4 mr-2" />
                        {rule.is_active ? 'Deactivate' : 'Activate'}
                      </DropdownMenuItem>
                      <DropdownMenuItem 
                        onClick={() => setDeletingRule(rule)}
                        className="text-red-600"
                      >
                        <TrashIcon className="h-4 w-4 mr-2" />
                        Delete
                      </DropdownMenuItem>
                    </DropdownMenuContent>
                  </DropdownMenu>
                </div>
              </CardContent>
            </Card>
          ))
        )}
      </div>

      {/* Edit Rule Dialog */}
      {editingRule && (
        <RuleDialog
          open={true}
          onOpenChange={(open) => !open && setEditingRule(null)}
          rule={editingRule}
          onSave={handleUpdateRule}
        />
      )}

      {/* Delete Confirmation Dialog */}
      <AlertDialog open={!!deletingRule} onOpenChange={() => setDeletingRule(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete Rule</AlertDialogTitle>
            <AlertDialogDescription>
              Are you sure you want to delete the rule &ldquo;{deletingRule?.name}&rdquo;? 
              This action cannot be undone.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction 
              onClick={handleDeleteRule}
              className="bg-red-600 hover:bg-red-700"
            >
              Delete
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  );
}