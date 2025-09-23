'use client';

import Image from 'next/image';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  ArrowPathIcon,
  BuildingLibraryIcon,
  TrashIcon,
} from '@heroicons/react/24/outline';

interface BankAccountCardProps {
  // Pure visual component - no data processing
}

export function BankAccountCard() {
  return (
    <Card className="hover:shadow-lg transition-all duration-300">
      <CardContent className="p-6 space-y-4">
        {/* Header Row: Bank Icon, Name, and Actions */}
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-3">
            {/* Bank Icon */}
            <div className="w-10 h-10 bg-gray-100 rounded flex items-center justify-center">
              <BuildingLibraryIcon className="h-6 w-6 text-gray-400" />
            </div>
            
            {/* Bank Name and Account Number */}
            <div>
              <h3 className="font-semibold text-base">
                Banco Exemplo
              </h3>
              <p className="text-sm text-muted-foreground mt-0.5">
                ****1234
              </p>
            </div>
          </div>

          {/* Delete Button */}
          <Button
            variant="ghost"
            size="icon"
            className="h-8 w-8 text-red-600 hover:text-red-700"
          >
            <TrashIcon className="h-4 w-4" />
          </Button>
        </div>

        {/* Type and Status Row */}
        <div className="flex items-center justify-between">
          <span className="text-sm text-muted-foreground">
            Conta Bancária
          </span>
          <Badge 
            variant="secondary" 
            className="bg-green-100 text-green-800"
          >
            Conectado
          </Badge>
        </div>

        {/* Balance */}
        <div className="py-2">
          <p className="text-sm text-muted-foreground mb-1">Saldo</p>
          <p className="text-3xl font-bold">
            R$ 1.234,56
          </p>
        </div>

        {/* Last Update */}
        <div className="flex items-center justify-between pt-3 border-t">
          <p className="text-sm text-muted-foreground">
            Atualizado há 2 horas
          </p>
          <Button
            variant="outline"
            size="sm"
          >
            <ArrowPathIcon className="h-4 w-4 mr-1.5" />
            Sincronizar
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}