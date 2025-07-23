'use client';

import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Textarea } from '@/components/ui/textarea';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import { toast } from 'sonner';
import { cn } from '@/lib/utils';
import {
  ShareIcon,
  LinkIcon,
  EnvelopeIcon,
  DocumentDuplicateIcon,
  LockClosedIcon,
  UsersIcon,
  CalendarIcon,
  CheckCircleIcon,
  ClockIcon,
  ChartBarIcon,
  DocumentTextIcon,
  PresentationChartLineIcon,
} from '@heroicons/react/24/outline';

interface InsightsSharingProps {
  insights: any;
  analysisId?: string;
  onShare?: (shareData: any) => void;
}

interface ShareSettings {
  type: 'link' | 'email' | 'report' | 'presentation';
  permissions: 'view' | 'comment' | 'edit';
  expiresIn: number; // dias
  includeData: {
    insights: boolean;
    predictions: boolean;
    recommendations: boolean;
    rawData: boolean;
  };
  recipients?: string[];
  message?: string;
}

export function InsightsSharing({ insights, analysisId, onShare }: InsightsSharingProps) {
  const [showDialog, setShowDialog] = useState(false);
  const [shareSettings, setShareSettings] = useState<ShareSettings>({
    type: 'link',
    permissions: 'view',
    expiresIn: 7,
    includeData: {
      insights: true,
      predictions: true,
      recommendations: true,
      rawData: false
    }
  });
  const [shareUrl, setShareUrl] = useState('');
  const [emailRecipients, setEmailRecipients] = useState('');
  const [shareMessage, setShareMessage] = useState('');
  const [isGenerating, setIsGenerating] = useState(false);

  const shareTypes = [
    {
      id: 'link',
      name: 'Link Compartilhável',
      icon: LinkIcon,
      description: 'Gere um link seguro para compartilhar'
    },
    {
      id: 'email',
      name: 'Email',
      icon: EnvelopeIcon,
      description: 'Envie por email com resumo'
    },
    {
      id: 'report',
      name: 'Relatório PDF',
      icon: DocumentTextIcon,
      description: 'Gere relatório profissional'
    },
    {
      id: 'presentation',
      name: 'Apresentação',
      icon: PresentationChartLineIcon,
      description: 'Slides executivos prontos'
    }
  ];

  const generateShareLink = async () => {
    setIsGenerating(true);
    
    // Simular geração de link (em produção seria uma API call)
    setTimeout(() => {
      const baseUrl = window.location.origin;
      const shareId = Math.random().toString(36).substring(7);
      const url = `${baseUrl}/shared/insights/${shareId}`;
      setShareUrl(url);
      setIsGenerating(false);
      
      // Copiar para clipboard
      navigator.clipboard.writeText(url);
      toast.success('Link copiado para a área de transferência!');
    }, 1500);
  };

  const sendEmail = async () => {
    setIsGenerating(true);
    
    const recipients = emailRecipients.split(',').map(e => e.trim());
    
    // Simular envio de email
    setTimeout(() => {
      toast.success(`Email enviado para ${recipients.length} destinatário(s)`);
      setIsGenerating(false);
      setShowDialog(false);
      
      if (onShare) {
        onShare({
          type: 'email',
          recipients,
          message: shareMessage,
          timestamp: new Date()
        });
      }
    }, 2000);
  };

  const generateReport = async (type: 'report' | 'presentation') => {
    setIsGenerating(true);
    
    // Simular geração de documento
    setTimeout(() => {
      const fileName = type === 'report' 
        ? `relatorio-insights-${new Date().toISOString().split('T')[0]}.pdf`
        : `apresentacao-insights-${new Date().toISOString().split('T')[0]}.pptx`;
      
      // Em produção, faria download real
      toast.success(`${type === 'report' ? 'Relatório' : 'Apresentação'} gerado(a): ${fileName}`);
      setIsGenerating(false);
      setShowDialog(false);
    }, 3000);
  };

  const handleShare = async () => {
    switch (shareSettings.type) {
      case 'link':
        await generateShareLink();
        break;
      case 'email':
        await sendEmail();
        break;
      case 'report':
        await generateReport('report');
        break;
      case 'presentation':
        await generateReport('presentation');
        break;
    }
  };

  return (
    <>
      <Button
        variant="outline"
        onClick={() => setShowDialog(true)}
        className="gap-2"
      >
        <ShareIcon className="h-4 w-4" />
        Compartilhar
      </Button>

      <Dialog open={showDialog} onOpenChange={setShowDialog}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>Compartilhar Insights</DialogTitle>
            <DialogDescription>
              Escolha como deseja compartilhar esta análise
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-6">
            {/* Tipos de compartilhamento */}
            <div>
              <Label className="text-base font-semibold mb-3 block">
                Método de Compartilhamento
              </Label>
              <div className="grid gap-3 md:grid-cols-2">
                {shareTypes.map((type) => {
                  const Icon = type.icon;
                  const isSelected = shareSettings.type === type.id;
                  
                  return (
                    <Card
                      key={type.id}
                      className={cn(
                        "cursor-pointer transition-all",
                        isSelected && "ring-2 ring-purple-600 bg-purple-50"
                      )}
                      onClick={() => setShareSettings({
                        ...shareSettings,
                        type: type.id as ShareSettings['type']
                      })}
                    >
                      <CardContent className="p-4">
                        <div className="flex items-start gap-3">
                          <div className={cn(
                            "p-2 rounded-lg",
                            isSelected ? "bg-purple-100" : "bg-gray-100"
                          )}>
                            <Icon className={cn(
                              "h-5 w-5",
                              isSelected ? "text-purple-600" : "text-gray-600"
                            )} />
                          </div>
                          <div className="flex-1">
                            <h4 className="font-medium">{type.name}</h4>
                            <p className="text-sm text-gray-600 mt-1">
                              {type.description}
                            </p>
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  );
                })}
              </div>
            </div>

            {/* Configurações específicas por tipo */}
            {shareSettings.type === 'link' && (
              <div className="space-y-4">
                <div>
                  <Label>Permissões</Label>
                  <div className="flex gap-2 mt-2">
                    {(['view', 'comment', 'edit'] as const).map((perm) => (
                      <Button
                        key={perm}
                        variant={shareSettings.permissions === perm ? 'default' : 'outline'}
                        size="sm"
                        onClick={() => setShareSettings({
                          ...shareSettings,
                          permissions: perm
                        })}
                      >
                        {perm === 'view' && <LockClosedIcon className="h-4 w-4 mr-1" />}
                        {perm === 'comment' && <UsersIcon className="h-4 w-4 mr-1" />}
                        {perm === 'edit' && <DocumentDuplicateIcon className="h-4 w-4 mr-1" />}
                        {perm === 'view' ? 'Visualizar' : perm === 'comment' ? 'Comentar' : 'Editar'}
                      </Button>
                    ))}
                  </div>
                </div>

                <div>
                  <Label>Validade do Link</Label>
                  <div className="flex gap-2 mt-2">
                    {[1, 7, 30, 365].map((days) => (
                      <Button
                        key={days}
                        variant={shareSettings.expiresIn === days ? 'default' : 'outline'}
                        size="sm"
                        onClick={() => setShareSettings({
                          ...shareSettings,
                          expiresIn: days
                        })}
                      >
                        {days === 1 ? '24h' : days === 365 ? '1 ano' : `${days} dias`}
                      </Button>
                    ))}
                  </div>
                </div>

                {shareUrl && (
                  <div className="p-4 bg-gray-50 rounded-lg">
                    <Label>Link Gerado</Label>
                    <div className="flex gap-2 mt-2">
                      <Input value={shareUrl} readOnly className="font-mono text-sm" />
                      <Button
                        size="sm"
                        onClick={() => {
                          navigator.clipboard.writeText(shareUrl);
                          toast.success('Link copiado!');
                        }}
                      >
                        <DocumentDuplicateIcon className="h-4 w-4" />
                      </Button>
                    </div>
                    <p className="text-xs text-gray-500 mt-2">
                      <CalendarIcon className="h-3 w-3 inline mr-1" />
                      Expira em {shareSettings.expiresIn} dias
                    </p>
                  </div>
                )}
              </div>
            )}

            {shareSettings.type === 'email' && (
              <div className="space-y-4">
                <div>
                  <Label>Destinatários</Label>
                  <Input
                    placeholder="email1@exemplo.com, email2@exemplo.com"
                    value={emailRecipients}
                    onChange={(e) => setEmailRecipients(e.target.value)}
                    className="mt-2"
                  />
                  <p className="text-xs text-gray-500 mt-1">
                    Separe múltiplos emails com vírgula
                  </p>
                </div>

                <div>
                  <Label>Mensagem Personalizada</Label>
                  <Textarea
                    placeholder="Adicione uma mensagem para acompanhar os insights..."
                    value={shareMessage}
                    onChange={(e) => setShareMessage(e.target.value)}
                    className="mt-2"
                    rows={4}
                  />
                </div>
              </div>
            )}

            {/* Dados a incluir */}
            <div>
              <Label className="text-base font-semibold mb-3 block">
                Dados a Incluir
              </Label>
              <div className="space-y-2">
                {Object.entries({
                  insights: 'Insights Principais',
                  predictions: 'Previsões e Projeções',
                  recommendations: 'Recomendações',
                  rawData: 'Dados Brutos (Avançado)'
                }).map(([key, label]) => (
                  <label key={key} className="flex items-center justify-between p-3 border rounded-lg hover:bg-gray-50">
                    <span className="text-sm font-medium">{label}</span>
                    <input
                      type="checkbox"
                      checked={shareSettings.includeData[key as keyof typeof shareSettings.includeData]}
                      onChange={(e) => setShareSettings({
                        ...shareSettings,
                        includeData: {
                          ...shareSettings.includeData,
                          [key]: e.target.checked
                        }
                      })}
                      className="h-4 w-4"
                    />
                  </label>
                ))}
              </div>
            </div>

            {/* Preview do compartilhamento */}
            <div className="p-4 bg-blue-50 rounded-lg">
              <h4 className="font-medium text-blue-900 mb-2">
                Resumo do Compartilhamento
              </h4>
              <ul className="space-y-1 text-sm text-blue-800">
                <li className="flex items-center gap-2">
                  <CheckCircleIcon className="h-4 w-4" />
                  Método: {shareTypes.find(t => t.id === shareSettings.type)?.name}
                </li>
                {shareSettings.type === 'link' && (
                  <>
                    <li className="flex items-center gap-2">
                      <CheckCircleIcon className="h-4 w-4" />
                      Permissões: {shareSettings.permissions === 'view' ? 'Visualização' : shareSettings.permissions === 'comment' ? 'Comentários' : 'Edição'}
                    </li>
                    <li className="flex items-center gap-2">
                      <CheckCircleIcon className="h-4 w-4" />
                      Validade: {shareSettings.expiresIn} dias
                    </li>
                  </>
                )}
                <li className="flex items-center gap-2">
                  <CheckCircleIcon className="h-4 w-4" />
                  {Object.values(shareSettings.includeData).filter(v => v).length} tipos de dados incluídos
                </li>
              </ul>
            </div>

            {/* Ações */}
            <div className="flex justify-end gap-3">
              <Button
                variant="outline"
                onClick={() => setShowDialog(false)}
              >
                Cancelar
              </Button>
              <Button
                onClick={handleShare}
                disabled={isGenerating || (shareSettings.type === 'email' && !emailRecipients)}
                className="bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700"
              >
                {isGenerating ? (
                  <>
                    <ClockIcon className="h-4 w-4 mr-2 animate-spin" />
                    Gerando...
                  </>
                ) : (
                  <>
                    <ShareIcon className="h-4 w-4 mr-2" />
                    {shareSettings.type === 'link' ? 'Gerar Link' :
                     shareSettings.type === 'email' ? 'Enviar Email' :
                     shareSettings.type === 'report' ? 'Gerar Relatório' :
                     'Criar Apresentação'}
                  </>
                )}
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </>
  );
}