'use client';

import { useState, useRef, useCallback } from 'react';
import { billsService, OCRResult, BillRequest } from '@/services/bills.service';
import { format } from 'date-fns';
import { ptBR } from 'date-fns/locale';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Textarea } from '@/components/ui/textarea';
import { LoadingSpinner } from '@/components/ui/loading-spinner';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import {
  DocumentArrowUpIcon,
  DocumentTextIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon,
  XMarkIcon,
  PhotoIcon,
} from '@heroicons/react/24/outline';
import { toast } from 'sonner';

interface BillUploadDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSuccess: () => void;
}

type UploadStep = 'upload' | 'processing' | 'review' | 'creating';

export function BillUploadDialog({
  open,
  onOpenChange,
  onSuccess,
}: BillUploadDialogProps) {
  const [step, setStep] = useState<UploadStep>('upload');
  const [file, setFile] = useState<File | null>(null);
  const [ocrResult, setOcrResult] = useState<OCRResult | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Form data for review/edit
  const [formData, setFormData] = useState<Partial<BillRequest>>({
    type: 'payable',
    description: '',
    amount: 0,
    due_date: '',
    customer_supplier: '',
    notes: '',
  });

  const resetState = () => {
    setStep('upload');
    setFile(null);
    setOcrResult(null);
    setFormData({
      type: 'payable',
      description: '',
      amount: 0,
      due_date: '',
      customer_supplier: '',
      notes: '',
    });
  };

  const handleClose = () => {
    resetState();
    onOpenChange(false);
  };

  const handleFileSelect = (selectedFile: File) => {
    // Validate file type
    const allowedTypes = ['application/pdf', 'image/png', 'image/jpeg', 'image/jpg'];
    if (!allowedTypes.includes(selectedFile.type)) {
      toast.error('Formato não suportado. Use PDF, PNG ou JPG.');
      return;
    }

    // Validate file size (5MB)
    if (selectedFile.size > 5 * 1024 * 1024) {
      toast.error('Arquivo muito grande. Máximo: 5MB');
      return;
    }

    setFile(selectedFile);
    processFile(selectedFile);
  };

  const processFile = async (fileToProcess: File) => {
    setStep('processing');

    try {
      const result = await billsService.uploadBoleto(fileToProcess);
      setOcrResult(result);

      // Pre-fill form with extracted data
      setFormData({
        type: 'payable',
        description: result.beneficiary || 'Boleto',
        amount: result.amount ? parseFloat(result.amount) : 0,
        due_date: result.due_date || '',
        customer_supplier: result.beneficiary || '',
        notes: result.barcode ? `Linha digitável: ${result.barcode}` : '',
      });

      setStep('review');

      if (!result.success) {
        toast.warning('Alguns dados não puderam ser extraídos. Por favor, revise.');
      } else if (result.needs_review) {
        toast.info('Dados extraídos. Por favor, revise antes de criar.');
      } else {
        toast.success('Dados extraídos com sucesso!');
      }
    } catch (error: any) {
      console.error('OCR error:', error);
      toast.error(error?.response?.data?.error || 'Erro ao processar arquivo');
      setStep('upload');
    }
  };

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);

    const droppedFile = e.dataTransfer.files[0];
    if (droppedFile) {
      handleFileSelect(droppedFile);
    }
  }, []);

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files && files[0]) {
      handleFileSelect(files[0]);
    }
  };

  const handleCreateBill = async () => {
    if (!formData.description || !formData.amount || !formData.due_date) {
      toast.error('Preencha os campos obrigatórios');
      return;
    }

    setStep('creating');

    try {
      const billData: BillRequest = {
        type: formData.type || 'payable',
        description: formData.description,
        amount: formData.amount,
        due_date: formData.due_date,
        customer_supplier: formData.customer_supplier || '',
        notes: formData.notes || '',
        recurrence: 'once',
      };

      // Add OCR metadata if available
      if (ocrResult) {
        (billData as any).barcode = ocrResult.barcode || '';
        (billData as any).ocr_confidence = ocrResult.confidence || 0;
        (billData as any).ocr_raw_data = ocrResult.extracted_fields || {};
      }

      await billsService.createFromOCR(billData);
      toast.success('Conta criada com sucesso!');
      onSuccess();
      handleClose();
    } catch (error: any) {
      console.error('Create bill error:', error);
      toast.error(error?.response?.data?.error || 'Erro ao criar conta');
      setStep('review');
    }
  };

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 70) return 'bg-green-500';
    if (confidence >= 50) return 'bg-yellow-500';
    return 'bg-red-500';
  };

  const getConfidenceLabel = (confidence: number) => {
    if (confidence >= 70) return 'Alta';
    if (confidence >= 50) return 'Média';
    return 'Baixa';
  };

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="max-w-2xl max-h-[85vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <DocumentArrowUpIcon className="h-5 w-5" />
            Upload de Boleto
          </DialogTitle>
          <DialogDescription>
            {step === 'upload' && 'Faça upload de um boleto (PDF ou imagem) para extrair os dados automaticamente.'}
            {step === 'processing' && 'Processando arquivo...'}
            {step === 'review' && 'Revise os dados extraídos e confirme para criar a conta.'}
            {step === 'creating' && 'Criando conta...'}
          </DialogDescription>
        </DialogHeader>

        {/* Step 1: Upload */}
        {step === 'upload' && (
          <div
            className={`
              border-2 border-dashed rounded-lg p-8 text-center cursor-pointer
              transition-colors duration-200
              ${isDragging
                ? 'border-primary bg-primary/10'
                : 'border-white/20 hover:border-white/40 hover:bg-white/5'
              }
            `}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current?.click()}
          >
            <input
              ref={fileInputRef}
              type="file"
              accept=".pdf,.png,.jpg,.jpeg"
              className="hidden"
              onChange={handleInputChange}
            />
            <PhotoIcon className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
            <p className="text-lg font-medium mb-2">
              Arraste um arquivo ou clique para selecionar
            </p>
            <p className="text-sm text-muted-foreground">
              Formatos aceitos: PDF, PNG, JPG (máx. 5MB)
            </p>
          </div>
        )}

        {/* Step 2: Processing */}
        {step === 'processing' && (
          <div className="py-12 text-center">
            <LoadingSpinner className="w-12 h-12 mx-auto mb-4" />
            <p className="text-lg font-medium mb-2">Processando boleto...</p>
            <p className="text-sm text-muted-foreground">
              Extraindo dados com OCR. Isso pode levar alguns segundos.
            </p>
            {file && (
              <p className="text-xs text-muted-foreground mt-4">
                {file.name} ({(file.size / 1024).toFixed(1)} KB)
              </p>
            )}
          </div>
        )}

        {/* Step 3: Review */}
        {step === 'review' && ocrResult && (
          <div className="space-y-6">
            {/* Confidence indicator */}
            <div className="flex items-center justify-between p-3 bg-muted/50 rounded-lg">
              <div className="flex items-center gap-2">
                {ocrResult.confidence >= 70 ? (
                  <CheckCircleIcon className="h-5 w-5 text-green-500" />
                ) : (
                  <ExclamationTriangleIcon className="h-5 w-5 text-yellow-500" />
                )}
                <span className="text-sm">Confiança da extração:</span>
              </div>
              <div className="flex items-center gap-2">
                <Progress
                  value={ocrResult.confidence}
                  className="w-24 h-2"
                />
                <Badge className={`${getConfidenceColor(ocrResult.confidence)} text-white`}>
                  {getConfidenceLabel(ocrResult.confidence)} ({ocrResult.confidence.toFixed(0)}%)
                </Badge>
              </div>
            </div>

            {/* Form fields */}
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="type">Tipo *</Label>
                <Select
                  value={formData.type}
                  onValueChange={(value) => setFormData(prev => ({ ...prev, type: value as 'payable' | 'receivable' }))}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="payable">A Pagar</SelectItem>
                    <SelectItem value="receivable">A Receber</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label htmlFor="amount">Valor *</Label>
                <Input
                  id="amount"
                  type="number"
                  step="0.01"
                  min="0"
                  value={formData.amount || ''}
                  onChange={(e) => setFormData(prev => ({ ...prev, amount: parseFloat(e.target.value) || 0 }))}
                  placeholder="0,00"
                />
              </div>

              <div className="space-y-2 col-span-2">
                <Label htmlFor="description">Descrição *</Label>
                <Input
                  id="description"
                  value={formData.description}
                  onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
                  placeholder="Descrição da conta"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="due_date">Data de Vencimento *</Label>
                <Input
                  id="due_date"
                  type="date"
                  value={formData.due_date}
                  onChange={(e) => setFormData(prev => ({ ...prev, due_date: e.target.value }))}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="customer_supplier">Beneficiário/Fornecedor</Label>
                <Input
                  id="customer_supplier"
                  value={formData.customer_supplier}
                  onChange={(e) => setFormData(prev => ({ ...prev, customer_supplier: e.target.value }))}
                  placeholder="Nome do beneficiário"
                />
              </div>

              <div className="space-y-2 col-span-2">
                <Label htmlFor="notes">Observações</Label>
                <Textarea
                  id="notes"
                  value={formData.notes}
                  onChange={(e) => setFormData(prev => ({ ...prev, notes: e.target.value }))}
                  placeholder="Observações adicionais..."
                  rows={3}
                />
              </div>
            </div>

            {/* Extracted barcode info */}
            {ocrResult.barcode && (
              <div className="p-3 bg-muted/30 rounded-lg">
                <p className="text-xs text-muted-foreground mb-1">Linha digitável extraída:</p>
                <p className="font-mono text-sm break-all">{ocrResult.barcode}</p>
              </div>
            )}
          </div>
        )}

        {/* Step 4: Creating */}
        {step === 'creating' && (
          <div className="py-12 text-center">
            <LoadingSpinner className="w-12 h-12 mx-auto mb-4" />
            <p className="text-lg font-medium">Criando conta...</p>
          </div>
        )}

        {/* Footer */}
        <div className="flex justify-between pt-4 border-t border-white/10">
          <Button variant="outline" onClick={handleClose}>
            Cancelar
          </Button>

          {step === 'review' && (
            <div className="flex gap-2">
              <Button
                variant="outline"
                onClick={() => {
                  setStep('upload');
                  setFile(null);
                  setOcrResult(null);
                }}
              >
                Novo Upload
              </Button>
              <Button onClick={handleCreateBill}>
                Criar Conta
              </Button>
            </div>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}
