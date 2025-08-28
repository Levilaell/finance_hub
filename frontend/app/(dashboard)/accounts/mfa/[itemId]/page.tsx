'use client';

import { useState, useEffect, useCallback } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { LoadingSpinner } from '@/components/ui/loading-spinner';
import { Shield, AlertCircle, CheckCircle } from 'lucide-react';
import Image from 'next/image';
import { bankingService } from '@/services/banking.service';
import { toast } from 'sonner';

interface MFAParameter {
  name: string;
  type: string;
  label: string;
  placeholder: string;
  validation?: any;
  assistiveText?: string;
  optional?: boolean;
}

interface MFAStatus {
  requires_mfa: boolean;
  status: string;
  parameter?: MFAParameter;
  connector?: {
    id: string;
    name: string;
    image_url: string;
  };
  message?: string;
}

export default function MFAPage() {
  const params = useParams();
  const router = useRouter();
  const itemId = params?.itemId as string;

  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [mfaStatus, setMfaStatus] = useState<MFAStatus | null>(null);
  const [mfaValue, setMfaValue] = useState('');
  const [error, setError] = useState('');

  const fetchMFAStatus = useCallback(async () => {
    try {
      setLoading(true);
      const response = await bankingService.getMFAStatus(itemId);
      setMfaStatus(response.data);

      if (!response.data.requires_mfa) {
        toast.info('Esta conexão não requer autenticação adicional');
        router.push('/accounts');
      }
    } catch (error: any) {
      console.error('Failed to fetch MFA status:', error);
      toast.error('Erro ao carregar status de autenticação');
      setError(error.response?.data?.error || 'Erro ao carregar informações');
    } finally {
      setLoading(false);
    }
  }, [itemId, router]);

  useEffect(() => {
    if (itemId) {
      fetchMFAStatus();
    }
  }, [itemId, fetchMFAStatus]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!mfaValue.trim()) {
      setError('Por favor, insira o código de verificação');
      return;
    }

    try {
      setSubmitting(true);
      setError('');

      const response = await bankingService.sendMFA(itemId, {
        value: mfaValue,
        [mfaStatus?.parameter?.name || 'token']: mfaValue
      });

      if (response.data.success) {
        toast.success('Código enviado com sucesso!');
        
        // Check if additional MFA is required
        if (response.data.requires_additional_mfa) {
          // Refresh MFA status for next parameter
          await fetchMFAStatus();
          setMfaValue('');
        } else {
          // MFA complete, redirect to accounts
          toast.success('Autenticação concluída! Sincronizando dados...');
          setTimeout(() => {
            router.push('/accounts');
          }, 2000);
        }
      }
    } catch (error: any) {
      console.error('Failed to send MFA:', error);
      const errorMessage = error.response?.data?.error || 'Erro ao enviar código';
      setError(errorMessage);
      toast.error(errorMessage);
    } finally {
      setSubmitting(false);
    }
  };

  const handleCancel = () => {
    router.push('/accounts');
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  if (!mfaStatus || !mfaStatus.requires_mfa) {
    return (
      <div className="container mx-auto py-8">
        <Alert>
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>
            Esta conexão não requer autenticação adicional no momento.
          </AlertDescription>
        </Alert>
      </div>
    );
  }

  const parameter = mfaStatus.parameter || {
    name: 'token',
    type: 'text',
    label: 'Código de verificação',
    placeholder: 'Digite o código',
    assistiveText: 'Verifique seu aplicativo bancário'
  };

  return (
    <div className="container mx-auto py-8 max-w-2xl">
      <Card>
        <CardHeader className="text-center">
          <div className="flex justify-center mb-4">
            <div className="p-3 bg-primary/10 rounded-full">
              <Shield className="h-8 w-8 text-primary" />
            </div>
          </div>
          
          <CardTitle className="text-2xl">Autenticação Adicional Necessária</CardTitle>
          
          {mfaStatus.connector && (
            <div className="flex items-center justify-center gap-2 mt-4">
              {mfaStatus.connector.image_url && (
                <Image 
                  src={mfaStatus.connector.image_url} 
                  alt={mfaStatus.connector.name}
                  width={32}
                  height={32}
                  className="object-contain"
                />
              )}
              <span className="text-lg font-medium">{mfaStatus.connector.name}</span>
            </div>
          )}
          
          <CardDescription className="mt-2">
            {mfaStatus.message || 'Por favor, insira o código de verificação para continuar'}
          </CardDescription>
        </CardHeader>

        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-6">
            {/* MFA Input Field */}
            <div className="space-y-2">
              <Label htmlFor="mfa-input">
                {parameter.label}
                {parameter.optional && (
                  <span className="text-sm text-muted-foreground ml-2">(Opcional)</span>
                )}
              </Label>
              
              <Input
                id="mfa-input"
                type={parameter.type === 'numeric' ? 'number' : 'text'}
                placeholder={parameter.placeholder}
                value={mfaValue}
                onChange={(e) => setMfaValue(e.target.value)}
                disabled={submitting}
                autoFocus
                className="text-center text-lg font-mono"
              />
              
              {parameter.assistiveText && (
                <p className="text-sm text-muted-foreground">
                  {parameter.assistiveText}
                </p>
              )}
            </div>

            {/* Error Message */}
            {error && (
              <Alert variant="destructive">
                <AlertCircle className="h-4 w-4" />
                <AlertDescription>{error}</AlertDescription>
              </Alert>
            )}

            {/* Action Buttons */}
            <div className="flex gap-3">
              <Button
                type="button"
                variant="outline"
                onClick={handleCancel}
                disabled={submitting}
                className="flex-1"
              >
                Cancelar
              </Button>
              
              <Button
                type="submit"
                disabled={submitting || !mfaValue.trim()}
                className="flex-1"
              >
                {submitting ? (
                  <>
                    <LoadingSpinner size="sm" className="mr-2" />
                    Enviando...
                  </>
                ) : (
                  <>
                    <CheckCircle className="h-4 w-4 mr-2" />
                    Enviar Código
                  </>
                )}
              </Button>
            </div>
          </form>

          {/* Help Text */}
          <div className="mt-6 p-4 bg-muted rounded-lg">
            <h4 className="font-medium mb-2">Onde encontrar o código?</h4>
            <ul className="text-sm text-muted-foreground space-y-1">
              <li>• Verifique o aplicativo do seu banco</li>
              <li>• Procure por notificações push no seu celular</li>
              <li>• Verifique mensagens SMS recebidas</li>
              <li>• Alguns bancos enviam por e-mail</li>
            </ul>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}