'use client';

import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { useQuery } from '@tanstack/react-query';
import { toast } from 'sonner';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Switch } from '@/components/ui/switch';
import { LoadingSpinner } from '@/components/ui/loading-spinner';
import { categoriesService } from '@/services/categories.service';
import { CategoryRule, CreateRuleRequest } from '@/services/rules.service';

interface RuleDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  rule?: CategoryRule | null;
  onSave: (data: CreateRuleRequest) => Promise<void>;
}

interface RuleFormData {
  name: string;
  rule_type: CategoryRule['rule_type'];
  category: string;
  priority: number;
  confidence_threshold: number;
  is_active: boolean;
  // Condition fields
  keywords: string;
  min_amount: string;
  max_amount: string;
  counterparts: string;
  regex_pattern: string;
}

export function RuleDialog({ open, onOpenChange, rule, onSave }: RuleDialogProps) {
  const [isLoading, setIsLoading] = useState(false);

  const { data: categories } = useQuery({
    queryKey: ['categories'],
    queryFn: categoriesService.getCategories,
  });

  const form = useForm<RuleFormData>({
    defaultValues: {
      name: rule?.name || '',
      rule_type: rule?.rule_type || 'keyword',
      category: rule?.category?.toString() || '',
      priority: rule?.priority || 0,
      confidence_threshold: rule?.confidence_threshold || 0.8,
      is_active: rule?.is_active ?? true,
      keywords: rule?.conditions?.keywords?.join(', ') || '',
      min_amount: rule?.conditions?.min_amount?.toString() || '',
      max_amount: rule?.conditions?.max_amount?.toString() || '',
      counterparts: rule?.conditions?.counterparts?.join(', ') || '',
      regex_pattern: rule?.conditions?.regex_pattern || '',
    },
  });

  const ruleType = form.watch('rule_type');

  const onSubmit = async (data: RuleFormData) => {
    setIsLoading(true);
    try {
      let conditions: Record<string, any> = {};

      switch (data.rule_type) {
        case 'keyword':
          conditions = {
            keywords: data.keywords
              .split(',')
              .map(k => k.trim().toLowerCase())
              .filter(k => k.length > 0),
            match_type: 'contains'
          };
          break;
        case 'amount_range':
          conditions = {
            min_amount: data.min_amount ? parseFloat(data.min_amount) : undefined,
            max_amount: data.max_amount ? parseFloat(data.max_amount) : undefined,
          };
          break;
        case 'counterpart':
          conditions = {
            counterparts: data.counterparts
              .split(',')
              .map(c => c.trim().toLowerCase())
              .filter(c => c.length > 0),
            match_type: 'exact'
          };
          break;
        case 'pattern':
          conditions = {
            regex_pattern: data.regex_pattern,
            flags: 'i'
          };
          break;
      }

      const payload: CreateRuleRequest = {
        name: data.name,
        rule_type: data.rule_type,
        category: parseInt(data.category),
        priority: data.priority,
        confidence_threshold: data.confidence_threshold,
        is_active: data.is_active,
        conditions,
      };

      await onSave(payload);
      onOpenChange(false);
      form.reset();
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to save rule');
    } finally {
      setIsLoading(false);
    }
  };

  const renderConditionFields = () => {
    switch (ruleType) {
      case 'keyword':
        return (
          <div>
            <Label htmlFor="keywords">Keywords (comma-separated)</Label>
            <Textarea
              id="keywords"
              placeholder="uber, taxi, transport"
              {...form.register('keywords', { required: true })}
            />
            <p className="text-sm text-gray-500 mt-1">
              Enter keywords that should match in transaction descriptions
            </p>
          </div>
        );

      case 'amount_range':
        return (
          <div className="grid grid-cols-2 gap-4">
            <div>
              <Label htmlFor="min_amount">Minimum Amount</Label>
              <Input
                id="min_amount"
                type="number"
                step="0.01"
                placeholder="0.00"
                {...form.register('min_amount')}
              />
            </div>
            <div>
              <Label htmlFor="max_amount">Maximum Amount</Label>
              <Input
                id="max_amount"
                type="number"
                step="0.01"
                placeholder="1000.00"
                {...form.register('max_amount')}
              />
            </div>
          </div>
        );

      case 'counterpart':
        return (
          <div>
            <Label htmlFor="counterparts">Counterparts (comma-separated)</Label>
            <Textarea
              id="counterparts"
              placeholder="Supermarket ABC, Restaurant XYZ"
              {...form.register('counterparts', { required: true })}
            />
            <p className="text-sm text-gray-500 mt-1">
              Enter exact names of transaction counterparts
            </p>
          </div>
        );

      case 'pattern':
        return (
          <div>
            <Label htmlFor="regex_pattern">Regular Expression Pattern</Label>
            <Input
              id="regex_pattern"
              placeholder="^(PAYROLL|SALARY).*"
              {...form.register('regex_pattern', { required: true })}
            />
            <p className="text-sm text-gray-500 mt-1">
              Enter a regular expression pattern to match transaction descriptions
            </p>
          </div>
        );

      default:
        return null;
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[600px]">
        <DialogHeader>
          <DialogTitle>
            {rule ? 'Edit Rule' : 'Create New Rule'}
          </DialogTitle>
          <DialogDescription>
            {rule 
              ? 'Update the categorization rule settings.' 
              : 'Create a new rule to automatically categorize transactions.'
            }
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <Label htmlFor="name">Rule Name</Label>
              <Input
                id="name"
                placeholder="Transportation expenses"
                {...form.register('name', { required: true })}
              />
            </div>
            <div>
              <Label htmlFor="rule_type">Rule Type</Label>
              <Select
                value={form.watch('rule_type')}
                onValueChange={(value) => form.setValue('rule_type', value as CategoryRule['rule_type'])}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="keyword">Keyword Match</SelectItem>
                  <SelectItem value="amount_range">Amount Range</SelectItem>
                  <SelectItem value="counterpart">Counterpart Match</SelectItem>
                  <SelectItem value="pattern">Regex Pattern</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>

          <div>
            <Label htmlFor="category">Target Category</Label>
            <Select
              value={form.watch('category')}
              onValueChange={(value) => form.setValue('category', value)}
            >
              <SelectTrigger>
                <SelectValue placeholder="Select a category" />
              </SelectTrigger>
              <SelectContent>
                {categories?.map((category) => (
                  <SelectItem key={category.id} value={category.id.toString()}>
                    {category.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {renderConditionFields()}

          <div className="grid grid-cols-2 gap-4">
            <div>
              <Label htmlFor="priority">Priority</Label>
              <Input
                id="priority"
                type="number"
                min="0"
                max="100"
                {...form.register('priority', { valueAsNumber: true })}
              />
              <p className="text-sm text-gray-500 mt-1">
                Higher priority rules are applied first
              </p>
            </div>
            <div>
              <Label htmlFor="confidence_threshold">Confidence Threshold</Label>
              <Input
                id="confidence_threshold"
                type="number"
                min="0"
                max="1"
                step="0.1"
                {...form.register('confidence_threshold', { valueAsNumber: true })}
              />
            </div>
          </div>

          <div className="flex items-center space-x-2">
            <Switch
              id="is_active"
              checked={form.watch('is_active')}
              onCheckedChange={(checked) => form.setValue('is_active', checked)}
            />
            <Label htmlFor="is_active">Active</Label>
          </div>

          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={() => onOpenChange(false)}
            >
              Cancel
            </Button>
            <Button type="submit" disabled={isLoading}>
              {isLoading ? <LoadingSpinner /> : (rule ? 'Update Rule' : 'Create Rule')}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}