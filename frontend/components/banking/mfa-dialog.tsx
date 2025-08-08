'use client';

import { useState } from 'react';
import { Shield } from 'lucide-react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';

interface MFADialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSubmit: (code: string) => void;
  isLoading?: boolean;
  institutionName?: string;
}

export function MFADialog({
  open,
  onOpenChange,
  onSubmit,
  isLoading = false,
  institutionName = 'sua instituição'
}: MFADialogProps) {
  const [code, setCode] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (code.trim()) {
      onSubmit(code);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        <form onSubmit={handleSubmit}>
          <DialogHeader>
            <div className="flex items-center gap-3 mb-4">
              <div className="p-2 bg-blue-50 rounded-full">
                <Shield className="h-6 w-6 text-blue-600" />
              </div>
              <div>
                <DialogTitle>Verificação em duas etapas</DialogTitle>
                <DialogDescription>
                  {institutionName} está solicitando um código de verificação
                </DialogDescription>
              </div>
            </div>
          </DialogHeader>

          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="mfa-code">Código de verificação</Label>
              <Input
                id="mfa-code"
                placeholder="Digite o código recebido"
                value={code}
                onChange={(e) => setCode(e.target.value)}
                autoComplete="off"
                autoFocus
                disabled={isLoading}
              />
            </div>
            
            <p className="text-sm text-muted-foreground">
              Digite o código de verificação enviado por SMS, e-mail ou gerado no aplicativo 
              de autenticação do banco.
            </p>
          </div>

          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={() => onOpenChange(false)}
              disabled={isLoading}
            >
              Cancelar
            </Button>
            <Button
              type="submit"
              disabled={!code.trim() || isLoading}
            >
              {isLoading ? 'Verificando...' : 'Verificar'}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}