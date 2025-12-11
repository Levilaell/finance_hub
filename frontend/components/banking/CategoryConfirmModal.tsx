'use client';

import { useState, useEffect } from 'react';
import { format } from 'date-fns';
import { ptBR } from 'date-fns/locale';
import { bankingService } from '@/services/banking.service';
import { Transaction, Category, SimilarTransaction } from '@/types/banking';
import { formatCurrency } from '@/lib/utils';
import { LoadingSpinner } from '@/components/ui/loading-spinner';
import { Button } from '@/components/ui/button';
import { Checkbox } from '@/components/ui/checkbox';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import {
  CheckIcon,
  SparklesIcon,
  DocumentDuplicateIcon,
} from '@heroicons/react/24/outline';
import { toast } from 'sonner';

interface CategoryConfirmModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  transaction: Transaction | null;
  selectedCategory: Category | null;
  onConfirm: (result: {
    appliedToSimilar: number;
    ruleCreated: boolean;
  }) => void;
}

export function CategoryConfirmModal({
  open,
  onOpenChange,
  transaction,
  selectedCategory,
  onConfirm,
}: CategoryConfirmModalProps) {
  const [isLoading, setIsLoading] = useState(false);
  const [isApplying, setIsApplying] = useState(false);
  const [similarTransactions, setSimilarTransactions] = useState<SimilarTransaction[]>([]);
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const [createRule, setCreateRule] = useState(true);
  const [suggestedPattern, setSuggestedPattern] = useState('');

  // Fetch similar transactions when modal opens
  useEffect(() => {
    if (open && transaction) {
      fetchSimilarTransactions();
    } else {
      // Reset state when modal closes
      setSimilarTransactions([]);
      setSelectedIds(new Set());
      setCreateRule(true);
    }
  }, [open, transaction]);

  const fetchSimilarTransactions = async () => {
    if (!transaction) return;

    setIsLoading(true);
    try {
      const response = await bankingService.getSimilarTransactions(transaction.id);
      setSimilarTransactions(response.transactions);
      setSuggestedPattern(response.suggested_pattern);
      // Pre-select all similar transactions
      setSelectedIds(new Set(response.transactions.map(t => t.id)));
    } catch (error) {
      console.error('Error fetching similar transactions:', error);
      toast.error('Erro ao buscar transacoes similares');
    } finally {
      setIsLoading(false);
    }
  };

  const toggleTransaction = (id: string) => {
    setSelectedIds(prev => {
      const next = new Set(prev);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      return next;
    });
  };

  const selectAll = () => {
    setSelectedIds(new Set(similarTransactions.map(t => t.id)));
  };

  const deselectAll = () => {
    setSelectedIds(new Set());
  };

  const handleApply = async () => {
    if (!transaction || !selectedCategory) return;

    setIsApplying(true);
    try {
      const result = await bankingService.updateTransactionCategoryWithRule(
        transaction.id,
        {
          user_category_id: selectedCategory.id,
          apply_to_similar: selectedIds.size > 0,
          create_rule: createRule,
          similar_transaction_ids: Array.from(selectedIds),
        }
      );

      // Show success message
      const messages: string[] = [];
      messages.push('Categoria atualizada');
      if (result.applied_to_similar > 0) {
        messages.push(`${result.applied_to_similar} transacoes similares atualizadas`);
      }
      if (result.rule_created) {
        messages.push('Regra criada para futuras transacoes');
      }
      toast.success(messages.join('. '));

      onConfirm({
        appliedToSimilar: result.applied_to_similar,
        ruleCreated: result.rule_created,
      });
      onOpenChange(false);
    } catch (error) {
      console.error('Error applying category:', error);
      toast.error('Erro ao aplicar categoria');
    } finally {
      setIsApplying(false);
    }
  };

  const handleApplyOnlyThis = async () => {
    if (!transaction || !selectedCategory) return;

    setIsApplying(true);
    try {
      await bankingService.updateTransactionCategory(transaction.id, selectedCategory.id);
      toast.success('Categoria atualizada');
      onConfirm({
        appliedToSimilar: 0,
        ruleCreated: false,
      });
      onOpenChange(false);
    } catch (error) {
      console.error('Error applying category:', error);
      toast.error('Erro ao aplicar categoria');
    } finally {
      setIsApplying(false);
    }
  };

  const getMatchTypeLabel = (matchType: string) => {
    switch (matchType) {
      case 'merchant':
        return 'Mesmo fornecedor';
      case 'prefix':
        return 'Descricao similar';
      case 'fuzzy':
        return 'Texto parecido';
      default:
        return matchType;
    }
  };

  if (!transaction || !selectedCategory) return null;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl max-h-[85vh] overflow-hidden flex flex-col">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <SparklesIcon className="h-5 w-5 text-blue-500" />
            Transacoes Similares Encontradas
          </DialogTitle>
          <DialogDescription>
            Deseja aplicar a categoria{' '}
            <span className="font-medium text-foreground inline-flex items-center gap-1">
              <span
                className="inline-flex items-center justify-center w-4 h-4 rounded text-xs"
                style={{ backgroundColor: selectedCategory.color }}
              >
                {selectedCategory.icon}
              </span>
              {selectedCategory.name}
            </span>{' '}
            tambem a estas transacoes similares?
          </DialogDescription>
        </DialogHeader>

        <div className="flex-1 overflow-y-auto py-4">
          {isLoading ? (
            <div className="flex items-center justify-center py-8">
              <LoadingSpinner />
            </div>
          ) : similarTransactions.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              <DocumentDuplicateIcon className="h-12 w-12 mx-auto mb-3 opacity-50" />
              <p>Nenhuma transacao similar encontrada.</p>
              <p className="text-sm mt-1">A categoria sera aplicada apenas a esta transacao.</p>
            </div>
          ) : (
            <div className="space-y-4">
              {/* Selection controls */}
              <div className="flex items-center justify-between text-sm">
                <span className="text-muted-foreground">
                  {selectedIds.size} de {similarTransactions.length} selecionadas
                </span>
                <div className="flex gap-2">
                  <Button variant="ghost" size="sm" onClick={selectAll}>
                    Selecionar todas
                  </Button>
                  <Button variant="ghost" size="sm" onClick={deselectAll}>
                    Limpar selecao
                  </Button>
                </div>
              </div>

              {/* Transactions list */}
              <div className="space-y-2 max-h-[300px] overflow-y-auto pr-2">
                {similarTransactions.map((tx) => (
                  <div
                    key={tx.id}
                    className={`
                      flex items-center gap-3 p-3 rounded-lg border cursor-pointer transition-colors
                      ${selectedIds.has(tx.id)
                        ? 'bg-blue-500/10 border-blue-500/30'
                        : 'bg-background border-border hover:bg-accent/50'
                      }
                    `}
                    onClick={() => toggleTransaction(tx.id)}
                  >
                    <Checkbox
                      checked={selectedIds.has(tx.id)}
                      onCheckedChange={() => toggleTransaction(tx.id)}
                    />
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between gap-2">
                        <span className="font-medium truncate">{tx.description}</span>
                        <span className="text-sm font-semibold whitespace-nowrap">
                          {formatCurrency(parseFloat(tx.amount))}
                        </span>
                      </div>
                      <div className="flex items-center gap-2 text-xs text-muted-foreground mt-1">
                        <span>{format(new Date(tx.date), 'dd/MM/yyyy', { locale: ptBR })}</span>
                        <span>•</span>
                        <span className="text-blue-500">{getMatchTypeLabel(tx.match_type)}</span>
                        <span>•</span>
                        <span>{Math.round(tx.score * 100)}% similar</span>
                      </div>
                    </div>
                    {selectedIds.has(tx.id) && (
                      <CheckIcon className="h-4 w-4 text-blue-500 flex-shrink-0" />
                    )}
                  </div>
                ))}
              </div>

              {/* Create rule option */}
              <div className="border-t pt-4 mt-4">
                <label
                  className="flex items-start gap-3 cursor-pointer p-3 rounded-lg hover:bg-accent/50 transition-colors"
                  onClick={() => setCreateRule(!createRule)}
                >
                  <Checkbox
                    checked={createRule}
                    onCheckedChange={(checked) => setCreateRule(!!checked)}
                  />
                  <div>
                    <div className="font-medium">Criar regra para futuras transacoes</div>
                    <div className="text-sm text-muted-foreground mt-0.5">
                      Transacoes com padrao similar a{' '}
                      <code className="bg-muted px-1 rounded">{suggestedPattern || transaction.description.substring(0, 15)}</code>{' '}
                      serao automaticamente categorizadas
                    </div>
                  </div>
                </label>
              </div>
            </div>
          )}
        </div>

        <DialogFooter className="flex-shrink-0 gap-2 sm:gap-2">
          <Button variant="ghost" onClick={() => onOpenChange(false)} disabled={isApplying}>
            Cancelar
          </Button>
          <Button
            variant="outline"
            onClick={handleApplyOnlyThis}
            disabled={isApplying}
          >
            Aplicar so nesta
          </Button>
          {similarTransactions.length > 0 && (
            <Button
              onClick={handleApply}
              disabled={isApplying || (selectedIds.size === 0 && !createRule)}
            >
              {isApplying ? (
                <>
                  <LoadingSpinner className="w-4 h-4 mr-2" />
                  Aplicando...
                </>
              ) : (
                <>
                  Aplicar{selectedIds.size > 0 && ` a ${selectedIds.size + 1}`}
                  {createRule && ' + criar regra'}
                </>
              )}
            </Button>
          )}
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
