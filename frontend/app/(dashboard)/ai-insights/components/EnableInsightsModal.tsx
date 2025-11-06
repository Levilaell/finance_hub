'use client';

import { useState } from 'react';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { aiInsightsService, EnableAIInsightsRequest } from '@/services/ai-insights.service';
import { LoadingSpinner } from '@/components/ui/loading-spinner';

interface EnableInsightsModalProps {
  open: boolean;
  onClose: () => void;
  onSuccess: () => void;
}

const companyTypes = [
  { value: 'mei', label: 'MEI' },
  { value: 'me', label: 'Microempresa' },
  { value: 'epp', label: 'Empresa de Pequeno Porte' },
  { value: 'ltda', label: 'Limitada' },
  { value: 'sa', label: 'Sociedade Anônima' },
  { value: 'other', label: 'Outros' },
];

const businessSectors = [
  { value: 'retail', label: 'Comércio' },
  { value: 'services', label: 'Serviços' },
  { value: 'industry', label: 'Indústria' },
  { value: 'technology', label: 'Tecnologia' },
  { value: 'healthcare', label: 'Saúde' },
  { value: 'education', label: 'Educação' },
  { value: 'food', label: 'Alimentação' },
  { value: 'construction', label: 'Construção' },
  { value: 'automotive', label: 'Automotivo' },
  { value: 'agriculture', label: 'Agricultura' },
  { value: 'other', label: 'Outros' },
];

export function EnableInsightsModal({ open, onClose, onSuccess }: EnableInsightsModalProps) {
  const [formData, setFormData] = useState<EnableAIInsightsRequest>({
    company_type: '',
    business_sector: ''
  });
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!formData.company_type || !formData.business_sector) {
      setError('Por favor, preencha todos os campos');
      return;
    }

    setIsLoading(true);

    try {
      await aiInsightsService.enable(formData);
      onSuccess();
      onClose();
    } catch (err: any) {
      setError(err.response?.data?.error || 'Erro ao habilitar insights');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Ativar Insights com IA</DialogTitle>
          <DialogDescription>
            Para gerar insights personalizados, precisamos de algumas informações sobre sua empresa.
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Company Type */}
          <div className="space-y-2">
            <Label htmlFor="company_type">Tipo de Empresa</Label>
            <Select
              value={formData.company_type}
              onValueChange={(value) => setFormData({ ...formData, company_type: value })}
            >
              <SelectTrigger id="company_type">
                <SelectValue placeholder="Selecione o tipo" />
              </SelectTrigger>
              <SelectContent>
                {companyTypes.map((type) => (
                  <SelectItem key={type.value} value={type.value}>
                    {type.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* Business Sector */}
          <div className="space-y-2">
            <Label htmlFor="business_sector">Setor de Atuação</Label>
            <Select
              value={formData.business_sector}
              onValueChange={(value) => setFormData({ ...formData, business_sector: value })}
            >
              <SelectTrigger id="business_sector">
                <SelectValue placeholder="Selecione o setor" />
              </SelectTrigger>
              <SelectContent>
                {businessSectors.map((sector) => (
                  <SelectItem key={sector.value} value={sector.value}>
                    {sector.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* Error Message */}
          {error && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-3">
              <p className="text-sm text-red-600">{error}</p>
            </div>
          )}

          {/* Info */}
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
            <p className="text-sm text-blue-800">
              ℹ️ Sua primeira análise será gerada automaticamente em alguns instantes após ativar.
            </p>
          </div>

          {/* Actions */}
          <div className="flex gap-3 justify-end">
            <Button
              type="button"
              variant="outline"
              onClick={onClose}
              disabled={isLoading}
            >
              Cancelar
            </Button>
            <Button type="submit" disabled={isLoading}>
              {isLoading ? (
                <>
                  <LoadingSpinner />
                  <span className="ml-2">Ativando...</span>
                </>
              ) : (
                'Ativar Insights'
              )}
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
}
