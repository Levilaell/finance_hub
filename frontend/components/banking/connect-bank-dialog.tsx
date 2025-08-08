'use client';

import { useState } from 'react';
import { Search, Building2, X } from 'lucide-react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Skeleton } from '@/components/ui/skeleton';
import { useQuery } from '@tanstack/react-query';
import { bankingService } from '@/services/banking.service';
import { usePluggyConnect } from '@/hooks/use-pluggy-connect';
import type { PluggyConnector as Institution } from '@/types/banking.types';
import { cn } from '@/lib/utils';

interface ConnectBankDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSuccess?: () => void;
}

export function ConnectBankDialog({
  open,
  onOpenChange,
  onSuccess,
}: ConnectBankDialogProps) {
  const [search, setSearch] = useState('');
  const [selectedInstitution, setSelectedInstitution] = useState<Institution | null>(null);

  const { data: institutions, isLoading } = useQuery({
    queryKey: ['connectors', search],
    queryFn: async () => {
      const response = await bankingService.getConnectors();
      if (search) {
        return response.filter(connector => 
          connector.name.toLowerCase().includes(search.toLowerCase())
        );
      }
      return response;
    },
    enabled: open,
  });

  const { openConnect, isConnecting } = usePluggyConnect({
    onSuccess: () => {
      onOpenChange(false);
      onSuccess?.();
    },
    onExit: () => {
      setSelectedInstitution(null);
    },
  });

  const handleConnect = () => {
    if (selectedInstitution) {
      openConnect();
    }
  };

  const filteredInstitutions = institutions?.filter(inst =>
    inst.name.toLowerCase().includes(search.toLowerCase())
  ) || [];

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle>Conectar conta bancária</DialogTitle>
          <DialogDescription>
            Selecione sua instituição financeira para conectar de forma segura via Open Banking
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          {/* Search */}
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="Buscar banco ou instituição..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="pl-10"
            />
          </div>

          {/* Institution List */}
          <ScrollArea className="h-[400px] rounded-md border p-4">
            {isLoading ? (
              <div className="space-y-3">
                {Array.from({ length: 6 }).map((_, i) => (
                  <div key={i} className="flex items-center gap-3 p-3">
                    <Skeleton className="h-12 w-12 rounded-lg" />
                    <Skeleton className="h-5 w-32" />
                  </div>
                ))}
              </div>
            ) : filteredInstitutions.length === 0 ? (
              <div className="flex flex-col items-center justify-center h-full text-center">
                <Building2 className="h-12 w-12 text-muted-foreground mb-3" />
                <p className="text-muted-foreground">
                  {search ? 'Nenhuma instituição encontrada' : 'Carregando instituições...'}
                </p>
              </div>
            ) : (
              <div className="grid grid-cols-2 gap-3">
                {filteredInstitutions.map((institution) => (
                  <button
                    key={institution.pluggy_id}
                    onClick={() => setSelectedInstitution(institution)}
                    className={cn(
                      "flex items-center gap-3 p-3 rounded-lg border transition-all hover:shadow-sm",
                      selectedInstitution?.pluggy_id === institution.pluggy_id
                        ? "border-primary bg-primary/5"
                        : "border-gray-200 hover:border-gray-300"
                    )}
                  >
                    {institution.image_url ? (
                      <img
                        src={institution.image_url}
                        alt={institution.name}
                        className="w-12 h-12 rounded-lg object-contain bg-white p-1 border"
                      />
                    ) : (
                      <div 
                        className="w-12 h-12 rounded-lg flex items-center justify-center text-white font-bold"
                        style={{ backgroundColor: institution.primary_color || '#6366f1' }}
                      >
                        {institution.name.charAt(0)}
                      </div>
                    )}
                    <div className="text-left flex-1">
                      <p className="font-medium text-sm">{institution.name}</p>
                      <p className="text-xs text-muted-foreground capitalize">{institution.type}</p>
                    </div>
                  </button>
                ))}
              </div>
            )}
          </ScrollArea>

          {/* Footer */}
          <div className="flex justify-between items-center pt-4 border-t">
            <p className="text-sm text-muted-foreground">
              Conexão segura via Open Banking
            </p>
            <div className="flex gap-2">
              <Button
                variant="outline"
                onClick={() => onOpenChange(false)}
                disabled={isConnecting}
              >
                Cancelar
              </Button>
              <Button
                onClick={handleConnect}
                disabled={!selectedInstitution || isConnecting}
              >
                {isConnecting ? 'Conectando...' : 'Conectar'}
              </Button>
            </div>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}