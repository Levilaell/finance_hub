'use client';

import { useState } from 'react';
import { MoreVertical, RefreshCw, AlertCircle, Trash2, Key, Shield } from 'lucide-react';
import { Card, CardContent, CardHeader } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { Badge } from '@/components/ui/badge';
import { 
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog';
import type { PluggyItem } from '@/types/banking.types';
import { cn } from '@/lib/utils';

const CONNECTION_STATUS_MESSAGES: Record<string, string> = {
  'LOGIN_ERROR': 'Erro de login',
  'OUTDATED': 'Desatualizado',
  'UPDATING': 'Atualizando',
  'ERROR': 'Erro',
  'WAITING_USER_INPUT': 'Aguardando ação',
  'CREATING': 'Criando',
  'MERGING': 'Mesclando',
  'LOGIN_IN_PROGRESS': 'Fazendo login',
  'DELETED': 'Deletado'
};

interface BankConnectionCardProps {
  connection: PluggyItem;
  onSync: (id: string) => void;
  onDelete: (id: string) => void;
  onUpdateCredentials: (id: string) => void;
  onUpdateMFA: (id: string) => void;
  isLoading?: boolean;
}

export function BankConnectionCard({
  connection,
  onSync,
  onDelete,
  onUpdateCredentials,
  onUpdateMFA,
  isLoading = false,
}: BankConnectionCardProps) {
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);

  const getStatusBadge = () => {
    const statusConfig = {
      UPDATING: { variant: 'default' as const, icon: <RefreshCw className="w-3 h-3 animate-spin mr-1" /> },
      LOGIN_IN_PROGRESS: { variant: 'default' as const, icon: <RefreshCw className="w-3 h-3 animate-spin mr-1" /> },
      LOGIN_ERROR: { variant: 'destructive' as const, icon: <AlertCircle className="w-3 h-3 mr-1" /> },
      WAITING_USER_INPUT: { variant: 'secondary' as const, icon: <Shield className="w-3 h-3 mr-1" /> },
      OUTDATED: { variant: 'secondary' as const, icon: <AlertCircle className="w-3 h-3 mr-1" /> },
      ERROR: { variant: 'destructive' as const, icon: <AlertCircle className="w-3 h-3 mr-1" /> },
    };

    const config = statusConfig[connection.status as keyof typeof statusConfig];
    
    if (!config) return null;
    
    return (
      <Badge variant={config.variant} className="flex items-center">
        {config.icon}
        {CONNECTION_STATUS_MESSAGES[connection.status]}
      </Badge>
    );
  };

  const needsAction = connection.status === 'LOGIN_ERROR' || connection.status === 'WAITING_USER_INPUT';

  return (
    <>
      <Card className={cn(
        "transition-all hover:shadow-md",
        needsAction && "border-orange-200 bg-orange-50/50"
      )}>
        <CardHeader className="pb-3">
          <div className="flex items-start justify-between">
            <div className="flex items-center gap-3">
              {connection.connector.image_url ? (
                <img
                  src={connection.connector.image_url}
                  alt={connection.connector.name}
                  className="w-10 h-10 rounded-lg object-contain bg-white p-1 border"
                />
              ) : (
                <div 
                  className="w-10 h-10 rounded-lg flex items-center justify-center text-white font-bold"
                  style={{ backgroundColor: connection.connector.primary_color || '#6366f1' }}
                >
                  {connection.connector.name.charAt(0)}
                </div>
              )}
              <div>
                <h3 className="font-semibold">{connection.connector.name}</h3>
                <p className="text-sm text-muted-foreground">
                  Conexão bancária
                </p>
              </div>
            </div>
            
            <div className="flex items-center gap-2">
              {getStatusBadge()}
              
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button variant="ghost" size="icon" className="h-8 w-8">
                    <MoreVertical className="h-4 w-4" />
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end">
                  <DropdownMenuItem onClick={() => onSync(connection.id)} disabled={isLoading}>
                    <RefreshCw className="w-4 h-4 mr-2" />
                    Sincronizar
                  </DropdownMenuItem>
                  
                  {connection.status === 'LOGIN_ERROR' && (
                    <DropdownMenuItem onClick={() => onUpdateCredentials(connection.id)}>
                      <Key className="w-4 h-4 mr-2" />
                      Atualizar credenciais
                    </DropdownMenuItem>
                  )}
                  
                  {connection.status === 'WAITING_USER_INPUT' && (
                    <DropdownMenuItem onClick={() => onUpdateMFA(connection.id)}>
                      <Shield className="w-4 h-4 mr-2" />
                      Inserir código
                    </DropdownMenuItem>
                  )}
                  
                  <DropdownMenuItem 
                    onClick={() => setShowDeleteDialog(true)}
                    className="text-red-600 focus:text-red-600"
                  >
                    <Trash2 className="w-4 h-4 mr-2" />
                    Remover conexão
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            </div>
          </div>
        </CardHeader>
        
        <CardContent>
          <div className="space-y-3">
            <div className="text-sm text-muted-foreground">
              ID: {connection.pluggy_item_id}
            </div>
          </div>
          
          {connection.next_auto_sync_at && (
            <p className="text-xs text-muted-foreground mt-3">
              Próxima sincronização: {new Date(connection.next_auto_sync_at).toLocaleString('pt-BR')}
            </p>
          )}
          
        </CardContent>
      </Card>

      <AlertDialog open={showDeleteDialog} onOpenChange={setShowDeleteDialog}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Remover conexão bancária</AlertDialogTitle>
            <AlertDialogDescription>
              Are you sure you want to remove the connection with {connection.connector.name}? 
              This action cannot be undone. All synced data will be retained.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancelar</AlertDialogCancel>
            <AlertDialogAction
              onClick={() => {
                onDelete(connection.id);
                setShowDeleteDialog(false);
              }}
              className="bg-red-600 hover:bg-red-700"
            >
              Remover
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  );
}