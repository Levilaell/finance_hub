'use client';

import { useEffect, useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { belvoService } from '@/services/belvo.service';
import { useBankingStore } from '@/store/banking-store';
import { toast } from 'sonner';

interface BelvoConnectHandlerProps {
  onSuccess?: () => void;
  onError?: (error: string) => void;
}

export function BelvoConnectHandler({ onSuccess, onError }: BelvoConnectHandlerProps) {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { fetchAccounts } = useBankingStore();
  const [isProcessing, setIsProcessing] = useState(false);

  useEffect(() => {
    const linkId = searchParams.get('link');
    const institution = searchParams.get('institution');
    
    if (linkId && institution && !isProcessing) {
      handleBelvoCallback(linkId, institution);
    }
  }, [searchParams]);

  const handleBelvoCallback = async (linkId: string, institution: string) => {
    setIsProcessing(true);
    
    try {
      // Create connection with the link ID
      const result = await belvoService.createConnection({
        institution,
        username: '', // Not needed with link ID
        password: ''  // Not needed with link ID
      });

      if (result.connection_id) {
        toast.success('Conta conectada com sucesso!');
        
        // Sync initial data
        await belvoService.syncBankData();
        
        // Refresh accounts list
        await fetchAccounts();
        
        // Clear URL params
        router.replace('/accounts');
        
        onSuccess?.();
      }
    } catch (error: any) {
      console.error('Error processing Belvo callback:', error);
      const errorMessage = error.response?.data?.error || error.message || 'Erro ao processar conexão';
      toast.error(errorMessage);
      onError?.(errorMessage);
    } finally {
      setIsProcessing(false);
    }
  };

  return null;
}