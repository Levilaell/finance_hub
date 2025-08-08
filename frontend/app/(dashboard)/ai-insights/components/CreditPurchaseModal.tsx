'use client';

import { useState } from 'react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Zap, TrendingUp } from 'lucide-react';
import { formatCurrency } from '@/lib/utils';
import toast from 'react-hot-toast';

interface CreditPurchaseModalProps {
  open: boolean;
  onClose: () => void;
}

const creditPackages = [
  {
    id: 'pack_10',
    credits: 10,
    price: 4.90,
    pricePerCredit: 0.49,
  },
  {
    id: 'pack_50',
    credits: 50,
    price: 19.90,
    pricePerCredit: 0.398,
    savings: '19%',
  },
  {
    id: 'pack_100',
    credits: 100,
    price: 34.90,
    pricePerCredit: 0.349,
    savings: '29%',
  },
  {
    id: 'pack_500',
    credits: 500,
    price: 149.90,
    pricePerCredit: 0.299,
    savings: '39%',
    bestValue: true,
  },
  {
    id: 'pack_1000',
    credits: 1000,
    price: 249.90,
    pricePerCredit: 0.249,
    savings: '49%',
  },
  {
    id: 'pack_5000',
    credits: 5000,
    price: 999.90,
    pricePerCredit: 0.199,
    savings: '59%',
    enterprise: true,
  },
];

export function CreditPurchaseModal({ open, onClose }: CreditPurchaseModalProps) {
  const [selectedPackage, setSelectedPackage] = useState('pack_100');
  const [loading, setLoading] = useState(false);

  const handlePurchase = async () => {
    setLoading(true);
    
    try {
      // TODO: Implement purchase API call
      await new Promise(resolve => setTimeout(resolve, 2000)); // Simulate API call
      
      toast.success('Seus créditos foram adicionados à sua conta.');
      
      onClose();
    } catch (error) {
      toast.error('Não foi possível processar sua compra. Tente novamente.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Zap className="h-5 w-5 text-blue-600" />
            Comprar Créditos AI
          </DialogTitle>
          <DialogDescription>
            Escolha um pacote de créditos para continuar usando o assistente AI.
            Créditos não expiram e podem ser usados a qualquer momento.
          </DialogDescription>
        </DialogHeader>

        <div className="py-6">
          <RadioGroup
            value={selectedPackage}
            onValueChange={setSelectedPackage}
            className="grid grid-cols-1 md:grid-cols-2 gap-4"
          >
            {creditPackages.map((pkg) => (
              <div key={pkg.id}>
                <RadioGroupItem
                  value={pkg.id}
                  id={pkg.id}
                  className="peer sr-only"
                />
                <Label
                  htmlFor={pkg.id}
                  className="flex flex-col cursor-pointer rounded-lg border-2 border-gray-200 p-4 hover:border-blue-500 peer-data-[state=checked]:border-blue-600 peer-data-[state=checked]:bg-blue-50 transition-all"
                >
                  <div className="flex items-start justify-between mb-2">
                    <div>
                      <p className="font-semibold text-lg">
                        {pkg.credits} créditos
                      </p>
                      <p className="text-sm text-gray-500">
                        {formatCurrency(pkg.pricePerCredit)}/crédito
                      </p>
                    </div>
                    <div className="text-right">
                      <p className="font-bold text-xl">
                        {formatCurrency(pkg.price)}
                      </p>
                      {pkg.savings && (
                        <Badge variant="secondary" className="mt-1">
                          <TrendingUp className="h-3 w-3 mr-1" />
                          {pkg.savings} OFF
                        </Badge>
                      )}
                    </div>
                  </div>
                  {pkg.bestValue && (
                    <Badge className="w-fit">
                      Melhor custo-benefício
                    </Badge>
                  )}
                  {pkg.enterprise && (
                    <Badge variant="outline" className="w-fit">
                      Empresarial
                    </Badge>
                  )}
                </Label>
              </div>
            ))}
          </RadioGroup>
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={onClose}>
            Cancelar
          </Button>
          <Button onClick={handlePurchase} disabled={loading}>
            {loading ? 'Processando...' : 'Comprar Agora'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}