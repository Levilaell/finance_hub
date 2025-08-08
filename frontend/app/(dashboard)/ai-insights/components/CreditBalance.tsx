'use client';

import { useState } from 'react';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { CreditPurchaseModal } from './CreditPurchaseModal';
import { Zap, ShoppingCart, Info } from 'lucide-react';
import { testId, TEST_IDS } from '@/utils/test-helpers';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip';

interface CreditBalanceProps {
  balance: number;
  monthlyAllowance: number;
  bonusCredits?: number;
}

export function CreditBalance({ balance, monthlyAllowance, bonusCredits = 0 }: CreditBalanceProps) {
  const [showPurchaseModal, setShowPurchaseModal] = useState(false);
  
  const usedCredits = monthlyAllowance - balance + bonusCredits;
  const percentageUsed = monthlyAllowance > 0 ? (usedCredits / monthlyAllowance) * 100 : 0;

  return (
    <>
      <Card className="p-6 glass hover-lift transition-all duration-300">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-3">
            <div className="h-10 w-10 rounded-full bg-gradient-primary flex items-center justify-center shadow-md">
              <Zap className="h-5 w-5 text-white" />
            </div>
            <div>
              <h3 className="font-semibold text-white">Créditos AI</h3>
              <p className="text-sm text-muted-foreground">Saldo atual</p>
            </div>
          </div>
          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger>
                <Info className="h-4 w-4 text-muted-foreground" />
              </TooltipTrigger>
              <TooltipContent>
                <p>Créditos são usados para interações com AI</p>
                <p className="text-xs mt-1">1 crédito = 1 mensagem simples</p>
              </TooltipContent>
            </Tooltip>
          </TooltipProvider>
        </div>

        <div className="space-y-4">
          {/* Balance display */}
          <div>
            <div className="flex items-baseline justify-between mb-2">
              <span className="text-3xl font-bold text-white" {...testId(TEST_IDS.aiInsights.creditBalance)}>{balance}</span>
              <span className="text-sm text-muted-foreground">
                de {monthlyAllowance} mensais
              </span>
            </div>
            {bonusCredits > 0 && (
              <p className="text-sm text-success">
                +{bonusCredits} créditos bônus
              </p>
            )}
          </div>

          {/* Usage progress */}
          <div>
            <div className="flex justify-between text-sm mb-1">
              <span className="text-muted-foreground">Uso mensal</span>
              <span className="text-foreground font-medium">
                {Math.round(percentageUsed)}%
              </span>
            </div>
            <Progress value={percentageUsed} className="h-2" />
          </div>

          {/* Low credits warning */}
          {balance < monthlyAllowance * 0.2 && (
            <div className="bg-warning/10 border border-warning/20 rounded-md p-3">
              <p className="text-sm text-warning">
                Créditos baixos! Considere comprar mais para continuar usando.
              </p>
            </div>
          )}

          {/* Purchase button */}
          <Button
            onClick={() => setShowPurchaseModal(true)}
            className={`w-full transition-all duration-300 hover-lift ${
              balance < monthlyAllowance * 0.2
                ? 'btn-gradient text-white shadow-md hover:shadow-lg'
                : 'border-primary/20 text-primary hover:bg-gradient-primary hover:text-white hover:border-transparent'
            }`}
            variant={balance < monthlyAllowance * 0.2 ? 'default' : 'outline'}
            {...testId(TEST_IDS.aiInsights.purchaseCreditsButton)}
          >
            <ShoppingCart className="h-4 w-4 mr-2" />
            Comprar Créditos
          </Button>
        </div>
      </Card>

      <CreditPurchaseModal
        open={showPurchaseModal}
        onClose={() => setShowPurchaseModal(false)}
      />
    </>
  );
}