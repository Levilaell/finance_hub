'use client';

import { useState, useEffect, FormEvent } from 'react';
import { toast } from 'sonner';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Clock, Shield, Info } from 'lucide-react';
import type { MFAParameter } from '@/types/banking';

interface MFAPromptProps {
  parameter: MFAParameter;
  onSubmit: (value: string) => Promise<void>;
  onCancel: () => void;
  institutionName: string;
}

/**
 * MFA Prompt Component
 * Displays a form to collect MFA code from user
 * Ref: https://docs.pluggy.ai/docs/connect-an-account
 *
 * This component handles 2-step MFA scenarios where:
 * - User logs in successfully
 * - Institution sends MFA code (SMS, email, app)
 * - User needs to input the code to complete authentication
 */
export function MFAPrompt({
  parameter,
  onSubmit,
  onCancel,
  institutionName,
}: MFAPromptProps) {
  const [mfaValue, setMfaValue] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [timeRemaining, setTimeRemaining] = useState<number | null>(null);

  // Calculate time remaining until expiration
  useEffect(() => {
    if (!parameter.expiresAt) return;

    const updateTimer = () => {
      const expiresAt = new Date(parameter.expiresAt!).getTime();
      const now = Date.now();
      const remaining = Math.max(0, Math.floor((expiresAt - now) / 1000));
      setTimeRemaining(remaining);

      if (remaining === 0) {
        toast.error('Código MFA expirado. Por favor, tente novamente.');
      }
    };

    updateTimer();
    const interval = setInterval(updateTimer, 1000);

    return () => clearInterval(interval);
  }, [parameter.expiresAt]);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();

    // Validate input
    if (!mfaValue.trim()) {
      toast.error('Por favor, insira o código');
      return;
    }

    // Validate against regex if provided
    if (parameter.validation) {
      const regex = new RegExp(parameter.validation);
      if (!regex.test(mfaValue)) {
        toast.error(parameter.validationMessage || 'Código inválido');
        return;
      }
    }

    // Check if expired
    if (timeRemaining === 0) {
      toast.error('Código MFA expirado. Por favor, tente novamente.');
      return;
    }

    setIsSubmitting(true);

    try {
      await onSubmit(mfaValue);
      toast.success('Código MFA enviado com sucesso!');
    } catch (error: any) {
      toast.error(error.message || 'Erro ao enviar código MFA');
      setIsSubmitting(false);
    }
  };

  const formatTime = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  return (
    <div className="space-y-4">
      <div className="flex items-start gap-3">
        <Shield className="h-5 w-5 text-orange-500 mt-0.5" />
        <div className="flex-1">
          <h3 className="font-semibold text-lg">
            Autenticação de Dois Fatores Necessária
          </h3>
          <p className="text-sm text-muted-foreground mt-1">
            {institutionName}
          </p>
        </div>
      </div>

      <Alert>
        <Info className="h-4 w-4" />
        <AlertDescription>
          Um código de verificação foi enviado. Por favor, verifique seu{' '}
          {parameter.label.toLowerCase().includes('sms') ? 'SMS' :
           parameter.label.toLowerCase().includes('email') ? 'e-mail' :
           parameter.label.toLowerCase().includes('app') ? 'aplicativo' :
           'método de autenticação'} e insira o código abaixo.
        </AlertDescription>
      </Alert>

      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="space-y-2">
          <label htmlFor="mfa-code" className="text-sm font-medium">
            {parameter.label}
          </label>
          <Input
            id="mfa-code"
            type={parameter.type === 'number' ? 'text' : parameter.type}
            inputMode={parameter.type === 'number' ? 'numeric' : 'text'}
            placeholder={parameter.placeholder || 'Digite o código'}
            value={mfaValue}
            onChange={(e) => setMfaValue(e.target.value)}
            disabled={isSubmitting || timeRemaining === 0}
            maxLength={parameter.validation ? parseInt(parameter.validation.match(/\{(\d+)\}$/)?.[1] || '10') : undefined}
            className="text-center text-lg tracking-wider font-mono"
            autoFocus
            autoComplete="one-time-code"
          />
          {parameter.validationMessage && (
            <p className="text-xs text-muted-foreground">
              {parameter.validationMessage}
            </p>
          )}
        </div>

        {timeRemaining !== null && (
          <div className="flex items-center gap-2 text-sm">
            <Clock className="h-4 w-4" />
            <span className={timeRemaining < 60 ? 'text-red-500 font-medium' : 'text-muted-foreground'}>
              Tempo restante: {formatTime(timeRemaining)}
            </span>
          </div>
        )}

        <div className="flex gap-2">
          <Button
            type="button"
            variant="outline"
            onClick={onCancel}
            disabled={isSubmitting}
            className="flex-1"
          >
            Cancelar
          </Button>
          <Button
            type="submit"
            disabled={isSubmitting || timeRemaining === 0 || !mfaValue.trim()}
            className="flex-1"
          >
            {isSubmitting ? 'Enviando...' : 'Confirmar'}
          </Button>
        </div>
      </form>

      <div className="text-xs text-muted-foreground space-y-1">
        <p>• Não recebeu o código? Aguarde alguns segundos ou tente novamente.</p>
        <p>• O código expira após alguns minutos por segurança.</p>
      </div>
    </div>
  );
}
